"""Tailscale on this PC and on the phone, so the phone reaches the PC's AI from anywhere.

Both devices log in to the player's own Tailscale account (browser on the PC,
the app on the phone): no auth key ships in this public installer.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
import webbrowser
from pathlib import Path

from common import NO_WINDOW, ask, t

MSI_URL = 'https://pkgs.tailscale.com/stable/tailscale-setup-latest-amd64.msi'
APK_URL = 'https://pkgs.tailscale.com/stable/tailscale-android-universal-latest.apk'
ANDROID_PACKAGE = 'com.tailscale.ipn'
LOGIN_WAIT_S = 300


def exe():
    for candidate in [Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Tailscale/tailscale.exe',
                      shutil.which('tailscale')]:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    return None


def run(*args, timeout=20):
    try:
        r = subprocess.run([exe(), *args], capture_output=True, text=True, timeout=timeout,
                           creationflags=NO_WINDOW)
        return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired, TypeError):
        return ''


def pc_ip():
    """This PC's Tailscale IPv4 when logged in, else None."""
    out = run('ip', '-4')
    return out.splitlines()[0] if re.match(r'100\.\d+\.\d+\.\d+', out) else None


def status():
    try:
        return json.loads(run('status', '--json') or '{}')
    except ValueError:
        return {}


def tailnet_ips():
    return {ip for p in (status().get('Peer') or {}).values() for ip in p.get('TailscaleIPs') or []}


def phone_ip(adb):
    """The phone's Tailscale IPv4 when its VPN is up, else None."""
    out = adb('shell', 'ip', '-4', 'addr', 'show', 'tun0', check=False)
    m = re.search(r'inet (100\.\d+\.\d+\.\d+)', out)
    return m.group(1) if m else None


def download(url, suffix):
    path = Path(tempfile.gettempdir()) / ('wasteland-tailscale' + suffix)
    print(t('  telechargement...', '  downloading...'))
    with urllib.request.urlopen(url, timeout=300) as r, open(path, 'wb') as f:
        shutil.copyfileobj(r, f, 1 << 20)
    return path


def ensure_pc():
    """Installs and logs in Tailscale on this PC. Returns its Tailscale IP or None."""
    if pc_ip():
        return pc_ip()
    if not exe():
        print(t('\nInstallation de Tailscale sur le PC (Windows va demander une autorisation)...',
                '\nInstalling Tailscale on the PC (Windows will ask for permission)...'))
        try:
            msi = download(MSI_URL, '.msi')
        except OSError as e:
            print(t('  echec : ', '  failed: ') + str(e))
            return None
        subprocess.run(['powershell', '-NoProfile', '-Command',
                        f"Start-Process msiexec -Verb RunAs -Wait -ArgumentList '/i \"{msi}\" /quiet /norestart'"],
                       creationflags=NO_WINDOW)
        for _ in range(30):
            if exe():
                break
            time.sleep(1)
        if not exe():
            print(t('  Tailscale ne s\'est pas installe (autorisation refusee?).', '  Tailscale did not install (permission refused?).'))
            return None
        time.sleep(5)  # the service starts after the install
    print(t('\nConnexion de Tailscale sur le PC : une page web va s\'ouvrir.\n'
            'Connecte-toi (Google, Microsoft...). Utilise le MEME compte sur le telephone ensuite.',
            '\nSigning Tailscale in on the PC: a web page will open.\n'
            'Log in (Google, Microsoft...). Use the SAME account on the phone afterwards.'))
    proc = subprocess.Popen([exe(), 'up', '--unattended'], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, creationflags=NO_WINDOW)
    opened = False
    deadline = time.time() + LOGIN_WAIT_S
    while time.time() < deadline and not pc_ip():
        line = proc.stdout.readline() if proc.poll() is None else ''
        url = re.search(r'https://login\.tailscale\.com/\S+', line or '')
        if url and not opened:
            webbrowser.open(url.group(0))
            print('  ' + url.group(0))
            opened = True
        if not line:
            time.sleep(1)
    if proc.poll() is None:
        proc.terminate()
    ip = pc_ip()
    print(t('  PC connecte a Tailscale : ', '  PC connected to Tailscale: ') + ip if ip
          else t('  Tailscale pas connecte sur le PC.', '  Tailscale not connected on the PC.'))
    return ip


def ensure_phone(adb):
    """Installs Tailscale on the phone (adb) and waits until it is on the PC's tailnet."""
    def joined():
        ip = phone_ip(adb)
        return ip if ip and ip in tailnet_ips() else None

    if joined():
        print(t('  Telephone deja connecte a Tailscale.', '  Phone already connected to Tailscale.'))
        return True
    if not adb('shell', 'pm', 'path', ANDROID_PACKAGE, check=False):
        print(t('\nInstallation de Tailscale sur le telephone...', '\nInstalling Tailscale on the phone...'))
        try:
            apk = download(APK_URL, '.apk')
        except OSError as e:
            print(t('  echec : ', '  failed: ') + str(e))
            return False
        out = adb('install', '-r', apk, check=False, timeout=300)
        if 'Success' not in out:
            print(t('  echec : ', '  failed: ') + out[-200:])
            return False
    adb('shell', 'monkey', '-p', ANDROID_PACKAGE, '-c', 'android.intent.category.LAUNCHER', '1', check=False)
    print(t("""
Sur le telephone, l'application Tailscale vient de s'ouvrir :
  - connecte-toi avec le MEME compte que sur le PC,
  - accepte la demande de connexion VPN (c'est Tailscale).
J'attends que le telephone apparaisse (Entree pour passer)...""", """
The Tailscale app just opened on the phone:
  - log in with the SAME account as on the PC,
  - accept the VPN connection request (that's Tailscale).
Waiting for the phone to show up (Enter to skip)..."""))
    import threading
    skipped = threading.Event()
    threading.Thread(target=lambda: (ask(''), skipped.set()), daemon=True).start()
    deadline = time.time() + LOGIN_WAIT_S
    while time.time() < deadline and not skipped.is_set():
        if joined():
            print(t('  Telephone connecte a Tailscale.', '  Phone connected to Tailscale.'))
            return True
        time.sleep(2)
    if phone_ip(adb):
        print(t('  Le telephone est sur Tailscale, mais pas avec le meme compte que le PC.', '  The phone is on Tailscale, but not with the same account as the PC.'))
    else:
        print(t('  Telephone pas encore connecte a Tailscale.', '  Phone not connected to Tailscale yet.'))
    return False
