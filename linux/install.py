#!/usr/bin/env python3
"""Linux installer. Every generated file is recorded in a per-prefix manifest."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = Path.home() / '.local/share/wasteland-reborn'
NAMES = ('Fallout 2', 'Fallout2', 'fallout 2', 'fallout2')


def game_dir(path):
    if not path or not Path(path).is_dir():
        return None
    path = Path(path)
    files = {p.name.lower(): p for p in path.iterdir() if p.is_file()}
    return path if 'master.dat' in files and 'critter.dat' in files else None


def game_file(path, name):
    return next(p for p in Path(path).iterdir() if p.name.lower() == name.lower())


def case_path(root, relative):
    current = Path(root)
    for part in relative.split('/'):
        if not current.is_dir(): return None
        current = next((p for p in current.iterdir() if p.name.lower() == part.lower()), None)
        if current is None: return None
    return current


def library_paths(vdf):
    if not vdf.is_file():
        return []
    return [Path(s.replace('\\\\', '/')) for s in re.findall(r'"path"\s+"([^\"]+)"', vdf.read_text(errors='replace'))]


def candidates(home):
    home = Path(home)
    steam = [home / '.steam/steam', home / '.local/share/Steam',
             home / '.var/app/com.valvesoftware.Steam/.local/share/Steam',
             home / '.var/app/com.valvesoftware.Steam/.steam/steam']
    for base in steam:
        for lib in [base, *library_paths(base / 'steamapps/libraryfolders.vdf')]:
            for name in NAMES:
                yield lib / 'steamapps/common' / name
    heroic_meta = home / '.config/heroic/GamesConfig'
    if heroic_meta.is_dir():
        for meta in heroic_meta.glob('*.json'):
            try:
                obj = json.loads(meta.read_text())
                for value in (obj.get('install', {}).get('install_path'), obj.get('install_path')):
                    if value:
                        yield Path(value)
            except (OSError, ValueError, AttributeError):
                pass
    for base in (home / 'Games/Heroic', home / '.config/heroic/GamesConfig',
                 home / 'Games', home / '.local/share/lutris/games',
                 home / '.wine/drive_c/GOG Games', home / '.wine/drive_c/Program Files (x86)/GOG Galaxy/Games'):
        for name in NAMES:
            yield base / name
        if base.is_dir():
            for child in base.iterdir():
                if child.is_dir():
                    yield child
                    for name in NAMES:
                        yield child / 'drive_c/GOG Games' / name
                        yield child / 'drive_c/Program Files (x86)/GOG Galaxy/Games' / name
                        yield child / name


def find_game(home):
    return next((found for p in candidates(home) if (found := game_dir(p))), None)


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def cfg_set(path, section, key, value):
    lines = path.read_text(encoding='latin-1').splitlines()
    header = '[' + section + ']'
    start = next((i for i, line in enumerate(lines) if line.strip().lower() == header.lower()), None)
    if start is None:
        lines += ['', header, f'{key}={value}']
    else:
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('[')), len(lines))
        index = next((i for i in range(start + 1, end) if lines[i].split('=', 1)[0].strip().lower() == key.lower() and '=' in lines[i]), None)
        if index is None:
            lines.insert(end, f'{key}={value}')
        else:
            lines[index] = f'{key}={value}'
    path.write_text('\n'.join(lines) + '\n', encoding='latin-1')


def tracked_copy(src, dst, records):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and digest(src) == digest(dst):
        records[str(dst)] = digest(dst)
        return
    shutil.copy2(src, dst)
    records[str(dst)] = digest(dst)


def tree(src, dst, records, skip_saves=True):
    if not src.is_dir():
        return
    for p in src.rglob('*'):
        if src == ROOT / 'brain' and (p.suffix not in ('.py', '.json') or 'tests' in p.parts or '__pycache__' in p.parts):
            continue
        if p.is_file() and not (skip_saves and any(x.lower() == 'savegame' for x in p.parts)):
            tracked_copy(p, dst / p.relative_to(src), records)


def write(path, content, records, mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    if mode:
        path.chmod(mode)
    records[str(path)] = digest(path)


def uninstall(prefix):
    manifest = prefix / '.install-manifest.json'
    if not manifest.exists():
        raise SystemExit(f'No installation manifest: {manifest}')
    files = json.loads(manifest.read_text())['files']
    for name, checksum in sorted(files.items(), key=lambda pair: len(pair[0]), reverse=True):
        p = Path(name)
        if p.is_file() and digest(p) == checksum:
            p.unlink()
        elif p.exists():
            print(f'Preserved modified file: {p}')
    manifest.unlink()
    for base in (prefix, Path.home() / '.local/bin', Path.home() / '.local/share/applications'):
        if base.is_dir():
            for directory in sorted((p for p in base.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
                try: directory.rmdir()
                except OSError: pass
            try: base.rmdir()
            except OSError: pass
    print('Uninstalled recorded files; modified files and saves were preserved.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--edition', choices=('classic', 'hd'), default='classic')
    ap.add_argument('--prefix', type=Path, default=DEFAULT)
    ap.add_argument('--game', type=Path)
    ap.add_argument('--ai', action='store_true', help='Enable local Ollama NPCs')
    ap.add_argument('--model', default='qwen3:4b')
    ap.add_argument('--no-hd-download', action='store_true')
    ap.add_argument('--uninstall', action='store_true', help=argparse.SUPPRESS)
    args = ap.parse_args()
    prefix = args.prefix.expanduser().resolve()
    if args.uninstall:
        uninstall(prefix); return
    game = game_dir(args.game) if args.game else find_game(Path.home())
    if not game:
        ap.error('Fallout 2 not found: supply --game DIR containing master.dat and critter.dat')
    profile = ROOT / 'build/profile'
    engine = ROOT / 'src/imbaner_fallout2-ce-mobile'
    if not (profile / 'fallout2.cfg').is_file():
        ap.error('build/profile missing; run ./bootstrap.sh --no-android first')
    binary = next((p for p in (ROOT / 'build/linux/fallout2-ce', engine / 'build/fallout2-ce') if p.is_file()), None)
    if binary is None:
        subprocess.run(['cmake', '-S', str(engine), '-B', str(ROOT / 'build/linux'), '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release'], check=True)
        subprocess.run(['cmake', '--build', str(ROOT / 'build/linux'), '--parallel', str(min(os.cpu_count() or 2, 8))], check=True)
        binary = ROOT / 'build/linux/fallout2-ce'
    old = prefix / '.install-manifest.json'
    records = json.loads(old.read_text())['files'] if old.exists() else {}
    dest = prefix / args.edition
    tree(profile, dest, records)
    for name in ('master.dat', 'critter.dat'):
        tracked_copy(game_file(game, name), dest / name, records)
    for rel in ('data/sound/music', 'sound/music'):
        music = case_path(game, rel)
        if music and music.is_dir():
            tree(music, dest / 'data/sound/music', records); break
    tracked_copy(binary, dest / 'fallout2-ce', records)
    ce_tool = binary.parent / 'ce-dat-tool'
    ce_data = dest / 'ce.dat'
    if not ce_tool.is_file():
        ap.error('ce-dat-tool missing next to the Linux engine; rebuild with CMake')
    subprocess.run([str(ce_tool), 'create', str(engine / 'files/ce.dat'), str(ce_data)], check=True, stdout=subprocess.DEVNULL)
    records[str(ce_data)] = digest(ce_data)
    config = dest / 'fallout2.cfg'
    cfg_set(config, 'graphics', 'hd_art', '1' if args.edition == 'hd' else '0')
    if args.edition == 'hd':
        cfg_set(config, 'graphics', 'hd_cache_mb', '256')
    if args.ai:
        if not shutil.which('ollama'):
            print('Ollama absent; install it to enable AI.', file=sys.stderr)
        else:
            answer = input(f'Pull {args.model} for optional NPC AI? [y/N] ')
            if answer.lower() == 'y': subprocess.run(['ollama', 'pull', args.model], check=True)
            cfg_set(config, 'ai', 'enabled', '1')
            cfg_set(config, 'ai', 'server', 'http://127.0.0.1:8822')
    if args.ai and shutil.which('ollama'):
        import secrets
        token_path = prefix / 'brain/token'
        token_path.parent.mkdir(parents=True, exist_ok=True)
        if not token_path.exists(): token_path.write_text(secrets.token_urlsafe(32) + '\n')
        token_path.chmod(0o600)
        cfg_set(config, 'ai', 'token', token_path.read_text().strip())
        records[str(token_path)] = digest(token_path)
    records[str(config)] = digest(config)
    if args.edition == 'hd' and not args.no_hd_download:
        tools = ROOT / 'src/wasteland-hd-tools'
        if tools.is_dir():
            env = dict(os.environ, PYTHONPATH=str(tools))
            result = subprocess.run([sys.executable, '-m', 'wasteland_hd', 'install', '--game', str(dest)], env=env)
            if result.returncode: print('HD packs unavailable; retry install later.', file=sys.stderr)
            else:
                for p in (dest / 'data/hd').rglob('*'):
                    if p.is_file(): records[str(p)] = digest(p)
    runner = f'''#!/usr/bin/env bash
set -euo pipefail
cd {str(dest)!r}
brain_pid=
if grep -q '^enabled=1$' fallout2.cfg && command -v ollama >/dev/null; then
  python3 {str(prefix / 'brain/server.py')!r} --host 127.0.0.1 --port 8822 --llm http://127.0.0.1:11434 --llm-api ollama --model {args.model!r} --db {str(prefix / 'brain/brain.db')!r} --log-dir {str(prefix / 'brain/logs')!r} --token-file {str(prefix / 'brain/token')!r} &
  brain_pid=$!
fi
trap 'if [[ -n "$brain_pid" ]]; then kill "$brain_pid" 2>/dev/null || :; fi' EXIT
./fallout2-ce
'''
    tree(ROOT / 'brain', prefix / 'brain', records)
    write(dest / 'launch.sh', runner, records, 0o755)
    binpath = Path.home() / '.local/bin/wasteland'
    serverpath = Path.home() / '.local/bin/wasteland-brain'
    for external in (binpath, serverpath, Path.home() / '.local/share/applications/wasteland-reborn.desktop'):
        if external.exists() and str(external) not in records:
            ap.error(f'refusing to replace unowned file: {external}')
    write(binpath, f'#!/usr/bin/env bash\nexec {str(dest / "launch.sh")!r} "$@"\n', records, 0o755)
    server_cmd = f'''#!/usr/bin/env bash
set -euo pipefail
exec python3 {str(prefix / 'brain/server.py')!r} --host 0.0.0.0 --port 8822 --llm http://127.0.0.1:11434 --llm-api ollama --model {args.model!r} --db {str(prefix / 'brain/brain.db')!r} --log-dir {str(prefix / 'brain/logs')!r} --token-file {str(prefix / 'brain/token')!r}
'''
    write(serverpath, server_cmd, records, 0o755)
    icon_src = engine / 'os/android/app/src' / ('wasteland-hd' if args.edition == 'hd' else 'wasteland') / 'res/mipmap-xxxhdpi/ic_launcher.png'
    icon = prefix / 'icon.png'
    if icon_src.exists(): tracked_copy(icon_src, icon, records)
    desktop = Path.home() / '.local/share/applications/wasteland-reborn.desktop'
    write(desktop, f'[Desktop Entry]\nType=Application\nName=Wasteland Reborn\nExec={binpath}\nIcon={icon}\nTerminal=false\nCategories=Game;\n', records)
    write(prefix / '.install-manifest.json', json.dumps({'files': records}, indent=2, sort_keys=True) + '\n', {})
    print(f'Installed {args.edition} in {dest}; run wasteland')

if __name__ == '__main__': main()
