WASTELAND REBORN v1.4 — Fallout 2 for Android and Windows
=============================================================================

WHAT YOU NEED
- Windows 10 or 11 (64-bit)
- Your own Fallout 2, installed (Epic, Steam or GOG). The setup finds your
  game and takes its files: nothing from the game is included here.
- Android 7.0 or newer, arm64. Classic APK: 5.2 MB; HD APK: 3.7 MB.
  Apps are named Wasteland and Wasteland HD. APK updates keep saves.
- About 2 GB free for game files; keep at least 3 GB free with HD art.
  HD packs: world 440 MB (9,422 images), heads 468 MB (1,352 images);
  about 910 MB to download and about 2 GB unpacked with the game.
- Fallout 2 is not included. Bring your own copy. Unofficial fan project.
- Optional: Ollama (https://ollama.com) for the AI NPCs.

INSTALL
1. Double-click WastelandReborn-Setup.exe and pick English.
   Windows may show "Windows protected your PC" (the file is not signed):
   click "More info", then "Run anyway".
2. Follow the setup. At the end a black window opens and asks about your
   game, the AI, then the phone.

HD EDITION / UNATTENDED INSTALL
- WastelandRebornHD-Setup.exe installs separately in
  %LOCALAPPDATA%\WastelandRebornHD. Saves and settings stay separate.
- Run either installer with /S to install unattended. It looks for Fallout 2
  using the normal Epic/Steam/GOG detection, copies the game if found and
  skips optional AI and phone configuration. Run Start menu > Wasteland -
  Setup afterwards to configure them interactively.
- The HD installer attempts the optional published art packs after it finds
  Fallout 2. If offline, the game installation still succeeds. Read
  userdata\setup-install.log in the install directory for the result, then
  rerun Wasteland - Setup when the packs are available.
- Uninstall removes the app files and registry/shortcuts, preserving saved
  games under game\data\savegame and AI userdata for manual backup.
- Offline test suite: python3 -m unittest discover -s windows/tests -v
- On a Linux host allowing Wine/Xvfb, after building both setup executables:
  bash windows/tests/test_wine_install.sh
  The Wine test uses tests/wine-hd only and disables host desktop integration.

THE PHONE
- The setup installs adb (Google's official Android tool) by itself.
- On the phone: Developer options > Wireless debugging ON, same Wi-Fi as the
  PC. A small menu lets you pick the phone (or pair one with the 6-digit
  code), or skip.
- Later: Start menu > "Wasteland - Install on phone".
- Classic app: "Wasteland"; HD app: "Wasteland HD".
- AI on the phone: the PC must be on with "Wasteland - AI server (phone)"
  open. Pick "Everywhere" in the menu so it works away from home: the setup
  installs Tailscale (free private VPN) on the PC and the phone. Log in with
  the SAME account on both.
- Without the AI server the game plays normally, offline.

THE AI (if Ollama is installed)
- In dialogues, pick "[Speak freely]" and type what you want to say to the
  character (in English, the game's language).
- The first message can take a few seconds (the model loads).
- Installed Ollama afterwards? Start menu > "Wasteland - Setup".

PLAYING ON THE PC
- The desktop icon "Wasteland Reborn" starts the game on the PC too
  (classic mouse controls).

Saves are in the install folder, game\data\savegame
(by default %LOCALAPPDATA%\WastelandReborn).
