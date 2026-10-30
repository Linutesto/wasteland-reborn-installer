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
from common import (GAME, LANG, OLLAMA, USERDATA, ask, cfg_set, fatal, http_json, load_settings, ollama_exe,
                    ollama_models, pause, save_settings, start_ollama, t, title, token, yes, BRAIN_PORT)

MODELS = [
    ('qwen3:4b', t('Qwen 3 4B  - leger, ~2,6 Go, va sur presque tout (recommande)',
                   'Qwen 3 4B  - light, ~2.6 GB, runs on almost anything (recommended)')),
    ('qwen3:8b', t('Qwen 3 8B  - plus intelligent, ~5,2 Go, carte graphique 8 Go+',
                   'Qwen 3 8B  - smarter, ~5.2 GB, 8 GB+ graphics card')),
    ('gemma3:4b', t('Gemma 3 4B - alternative, ~3,3 Go', 'Gemma 3 4B - alternative, ~3.3 GB')),
]
EDITION_FILE = Path(__file__).resolve().parent / 'edition.json'


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
              "$f.Description = '" + t('Choisis le dossier de Fallout 2 (celui avec master.dat)', 'Choose the Fallout 2 folder (the one with master.dat)') + "';"
              "if ($f.ShowDialog() -eq 'OK') { $f.SelectedPath }")
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-STA', '-Command', script],
                             capture_output=True, text=True, timeout=600).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        out = ''
    return Path(out) if out else None


def install_game_files(source):
    print(t('\nCopie des fichiers de ton Fallout 2 depuis :', '\nCopying the files of your Fallout 2 from:') + f'\n  {source}')
    for name in ['master.dat', 'critter.dat']:
        src = source / name
        dest = GAME / name
        if dest.is_file() and dest.stat().st_size == src.stat().st_size:
            print(f'  {name} : ' + t('deja la', 'already there'))
            continue
        print(f'  {name} ({src.stat().st_size // 2**20} ' + t('Mo', 'MB') + ')...')
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
    print(t(f'  musique : {copied} fichiers copies', f'  music: {copied} files copied') if music_src
          else t('  musique : introuvable (le jeu marche sans)', '  music: not found (the game works without it)'))


def setup_game():
    title(t('1/3  Ton jeu Fallout 2', '1/3  Your Fallout 2 game'))
    if (GAME / 'master.dat').is_file() and (GAME / 'critter.dat').is_file() \
            and not yes(t('Les fichiers du jeu sont deja installes. Les recopier?', 'The game files are already installed. Copy them again?'), default=False):
        return
    source = find_game()
    if source:
        print(t('Trouve : ', 'Found: ') + str(source))
        if not yes(t('Utiliser ce dossier?', 'Use this folder?')):
            source = None
    while source is None:
        print(t("\nJe n'ai pas trouve Fallout 2 automatiquement.", "\nI couldn't find Fallout 2 automatically."))
        print(t("Dans le lanceur Epic : clic sur les ... de Fallout 2 > Gerer > icone de dossier.",
                "In the Epic launcher: click the ... of Fallout 2 > Manage > folder icon."))
        input(t('Appuie sur Entree pour choisir le dossier...', 'Press Enter to choose the folder...'))
        source = look_inside(pick_folder())
        if source is None and not yes(t('Pas de master.dat + critter.dat la-dedans. Reessayer?', 'No master.dat + critter.dat in there. Try again?')):
            fatal(t("Il faut ta copie de Fallout 2 pour jouer. Relance 'Wasteland - Configurer' plus tard.",
                    "You need your copy of Fallout 2 to play. Run 'Wasteland - Setup' again later."))
    install_game_files(source)


def setup_hd_art(unattended=False):
    """Install published packs after game verification, even on repeat setup."""
    if not EDITION_FILE.is_file() or json.loads(EDITION_FILE.read_text(encoding='utf-8')).get('edition') != 'hd':
        return
    title(t('Art HD (optionnel)', 'HD art (optional)'))
    if not is_game_dir(GAME):
        print(t('Art HD refuse : Fallout 2 (master.dat et critter.dat) absent.',
                'HD art refused: Fallout 2 (master.dat and critter.dat) is missing.'))
        return
    if not unattended and not yes(t('Telecharger les packs graphiques HD disponibles?',
                                   'Download the available HD graphics packs?')):
        return
    print(t('Recherche des packs HD publies...', 'Checking for published HD packs...'))
    try:
        from types import SimpleNamespace
        from wasteland_hd.__main__ import ASSETS, cmd_install
        cmd_install(SimpleNamespace(game=str(GAME), packs=ASSETS, only=None))
    except (Exception, SystemExit) as e:  # noqa: BLE001 - optional art must not break setup
        # The first release remains a GitHub draft until Yan checks its art.
        print(t('Packs HD indisponibles pour le moment : ', 'HD packs unavailable for now: ') + str(e))
        print(t('Relance la configuration pour les installer apres publication.',
                'Run setup again to install them once published.'))


def unattended_main():
    """NSIS /S: configure a found game without input, phone, or AI downloads.

    An offline HD pack must never abort a successful install. Keep a readable
    setup log because a silent NSIS run has no console to display its errors.
    """
    from contextlib import redirect_stderr, redirect_stdout

    USERDATA.mkdir(parents=True, exist_ok=True)
    with (USERDATA / 'setup-install.log').open('w', encoding='utf-8') as log:
        with redirect_stdout(log), redirect_stderr(log):
            print('Wasteland Reborn unattended configuration', flush=True)
            try:
                settings = load_settings()
                settings.update(lang=LANG, ai=False, phone_ai=False)
                save_settings(settings)
                source = find_game()
                if source is None:
                    print(t('Fallout 2 introuvable. Installer le jeu puis relancer Wasteland - Configurer.',
                            'Fallout 2 not found. Install the game and run Wasteland - Setup later.'))
                    return 0
                print(t('Fallout 2 trouve : ', 'Fallout 2 found: ') + str(source))
                install_game_files(source)
                setup_hd_art(unattended=True)
                apply_pc_config(settings)
                print(t('Installation du jeu terminee. Telephone et IA configurables plus tard.',
                        'Game setup complete. Configure phone and AI later.'))
                return 0
            except Exception as e:  # noqa: BLE001 - preserve installer even if setup fails
                print(f'Unattended setup failed: {type(e).__name__}: {e}')
                print('Run Wasteland - Setup from the Start menu to retry.')
                return 1


def pull_model(name):
    import urllib.request
    print(t(f'\nTelechargement de {name} (ca peut prendre plusieurs minutes)...', f'\nDownloading {name} (this can take several minutes)...'))
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
                print(t('\n  Erreur :', '\n  Error:'), msg['error'])
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
    title(t('2/3  PNJ avec IA (optionnel)', '2/3  AI NPCs (optional)'))
    print(t('Avec Ollama, les personnages repondent a ce que tu leur ecris (option [Speak freely]\n'
            'dans les dialogues). Sans Ollama, le jeu est normal.',
            'With Ollama, characters answer whatever you type to them (the [Speak freely] option\n'
            'in dialogues). Without Ollama, the game is the normal one.'))
    if ollama_exe() is None and ollama_models() is None:
        print(t('\nOllama n\'est pas installe : IA desactivee.\n'
                'Pour l\'activer plus tard : installe Ollama (https://ollama.com), puis\n'
                'lance "Wasteland - Configurer" dans le menu Demarrer.',
                '\nOllama is not installed: AI is off.\n'
                'To turn it on later: install Ollama (https://ollama.com), then\n'
                'run "Wasteland - Setup" from the Start menu.'))
        settings['ai'] = False
        return
    if not start_ollama():
        print(t('\nOllama est installe mais ne repond pas. Ouvre Ollama puis relance la configuration.',
                '\nOllama is installed but not answering. Open Ollama, then run the setup again.'))
        settings['ai'] = False
        return
    if not yes(t('\nOllama detecte. Activer les PNJ avec IA?', '\nOllama found. Turn on AI NPCs?')):
        settings['ai'] = False
        return
    installed = ollama_models() or []
    already = t('  [deja installe]', '  [already installed]')
    choices = [(m, d + (already if m in installed else '')) for m, d in MODELS]
    choices += [(m, m + already) for m in installed
                if m not in dict(MODELS) and not any(x in m for x in ('embed', 'minilm', ':cloud'))]
    print(t('\nQuel modele?', '\nWhich model?'))
    for i, (_, label) in enumerate(choices, 1):
        print(f'  {i}. {label}')
    current = settings.get('model')
    default = next((str(i) for i, (m, _) in enumerate(choices, 1) if m == current), '1')
    while True:
        pick = ask(t('Numero', 'Number'), default)
        if pick.isdigit() and 1 <= int(pick) <= len(choices):
            model = choices[int(pick) - 1][0]
            break
    if model not in installed and not pull_model(model):
        print(t('Telechargement rate : IA desactivee pour l\'instant.', 'Download failed: AI is off for now.'))
        settings['ai'] = False
        return
    settings.update(ai=True, model=model)
    print(t(f'\nIA activee avec {model}.', f'\nAI on with {model}.'))


def apply_pc_config(settings):
    cfg = GAME / 'fallout2.cfg'
    cfg_set(cfg, 'ai', 'enabled', '1' if settings.get('ai') else '0')
    cfg_set(cfg, 'ai', 'server', f'http://127.0.0.1:{BRAIN_PORT}')
    cfg_set(cfg, 'ai', 'token', token())
    cfg_set(cfg, 'ai', 'timeout_ms', '45000')
    cfg_set(cfg, 'ai', 'content_id', 'fallout2')


def main():
    hd = EDITION_FILE.is_file()
    product = 'Wasteland Reborn HD' if hd else 'Wasteland Reborn'
    os.system('title ' + product + ' - Configuration')
    print(product.upper() + t(' - Fallout 2 Restoration Project + PNJ avec IA',
                              ' - Fallout 2 Restoration Project + AI NPCs'))
    settings = load_settings()
    settings['lang'] = LANG
    save_settings(settings)
    setup_game()
    setup_hd_art()
    setup_ai(settings)
    save_settings(settings)
    apply_pc_config(settings)

    import phone
    phone.run(interactive_end=False)

    title(t('Fini!', 'Done!'))
    print(t(f'Lance le jeu avec l\'icone "{product}" sur le bureau.',
            f'Start the game with the "{product}" desktop icon.'))
    if settings.get('ai'):
        print(t('En dialogue, choisis [Speak freely] et ecris ce que tu veux.', 'In dialogues, pick [Speak freely] and type whatever you want.'))
    pause()


if __name__ == '__main__':
    if '--unattended' in sys.argv:
        sys.exit(unattended_main())
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:  # noqa: BLE001
        fatal(f'{type(e).__name__}: {e}')
