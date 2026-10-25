"""Wasteland Reborn — install the game on an Android phone over (wireless) ADB.

Installs the Wasteland app, copies the player's game files and the RPU
profile to it, and points its AI at this PC when the AI is on.
Nothing is installed without the player picking the phone in a menu.
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (BRAIN_PORT, GAME, NO_WINDOW, ROOT, ask, cfg_set, fatal, lan_ip, load_settings,
                    pause, save_settings, title, token, yes)

PACKAGE = 'io.github.imbaner.fallout2ce.debug'
ACTIVITY = PACKAGE + '/com.alexbatalov.fallout2ce.MainActivity'
PHONE = '/sdcard/Android/data/' + PACKAGE + '/files'
PROFILE = 'rpu-plus'
APK = ROOT / 'phone/wasteland.apk'
TOOLS_URL = 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip'
ADB = None


def find_adb(offer_download=True):
    local = ROOT / 'platform-tools/adb.exe'
    candidates = [shutil.which('adb'), local,
                  Path(os.environ.get('LOCALAPPDATA', '')) / 'Android/Sdk/platform-tools/adb.exe']
    for c in candidates:
        if c and Path(c).is_file():
            return str(c)
    if not offer_download:
        return None
    print("Installation d'adb (outils Android officiels de Google, ~7 Mo)...")
    try:
        with urllib.request.urlopen(TOOLS_URL, timeout=120) as r:
            zipfile.ZipFile(io.BytesIO(r.read())).extractall(ROOT)
    except OSError as e:
        print(f'  echec : {e}')
        return None
    print('  OK')
    return str(local) if local.is_file() else None


def adb(*args, check=True, capture=True, timeout=None):
    r = subprocess.run([ADB, *map(str, args)], capture_output=capture, text=True,
                       timeout=timeout, creationflags=NO_WINDOW)
    if check and r.returncode != 0:
        raise RuntimeError(f"adb {' '.join(map(str, args[:2]))} : {(r.stderr or r.stdout or '').strip()}")
    return (r.stdout or '').strip()


def devices():
    out = adb('devices', check=False)
    return [line.split()[0] for line in out.splitlines()[1:] if line.strip().endswith('device')]


def mdns_connect():
    out = adb('mdns', 'services', check=False, timeout=15)
    for m in re.finditer(r'_adb-tls-connect\._tcp\.?\s+([\d.]+:\d+)', out):
        adb('connect', m.group(1), check=False, timeout=15)
    return devices()


def pairing_address():
    out = adb('mdns', 'services', check=False, timeout=15)
    m = re.search(r'_adb-tls-pairing\._tcp\.?\s+([\d.]+:\d+)', out)
    return m.group(1) if m else None


def pair_new():
    """Walks through wireless-debugging pairing; returns the new device's serial or None."""
    before = set(devices())
    print("""
Sur le telephone :
  1. Parametres > A propos du telephone > tape 7 fois sur "Numero de build"
     (active les Options pour les developpeurs).
  2. Parametres > Systeme > Options pour les developpeurs > "Debogage sans fil" : ACTIVE
     (le telephone et le PC doivent etre sur le meme Wi-Fi).
  3. Touche "Debogage sans fil", puis "Associer l'appareil avec un code d'association".
     Ca affiche une adresse (ex. 192.168.1.42:37123) et un code a 6 chiffres.
(Ou branche le telephone par cable USB avec le "Debogage USB" active.)""")
    while True:
        input("\nQuand le code est affiche (ou le cable branche), appuie sur Entree...")
        new = [d for d in devices() if d not in before]
        if new:
            return new[0]
        addr = pairing_address()
        if addr:
            print(f'Telephone trouve : {addr}')
        else:
            addr = ask("Adresse IP:port affichee sous le code (q = annuler)")
        if addr.lower() == 'q':
            return None
        if addr:
            print(adb('pair', addr, ask('Code a 6 chiffres'), check=False, timeout=30))
            time.sleep(2)
            new = [d for d in mdns_connect() if d not in before]
            if not new:
                print('\nSur l\'ecran "Debogage sans fil", lis la ligne "Adresse IP et port"')
                print('(ce n\'est PAS le meme port que pour l\'association).')
                addr = ask('Adresse IP et port')
                if addr:
                    print(adb('connect', addr, check=False, timeout=15))
                new = [d for d in devices() if d not in before]
            if new:
                return new[0]
        if not yes('Pas de telephone connecte. Reessayer?'):
            return None


def describe(serial):
    os.environ['ANDROID_SERIAL'] = serial
    model = adb('shell', 'getprop', 'ro.product.model', check=False) or serial
    return model + ('  [Wasteland deja installe]' if installed() else '')


def choose_phone():
    """Little menu: detected phones, pair a new one, or skip (default)."""
    adb('start-server', check=False, timeout=30)
    found = devices() or mdns_connect()
    entries = [(serial, describe(serial)) for serial in found]
    os.environ.pop('ANDROID_SERIAL', None)
    print('\nInstaller Wasteland sur quel telephone?')
    for i, (serial, label) in enumerate(entries, 1):
        print(f'  {i}. {label}')
    print(f'  {len(entries) + 1}. Associer un autre telephone (debogage sans fil)')
    print(f'  {len(entries) + 2}. Passer')
    while True:
        pick = ask('Choix', str(len(entries) + 2))
        if pick.isdigit() and 1 <= int(pick) <= len(entries) + 2:
            break
    pick = int(pick)
    if pick <= len(entries):
        return entries[pick - 1][0]
    return pair_new() if pick == len(entries) + 1 else None


def push(local, remote):
    print(f'  -> {Path(local).name}')
    r = subprocess.run([ADB, 'push', '--sync', str(local), remote], capture_output=True, text=True,
                       creationflags=NO_WINDOW)
    if r.returncode != 0:
        print('     (avertissement) ' + (r.stderr or r.stdout).strip()[-300:])
        return False
    return True


def phone_cfg(dest, settings):
    shutil.copyfile(GAME / 'fallout2.cfg', dest)
    values = {
        'system': {'master_dat': '../../master.dat', 'critter_dat': '../../critter.dat',
                   'master_patches': 'data', 'critter_patches': 'data'},
        'touch': {'mobile_ui': '1', 'hud': '1', 'controls': '1'},
        'ui': {'skip_opening_movies': '2'},
        'ai': {'enabled': '0', 'server': '', 'token': '', 'timeout_ms': '45000', 'content_id': 'fallout2'},
    }
    lan = lan_ip()
    if settings.get('ai'):
        print("""
L'IA du telephone passe par ce PC : il doit etre allume avec
"Wasteland - Serveur IA (telephone)" ouvert. Sinon les PNJ parlent sans IA.

IA sur le telephone :
  1. Partout (installe et configure Tailscale sur le PC et le telephone)
  2. Seulement a la maison (meme Wi-Fi que le PC)
  3. Pas d'IA sur le telephone""")
        pick = ask('Choix', '1')
        server_ip = None
        if pick == '1':
            import tailscale
            ts_ip = tailscale.ensure_pc()
            if ts_ip and tailscale.ensure_phone(adb):
                server_ip = ts_ip
            else:
                print('Tailscale pas pret : l\'IA du telephone marchera a la maison (meme Wi-Fi).')
                print('Pour reessayer : menu Demarrer > "Wasteland - Installer sur le telephone".')
                server_ip = lan
        elif pick == '2':
            server_ip = lan
        if server_ip:
            values['ai'].update(enabled='1', server=f'http://{server_ip}:{BRAIN_PORT}', token=token())
            settings['phone_ai'] = True
            if not settings.get('firewall_ts'):
                allow_firewall()
                settings['firewall_ts'] = True
        else:
            settings['phone_ai'] = False
    for section, kv in values.items():
        for key, value in kv.items():
            cfg_set(dest, section, key, value)


def allow_firewall():
    """One UAC prompt so the phone can reach the AI server on this PC (local subnet only)."""
    rule = (f'netsh advfirewall firewall delete rule name="Wasteland IA" >nul 2>&1 & '
            f'netsh advfirewall firewall add rule name="Wasteland IA" dir=in action=allow '
            f'protocol=TCP localport={BRAIN_PORT} remoteip=localsubnet,100.64.0.0/10')
    print('Windows va demander une autorisation pour ouvrir le port de l\'IA (reseau local et Tailscale seulement).')
    subprocess.run(['powershell', '-NoProfile', '-Command',
                    f"Start-Process cmd -Verb RunAs -WindowStyle Hidden -Wait -ArgumentList '/c {rule}'"],
                   creationflags=NO_WINDOW)


def installed():
    """The app and our profile are already on the connected phone."""
    return bool(adb('shell', 'pm', 'path', PACKAGE, check=False)) and \
        adb('shell', 'ls', f'{PHONE}/profiles/{PROFILE}/fallout2.cfg', check=False).endswith('fallout2.cfg')


def run(interactive_end=True):
    """Returns 'done' or 'skipped'."""
    global ADB
    os.system('title Wasteland Reborn - Telephone')
    title('Telephone Android (optionnel)')
    if not (GAME / 'master.dat').is_file():
        fatal("Les fichiers du jeu ne sont pas installes. Lance d'abord 'Wasteland - Configurer'.")
    ADB = find_adb()
    if not ADB:
        print("Impossible d'installer adb (pas d'Internet?). Reessaie plus tard via le menu Demarrer.")
        if interactive_end:
            pause()
        return 'skipped'
    serial = choose_phone()
    if not serial:
        print('Plus tard : menu Demarrer > "Wasteland - Installer sur le telephone".')
        if interactive_end:
            pause()
        return 'skipped'
    os.environ['ANDROID_SERIAL'] = serial
    print(f"Telephone : {adb('shell', 'getprop', 'ro.product.model', check=False) or serial}")
    abi = adb('shell', 'getprop', 'ro.product.cpu.abi', check=False)
    if abi and 'arm64' not in abi:
        fatal(f'Ce telephone ({abi}) n\'est pas compatible : il faut un Android 64 bits (arm64).')

    settings = load_settings()
    print('\nInstallation de l\'application "Wasteland"...')
    out = adb('install', '-r', APK, check=False, timeout=300)
    if 'Success' not in out:
        fatal('Installation refusee : ' + out[-300:] +
              '\nSur certains telephones (Xiaomi...), active aussi "Installer via USB" dans les Options pour les developpeurs.')
    adb('shell', 'am', 'start', '-n', ACTIVITY, check=False)  # creates its storage folder
    time.sleep(4)
    adb('shell', 'am', 'force-stop', PACKAGE, check=False)

    print('\nCopie du jeu (~1,3 Go par Wi-Fi : quelques minutes, garde l\'ecran allume)...')
    profile = f'{PHONE}/profiles/{PROFILE}'
    adb('shell', 'mkdir', '-p', f'{profile}/data', check=False)
    ok = push(GAME / 'master.dat', PHONE + '/') & push(GAME / 'critter.dat', PHONE + '/')
    ok &= push(GAME / 'mods', profile + '/')
    for entry in sorted((GAME / 'data').iterdir()):
        if entry.name.lower() != 'savegame':  # never overwrite the phone's saves
            ok &= push(entry, profile + '/data/')
    for name in ['ce.dat', 'ddraw.ini', 'f2_res.ini']:
        if (GAME / name).exists():
            ok &= push(GAME / name, profile + '/')
    with tempfile.TemporaryDirectory() as tmp:
        cfg = Path(tmp) / 'fallout2.cfg'
        phone_cfg(cfg, settings)
        ok &= push(cfg, profile + '/')
        active = Path(tmp) / 'active-profile.txt'
        active.write_text(PROFILE + '\n')
        ok &= push(active, PHONE + '/')
    save_settings(settings)
    if not ok:
        print('\nCertains fichiers n\'ont pas pu etre copies (voir plus haut). Relance au besoin.')

    adb('shell', 'am', 'start', '-n', ACTIVITY, check=False)
    print('\nC\'est installe! L\'application "Wasteland" (icone verte) vient de s\'ouvrir.')
    print('Tu peux maintenant debrancher / desactiver le debogage sans fil.')
    if interactive_end:
        pause()
    return 'done'


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        pass
    except Exception as e:  # noqa: BLE001
        fatal(f'{type(e).__name__}: {e}')
