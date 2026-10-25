"""Wasteland Reborn launcher: starts the AI brain (if enabled) and the game.

    pythonw launcher.py           play on the PC
    python  launcher.py --server  only the AI server, for the phone (console stays open)
"""
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (BRAIN, BRAIN_PORT, GAME, NO_WINDOW, OLLAMA, PYTHON, USERDATA, brain_up,
                    http_json, lan_ip, load_settings, start_ollama, token)


def message(text):
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, text, 'Wasteland Reborn', 0x40)


def start_brain(settings, visible):
    host = '0.0.0.0' if settings.get('phone_ai') else '127.0.0.1'
    token()  # creates the token file on first use
    env = dict(os.environ, BRAIN_LLM_TIMEOUT='40', BRAIN_LLM_SLOT='-1')
    args = [str(PYTHON), str(BRAIN / 'server.py'), '--host', host, '--port', str(BRAIN_PORT),
            '--llm', OLLAMA, '--llm-api', 'ollama', '--model', settings['model'],
            '--db', str(USERDATA / 'brain.db'), '--log-dir', str(USERDATA / 'logs'),
            '--token-file', str(USERDATA / 'token')]
    if visible:
        return subprocess.Popen(args, env=env)
    log = open(USERDATA / 'brain.log', 'a', encoding='utf-8')
    return subprocess.Popen(args, env=env, stdout=log, stderr=log, creationflags=NO_WINDOW)


def warm_up(model):
    """Loads the model now so the first conversation isn't the slow one."""
    try:
        http_json(OLLAMA + '/api/generate', {'model': model, 'prompt': '', 'keep_alive': '30m'}, timeout=120)
    except Exception:  # noqa: BLE001
        pass


def main():
    server_only = '--server' in sys.argv
    settings = load_settings()
    USERDATA.mkdir(parents=True, exist_ok=True)
    if not (GAME / 'master.dat').is_file():
        message("Le jeu n'est pas encore configure.\nLance 'Wasteland - Configurer' dans le menu Demarrer.")
        return
    brain = None
    if settings.get('ai') and settings.get('model'):
        if not start_ollama():
            if server_only:
                print("Ollama ne repond pas : ouvre Ollama puis relance.")
                input()
                return
            message("Ollama ne repond pas : le jeu demarre sans IA.\n(Ouvre Ollama avant le jeu pour avoir l'IA.)")
        elif not brain_up():
            brain = start_brain(settings, visible=server_only)
            threading.Thread(target=warm_up, args=(settings['model'],), daemon=True).start()
            for _ in range(40):
                if brain_up() or brain.poll() is not None:
                    break
                time.sleep(0.25)
    elif server_only:
        print("L'IA n'est pas activee. Lance 'Wasteland - Configurer' pour l'activer.")
        input()
        return

    if server_only:
        import tailscale
        ts = tailscale.pc_ip() if tailscale.exe() else None
        print(f"\nServeur IA pour le telephone : http://{lan_ip()}:{BRAIN_PORT}"
              + (f"  (Tailscale : http://{ts}:{BRAIN_PORT})" if ts else ""))
        print("Laisse cette fenetre ouverte pendant que tu joues sur le telephone.")
        print("Ferme-la pour arreter.\n")
        try:
            if brain:
                brain.wait()
            else:
                print("(Le serveur tournait deja.)")
                input()
        except KeyboardInterrupt:
            pass
        return

    try:
        subprocess.run([str(GAME / 'fallout2-ce.exe')], cwd=str(GAME))
    finally:
        if brain and brain.poll() is None:
            brain.terminate()


if __name__ == '__main__':
    main()
