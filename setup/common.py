"""Shared helpers for the Windows installer, launcher and phone setup.

Runs on the bundled embeddable Python (stdlib only). Layout under ROOT:
game/ (engine + RPU profile), brain/, python/, setup/, phone/, userdata/.
"""
import json
import os
import re
import secrets
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / 'game'
BRAIN = ROOT / 'brain'
USERDATA = ROOT / 'userdata'
SETTINGS = USERDATA / 'settings.json'
TOKEN = USERDATA / 'token'
PYTHON = ROOT / 'python' / 'python.exe'
PYTHONW = ROOT / 'python' / 'pythonw.exe'
BRAIN_PORT = 8822
OLLAMA = 'http://127.0.0.1:11434'
NO_WINDOW = 0x08000000 if os.name == 'nt' else 0  # CREATE_NO_WINDOW


def load_settings():
    try:
        return json.loads(SETTINGS.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def save_settings(settings):
    USERDATA.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2), encoding='utf-8')


def token():
    if not TOKEN.is_file():
        USERDATA.mkdir(parents=True, exist_ok=True)
        TOKEN.write_text(secrets.token_urlsafe(32), encoding='utf-8')
    return TOKEN.read_text(encoding='utf-8').strip()


def cfg_set(path, section, key, value):
    """Set key=value in [section] of a Fallout ini, keeping everything else."""
    lines = Path(path).read_text(encoding='latin-1').splitlines()
    out, current, done, seen = [], None, False, False
    for line in lines:
        m = re.match(r'\s*\[([^\]]+)\]', line)
        if m:
            if current == section and not done:
                out.append(f'{key}={value}')
                done = True
            current, seen = m.group(1).strip().lower(), seen or m.group(1).strip().lower() == section
        elif current == section and re.match(rf'\s*{re.escape(key)}\s*=', line, re.I):
            if not done:
                out.append(f'{key}={value}')
                done = True
            continue
        out.append(line)
    if not done:
        if not seen:
            out += ['', f'[{section}]']
        out.append(f'{key}={value}')
    Path(path).write_text('\n'.join(out) + '\n', encoding='latin-1')


def http_json(url, body=None, timeout=5):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read() or b'{}')


def ollama_models():
    """Installed model names, or None when Ollama isn't answering."""
    try:
        return [m['name'] for m in http_json(OLLAMA + '/api/tags', timeout=3).get('models', [])]
    except Exception:  # noqa: BLE001
        return None


def ollama_exe():
    for candidate in [Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/Ollama/ollama.exe',
                      Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Ollama/ollama.exe']:
        if candidate.is_file():
            return candidate
    from shutil import which
    found = which('ollama')
    return Path(found) if found else None


def start_ollama(wait=20):
    """Starts Ollama if it is installed but not running. True when it answers."""
    import time
    if ollama_models() is not None:
        return True
    exe = ollama_exe()
    if exe is None:
        return False
    subprocess.Popen([str(exe), 'serve'], creationflags=NO_WINDOW,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(wait * 2):
        time.sleep(0.5)
        if ollama_models() is not None:
            return True
    return False


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.168.1.1', 9))  # no packet is sent; picks the LAN interface
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def brain_up(timeout=1.5):
    try:
        return http_json(f'http://127.0.0.1:{BRAIN_PORT}/v1/health', timeout=timeout).get('ok') is True
    except Exception:  # noqa: BLE001
        return False


def ask(prompt, default=None):
    suffix = f' [{default}]' if default else ''
    try:
        answer = input(f'{prompt}{suffix} : ').strip()
    except EOFError:
        answer = ''
    return answer or (default or '')


def yes(prompt, default=True):
    answer = ask(prompt + (' (O/n)' if default else ' (o/N)')).lower()
    return default if not answer else answer[0] in 'oy'


def pause():
    ask('\nAppuie sur Entree pour fermer')


def title(text):
    print('\n' + '=' * 60 + '\n  ' + text + '\n' + '=' * 60)


def fatal(text):
    print('\n[ERREUR] ' + text)
    pause()
    sys.exit(1)
