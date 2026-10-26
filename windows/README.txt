WASTELAND REBORN — Fallout 2 Restoration Project + AI NPCs, for Android phones
=============================================================================

WHAT YOU NEED
- Windows 10 or 11 (64-bit)
- Your own Fallout 2, installed (Epic, Steam or GOG). The setup finds your
  game and takes its files: nothing from the game is included here.
- An Android 64-bit phone to play on (the game is made for touch).
- Optional: Ollama (https://ollama.com) for the AI NPCs.

INSTALL
1. Double-click WastelandReborn-Setup.exe and pick English.
   Windows may show "Windows protected your PC" (the file is not signed):
   click "More info", then "Run anyway".
2. Follow the setup. At the end a black window opens and asks about your
   game, the AI, then the phone.

THE PHONE
- The setup installs adb (Google's official Android tool) by itself.
- On the phone: Developer options > Wireless debugging ON, same Wi-Fi as the
  PC. A small menu lets you pick the phone (or pair one with the 6-digit
  code), or skip.
- Later: Start menu > "Wasteland - Install on phone".
- The app is called "Wasteland" (green icon).
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
