"""Wasteland Reborn — configuration after install (run by the installer).

1. finds the player's own Fallout 2 (Epic, Steam, GOG or a chosen folder) and
   copies master.dat, critter.dat and the music next to the RPU profile;
2. turns the AI on if Ollama is installed (optional);
3. offers to install the game on an Android phone over ADB (phone.py).
"""
import json
import os
import shutil
import string
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (GAME, OLLAMA, ask, cfg_set, fatal, http_json, load_settings, ollama_exe,
                    ollama_models, pause, save_settings, start_ollama, title, token, yes, BRAIN_PORT)

MODELS = [
    ('qwen3:4b', 'Qwen 3 4B  - leger, ~2,6 Go, va sur presque tout (recommande)'),
    ('qwen3:8b', 'Qwen 3 8B  - plus intelligent, ~5,2 Go, carte graphique 8 Go+'),
    ('gemma3:4b', 'Gemma 3 4B - alternative, ~3,3 Go'),
]


def is_game_dir(path):
    return path is not None and (path / 'master.dat').is_file() and (path / 'critter.dat').is_file()


def look_inside(path):
    """The folder itself or a sub-folder (2 levels) holding master.dat + critter.dat."""
    if not path or not path.is_dir():
        return None
    if is_game_dir(path):
        return path
    try:
        for child in path.iterdir():
            if child.is_dir():
                if is_game_dir(child):
                    return child
                for grandchild in child.iterdir():
                    if grandchild.is_dir() and is_game_dir(grandchild):
                        return grandchild
    except OSError:
        pass
    return None


def epic_dirs():
    manifests = Path(os.environ.get('ProgramData', 'C:/ProgramData')) / 'Epic/EpicGamesLauncher/Data/Manifests'
    for item in sorted(manifests.glob('*.item')) if manifests.is_dir() else []:
        try:
            data = json.loads(item.read_text(encoding='utf-8', errors='replace'))
        except ValueError:
            continue
        name = (data.get('DisplayName') or '') + ' ' + (data.get('AppName') or '')
        if 'fallout' in name.lower() and ('2' in name or 'ii' in name.lower()):
            yield Path(data.get('InstallLocation', ''))


def registry_value(root, key, name):
    try:
        import winreg
        with winreg.OpenKey(root, key) as k:
            return winreg.QueryValueEx(k, name)[0]
    except OSError:
        return None


def steam_dirs():
    import re
    import winreg
    steam = registry_value(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath')
    if not steam:
        return
    libraries = [Path(steam)]
    vdf = Path(steam) / 'steamapps/libraryfolders.vdf'
    if vdf.is_file():
        for m in re.finditer(r'"path"\s+"([^"]+)"', vdf.read_text(encoding='utf-8', errors='replace')):
            libraries.append(Path(m.group(1).replace('\\\\', '\\')))
    for lib in libraries:
        yield lib / 'steamapps/common/Fallout 2'


def gog_dirs():
    import winreg
    for key in [r'SOFTWARE\WOW6432Node\GOG.com\Games\1440151285', r'SOFTWARE\GOG.com\Games\1440151285']:
        path = registry_value(winreg.HKEY_LOCAL_MACHINE, key, 'path')
        if path:
            yield Path(path)


def common_dirs():
    for drive in string.ascii_uppercase[2:]:
        base = Path(f'{drive}:/')
        if not base.exists():
            continue
        for rel in ['Program Files/Epic Games/Fallout2', 'Program Files/Epic Games/Fallout 2',
                    'Epic Games/Fallout2', 'Epic Games/Fallout 2', 'GOG Games/Fallout 2',
                    'Program Files (x86)/GOG Galaxy/Games/Fallout 2', 'Games/Fallout 2', 'Fallout2',
                    'Program Files (x86)/Steam/steamapps/common/Fallout 2', 'SteamLibrary/steamapps/common/Fallout 2']:
            yield base / rel


def find_game():
    for source in (epic_dirs, steam_dirs, gog_dirs, common_dirs):
        try:
            for candidate in source():
                found = look_inside(candidate)
                if found:
                    return found
        except Exception:  # noqa: BLE001 - a broken launcher install shouldn't stop the search
            continue
    return None


def pick_folder():
    script = ("Add-Type -AssemblyName System.Windows.Forms;"
              "$f = New-Object System.Windows.Forms.FolderBrowserDialog;"
              "$f.Description = 'Choisis le dossier de Fallout 2 (celui avec master.dat)';"
              "if ($f.ShowDialog() -eq 'OK') { $f.SelectedPath }")
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-STA', '-Command', script],
                             capture_output=True, text=True, timeout=600).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        out = ''
    return Path(out) if out else None


def install_game_files(source):
    print(f'\nCopie des fichiers de ton Fallout 2 depuis :\n  {source}')
    for name in ['master.dat', 'critter.dat']:
        src = source / name
        dest = GAME / name
        if dest.is_file() and dest.stat().st_size == src.stat().st_size:
            print(f'  {name} : deja la')
            continue
        print(f'  {name} ({src.stat().st_size // 2**20} Mo)...')
        shutil.copyfile(src, dest)
    music_src = next((p for p in [source / 'data/sound/music', source / 'sound/music'] if p.is_dir()), None)
    music_dest = GAME / 'data/sound/music'
    music_dest.mkdir(parents=True, exist_ok=True)
    copied = 0
    if music_src:
        for f in music_src.iterdir():
            if f.is_file() and not (music_dest / f.name).exists():
                shutil.copyfile(f, music_dest / f.name)
                copied += 1
    print(f'  musique : {copied} fichiers copies' if music_src else '  musique : introuvable (le jeu marche sans)')


def setup_game():
    title('1/3  Ton jeu Fallout 2')
    if (GAME / 'master.dat').is_file() and (GAME / 'critter.dat').is_file() \
            and not yes('Les fichiers du jeu sont deja installes. Les recopier?', default=False):
        return
    source = find_game()
    if source:
        print(f'Trouve : {source}')
        if not yes('Utiliser ce dossier?'):
            source = None
    while source is None:
        print("\nJe n'ai pas trouve Fallout 2 automatiquement.")
        print("Dans le lanceur Epic : clic sur les ... de Fallout 2 > Gerer > icone de dossier.")
        input('Appuie sur Entree pour choisir le dossier...')
        source = look_inside(pick_folder())
        if source is None and not yes('Pas de master.dat + critter.dat la-dedans. Reessayer?'):
            fatal("Il faut ta copie de Fallout 2 pour jouer. Relance 'Wasteland - Configurer' plus tard.")
    install_game_files(source)


def pull_model(name):
    import urllib.request
    print(f'\nTelechargement de {name} (ca peut prendre plusieurs minutes)...')
    req = urllib.request.Request(OLLAMA + '/api/pull', data=json.dumps({'name': name}).encode(),
                                 headers={'Content-Type': 'application/json'})
    last = ''
    with urllib.request.urlopen(req, timeout=3600) as r:
        for line in r:
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg.get('error'):
                print('\n  Erreur :', msg['error'])
                return False
            status = msg.get('status', '')
            if msg.get('total'):
                status += f" {100 * msg.get('completed', 0) // msg['total']}%"
            if status != last:
                print('\r  ' + status.ljust(50), end='', flush=True)
                last = status
    print('\n  OK')
    return True


def setup_ai(settings):
    title('2/3  PNJ avec IA (optionnel)')
    print('Avec Ollama, les personnages repondent a ce que tu leur ecris (option [Speak freely]')
    print("dans les dialogues). Sans Ollama, le jeu est normal.")
    if ollama_exe() is None and ollama_models() is None:
        print('\nOllama n\'est pas installe : IA desactivee.')
        print('Pour l\'activer plus tard : installe Ollama (https://ollama.com), puis')
        print('lance "Wasteland - Configurer" dans le menu Demarrer.')
        settings['ai'] = False
        return
    if not start_ollama():
        print('\nOllama est installe mais ne repond pas. Ouvre Ollama puis relance la configuration.')
        settings['ai'] = False
        return
    if not yes('\nOllama detecte. Activer les PNJ avec IA?'):
        settings['ai'] = False
        return
    installed = ollama_models() or []
    choices = [(m, d + ('  [deja installe]' if m in installed else '')) for m, d in MODELS]
    choices += [(m, m + '  [deja installe]') for m in installed
                if m not in dict(MODELS) and not any(x in m for x in ('embed', 'minilm', ':cloud'))]
    print('\nQuel modele?')
    for i, (_, label) in enumerate(choices, 1):
        print(f'  {i}. {label}')
    current = settings.get('model')
    default = next((str(i) for i, (m, _) in enumerate(choices, 1) if m == current), '1')
    while True:
        pick = ask('Numero', default)
        if pick.isdigit() and 1 <= int(pick) <= len(choices):
            model = choices[int(pick) - 1][0]
            break
    if model not in installed and not pull_model(model):
        print('Telechargement rate : IA desactivee pour l\'instant.')
        settings['ai'] = False
        return
    settings.update(ai=True, model=model)
    print(f'\nIA activee avec {model}.')


def apply_pc_config(settings):
    cfg = GAME / 'fallout2.cfg'
    cfg_set(cfg, 'ai', 'enabled', '1' if settings.get('ai') else '0')
    cfg_set(cfg, 'ai', 'server', f'http://127.0.0.1:{BRAIN_PORT}')
    cfg_set(cfg, 'ai', 'token', token())
    cfg_set(cfg, 'ai', 'timeout_ms', '45000')
    cfg_set(cfg, 'ai', 'content_id', 'fallout2')


def main():
    os.system('title Wasteland Reborn - Configuration')
    print('WASTELAND REBORN - Fallout 2 Restoration Project + PNJ avec IA')
    settings = load_settings()
    setup_game()
    setup_ai(settings)
    save_settings(settings)
    apply_pc_config(settings)

    import phone
    phone.run(interactive_end=False)

    title('Fini!')
    print('Lance le jeu avec l\'icone "Wasteland Reborn" sur le bureau.')
    if settings.get('ai'):
        print('En dialogue, choisis l\'option de parler librement et ecris ce que tu veux.')
    pause()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:  # noqa: BLE001
        fatal(f'{type(e).__name__}: {e}')
