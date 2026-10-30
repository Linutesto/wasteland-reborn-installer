#!/usr/bin/env python3
"""Install the selected edition on one selected Android device. Dry-run is safe offline."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE = 'https://github.com/Linutesto/wasteland-reborn-installer/releases/latest/download/'
PACKAGES = {'classic': ('io.github.imbaner.fallout2ce.debug', 'Wasteland-arm64.apk'),
            'hd': ('io.github.imbaner.fallout2ce.hd', 'Wasteland-HD-arm64.apk')}


def run(cmd, dry=False, capture=False):
    print('+ ' + ' '.join(map(str, cmd)), flush=True)
    if dry:
        return ''
    result = subprocess.run(list(map(str, cmd)), check=True, text=True, capture_output=capture)
    return result.stdout if capture else ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--edition', choices=PACKAGES, default='classic')
    ap.add_argument('--prefix', type=Path, default=Path.home() / '.local/share/wasteland-reborn')
    ap.add_argument('--apk', type=Path)
    ap.add_argument('--serial', help='adb device serial; required with multiple phones')
    ap.add_argument('--pair', metavar='IP:PORT', help='wireless debugging pairing address')
    ap.add_argument('--code', help='six-digit wireless debugging code')
    ap.add_argument('--connect', metavar='IP:PORT', help='wireless debugging connection address (different port)')
    ap.add_argument('--ai-server', help='Phone-reachable PC brain URL (LAN or Tailscale)')
    ap.add_argument('--ai-token-file', type=Path, help='Brain token file; required with --ai-server')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    package, apk_name = PACKAGES[args.edition]
    profile = args.prefix.expanduser() / args.edition
    if not all((profile / n).is_file() for n in ('master.dat', 'critter.dat', 'fallout2.cfg')):
        ap.error('install the PC edition first; profile/game files are missing')
    if args.code and not re.fullmatch(r'\d{6}', args.code): ap.error('--code must be six digits')
    if args.pair and not args.code: ap.error('--pair needs --code')
    if args.ai_server and (not args.ai_token_file or not args.ai_token_file.is_file()):
        ap.error('--ai-server needs an existing --ai-token-file')
    if args.ai_server and not re.fullmatch(r'https?://[A-Za-z0-9.:-]+', args.ai_server):
        ap.error('--ai-server must be a simple http(s) host:port URL')
    if args.pair: run(['adb', 'pair', args.pair, args.code], args.dry_run)
    if args.connect: run(['adb', 'connect', args.connect], args.dry_run)
    if not args.dry_run and not args.serial:
        devices = [line.split()[0] for line in run(['adb', 'devices'], capture=True).splitlines()[1:] if line.endswith('\tdevice')]
        if not devices: ap.error('no authorized phone found; check adb devices or use --pair/--connect')
        if len(devices) > 1:
            for i, device in enumerate(devices, 1): print(f'{i}. {device}')
            choice = input('Choose phone number (blank to cancel): ').strip()
            if not choice.isdigit() or not 1 <= int(choice) <= len(devices): ap.error('no phone selected')
            args.serial = devices[int(choice) - 1]
        else:
            args.serial = devices[0]
    adb = ['adb'] + (['-s', args.serial] if args.serial else [])
    apk = args.apk or ROOT / 'apk' / apk_name
    if not apk.is_file() and not args.dry_run:
        apk.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(RELEASE + apk_name, apk)
    elif args.dry_run and not apk.is_file():
        print('Download: ' + RELEASE + apk_name)
    run(adb + ['install', '-r', apk], args.dry_run)
    activity = package + '/com.alexbatalov.fallout2ce.MainActivity'
    run(adb + ['shell', 'am', 'start', '-n', activity], args.dry_run)
    run(adb + ['shell', 'am', 'force-stop', package], args.dry_run)
    base = '/sdcard/Android/data/' + package + '/files'
    remote = base + '/profiles/rpu-plus'
    # Explicitly create both levels; Android's compat_mkdir_recursive stops at an existing ancestor.
    for directory in (base + '/profiles', remote, remote + '/data'):
        run(adb + ['shell', 'mkdir', '-p', directory], args.dry_run)
    for name in ('master.dat', 'critter.dat'):
        run(adb + ['push', profile / name, base + '/' + name], args.dry_run)
    made = {base + '/profiles', remote, remote + '/data'}
    def push_item(local, target):
        if local.is_file():
            run(adb + ['push', local, target], args.dry_run)
            return
        for file in sorted(local.rglob('*')):
            if not file.is_file() or any(part.lower() in ('savegame', 'maps') for part in file.parts):
                continue
            dest = target + '/' + str(file.relative_to(local))
            parent = dest.rsplit('/', 1)[0]
            if parent not in made:
                run(adb + ['shell', 'mkdir', '-p', parent], args.dry_run)
                made.add(parent)
            run(adb + ['push', file, dest], args.dry_run)
    for p in profile.iterdir():
        if p.name in ('master.dat', 'critter.dat', 'fallout2-ce', 'launch.sh', 'data', 'fallout2.cfg', 'hdpack.zip'):
            continue
        if p.is_file() or p.is_dir():
            push_item(p, remote + '/' + p.name)
    for p in (profile / 'data').iterdir():
        if p.name.lower() not in ('savegame', 'maps', 'hd'):
            push_item(p, remote + '/data/' + p.name)
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        cfg = stage / 'fallout2.cfg'
        from install import cfg_set
        cfg.write_bytes((profile / 'fallout2.cfg').read_bytes())
        for section, key, value in (('system', 'master_dat', '../../master.dat'), ('system', 'critter_dat', '../../critter.dat'),
                                    ('touch', 'mobile_ui', '1'), ('touch', 'hud', '1'), ('touch', 'controls', '1')):
            cfg_set(cfg, section, key, value)
        # A localhost PC brain cannot be reached from a phone. Enable only with explicit network settings.
        cfg_set(cfg, 'ai', 'enabled', '1' if args.ai_server else '0')
        if args.ai_server:
            cfg_set(cfg, 'ai', 'server', args.ai_server)
            cfg_set(cfg, 'ai', 'token', args.ai_token_file.read_text().strip())
        else:
            cfg_set(cfg, 'ai', 'server', '')
            cfg_set(cfg, 'ai', 'token', '')
        run(adb + ['push', cfg, remote + '/fallout2.cfg'], args.dry_run)
        active = stage / 'active-profile.txt'; active.write_text('rpu-plus\n')
        run(adb + ['push', active, base + '/active-profile.txt'], args.dry_run)
        if args.edition == 'hd':
            art = profile / 'data/hd'
            if art.is_dir():
                archive = stage / 'hdpack.zip'
                with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as z:
                    for p in art.rglob('*'):
                        if p.is_file(): z.write(p, 'hd/' + str(p.relative_to(art)))
                run(adb + ['push', archive, remote + '/data/hdpack.zip'], args.dry_run)
                run(adb + ['shell', 'sh', '-c', f'cd {remote}/data && unzip -oq hdpack.zip && rm hdpack.zip'], args.dry_run)
            else:
                print('HD art absent locally; install published packs on PC first.')
    run(adb + ['shell', 'am', 'start', '-n', activity], args.dry_run)

if __name__ == '__main__': main()
