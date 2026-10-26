# Wasteland Reborn

**Fallout 2 on your Android phone**, with the **Restoration Project (RPU)** +
FO2Tweaks on the open-source **Fallout 2 Community Edition** engine (mobile
fork), a full touch UI, and **NPCs you can talk to freely through a local AI**
(optional, via Ollama).

*[Version française plus bas](#wasteland-reborn--installateur-windows)*

## ⬇️ Download

📱 **Android: [Wasteland-arm64.apk](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest/download/Wasteland-arm64.apk)** (≈ 8 MB). If the Wasteland app is already installed, this is an update: your saves stay. The game itself (your Fallout 2 files) is imported in the app, or installed from the PC with the Windows installer.

💻 **Windows installer: [WastelandReborn-Setup.exe](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest)** (≈ 830 MB, Windows 10/11 64-bit, English or French). It sets everything up and pushes the game to your phone.

## You need

- **Your own copy of Fallout 2** installed (Epic, Steam or GOG). No game files
  are included: the setup finds your game and copies `master.dat`,
  `critter.dat` and the music.
- An Android 64-bit phone (wireless debugging on, for the install from the PC).
- Optional: [Ollama](https://ollama.com) for the AI.

## Install

1. Run `WastelandReborn-Setup.exe` and pick English. Windows may show
   "Windows protected your PC" (unsigned file) → **More info** → **Run anyway**.
2. At the end a setup window asks about your game, the AI (if Ollama is
   there), then a small phone menu (pick a phone, pair one with the 6-digit
   code, or skip). adb (Google's official Android tool) is downloaded
   automatically.
3. Play on the phone (the **Wasteland** app). The desktop icon also starts it
   on the PC with classic mouse controls.

In dialogues, pick **[Speak freely]** and type whatever you want to the
character.

Start menu › Wasteland Reborn: *Setup* (turn the AI on later), *Install on
phone*, *AI server (phone)*.

**AI on the phone** runs on the PC (on, with *AI server* open). The menu offers
"Everywhere": the setup installs and configures [Tailscale](https://tailscale.com)
(free private VPN) on the PC and the phone; log in with **the same account** on
both. Or "Only at home" (same Wi-Fi), or no AI on the phone. Without the
server the game plays normally, offline.

## Build from source

Everything is rebuilt from this repository on Linux x86_64. No Fallout 2 file is
downloaded or included: players add their own at install time.

```sh
git clone --recursive https://github.com/Linutesto/wasteland-reborn-installer
cd wasteland-reborn-installer
./bootstrap.sh        # toolchains, RPU profile, APK (asks you to accept the Android SDK licenses)
windows/build.sh      # windows/dist/WastelandReborn-Setup.exe
```

Host packages: `git cmake ninja rsync unzip curl tar xz python3`, ImageMagick,
SDL2 and zlib development files, and `makensis` or Wine.
`./bootstrap.sh --no-android` skips the Android SDK; then pass an APK:
`APK=path/to.apk windows/build.sh`.

| Part | Where | What |
| --- | --- | --- |
| Engine | `src/imbaner_fallout2-ce-mobile` (submodule, branch `wasteland-reborn`) | fallout2-ce mobile fork + touch UI, AI free talk, Windows build |
| AI brain | `brain/` | Python HTTP server between the game and Ollama / an OpenAI-compatible server (`python3 -m unittest discover -s brain/tests`) |
| Game profile | `profile/` + `tools/mkprofile.py` | RPU + FO2Tweaks from their GitHub releases (pinned sha256), the game config and overlay → `build/profile` |
| Windows installer | `windows/` | NSIS installer, setup scripts (game detection, Ollama, phone over adb, Tailscale) |
| Toolchains | `bootstrap.sh` → `toolchain/` | llvm-mingw 20261020, JDK 17, Android SDK 35 / NDK 27.3, embeddable Python 3.13.9, NSIS 3.11 |

Your APK is signed with your own Android debug key, so it can't update the
released app (Android refuses a different signature): back up your saves,
uninstall the released app, then install yours.

## Credits

- [Fallout 2 CE](https://github.com/alexbatalov/fallout2-ce) and the
  [mobile fork](https://github.com/imbaner/fallout2-ce-mobile)
- [Restoration Project (RPU)](https://github.com/BGforgeNet/Fallout2_Restoration_Project)
  and [FO2Tweaks](https://github.com/BGforgeNet/FO2tweaks) by BGforgeNet
- Python (embeddable), NSIS, Ollama

Fallout is a trademark of Bethesda Softworks. Unofficial fan project.

---

# Wasteland Reborn — installateur Windows

Fallout 2 avec le **Restoration Project (RPU)** + FO2Tweaks, sur le moteur
open source **Fallout 2 Community Edition** (fork mobile), avec des **PNJ qui
répondent en texte libre grâce à une IA locale** (optionnelle, via Ollama).
Peut aussi installer le jeu sur un téléphone Android.

## ⬇️ Télécharger

📱 **Android : [Wasteland-arm64.apk](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest/download/Wasteland-arm64.apk)** (≈ 8 Mo) — si l'app Wasteland est déjà installée, c'est une mise à jour : tes sauvegardes restent. Le jeu lui-même (fichiers de Fallout 2) s'importe dans l'app, ou s'installe depuis le PC avec l'installateur Windows.

💻 **Windows : [WastelandReborn-Setup.exe](https://github.com/Linutesto/wasteland-reborn-installer/releases/latest)** (≈ 830 Mo, Windows 10/11 64 bits, anglais ou français)

## Il te faut

- **Ta propre copie de Fallout 2** installée (Epic, Steam ou GOG). Aucun
  fichier du jeu n'est inclus : l'installation retrouve ton jeu et copie
  `master.dat`, `critter.dat` et la musique.
- Optionnel : [Ollama](https://ollama.com) pour l'IA.
- Optionnel : un téléphone Android 64 bits (débogage sans fil activé).

## Installation

1. Lance `WastelandReborn-Setup.exe` et choisis Français. Windows peut afficher « Windows a
   protégé votre ordinateur » (fichier non signé) → **Informations
   complémentaires** → **Exécuter quand même**.
2. À la fin, une fenêtre de configuration te pose les questions :
   ton jeu, l'IA (si Ollama est là), puis un petit menu pour le téléphone
   (choisir un téléphone, en associer un avec le code à 6 chiffres, ou passer).
   adb (outil Android officiel de Google) est téléchargé automatiquement.
3. Joue avec l'icône **Wasteland Reborn** sur le bureau.

En dialogue, choisis **[Speak freely]** et écris ce que tu veux au personnage
(en anglais, la langue du jeu).

Menu Démarrer › Wasteland Reborn : *Configurer* (activer l'IA plus tard),
*Installer sur le téléphone*, *Serveur IA (téléphone)*.

**IA sur le téléphone** : elle passe par le PC (allumé, *Serveur IA* ouvert).
Le menu propose « Partout » : l'installation installe et configure
[Tailscale](https://tailscale.com) (VPN privé gratuit) sur le PC et le
téléphone. Connecte-toi avec **le même compte** sur les deux. Ou « Seulement
à la maison » (même Wi-Fi), ou pas d'IA sur le téléphone.

## Construire depuis les sources

Tout se reconstruit depuis ce dépôt sous Linux x86_64 (aucun fichier de Fallout 2
n'est téléchargé ni inclus) :

```sh
git clone --recursive https://github.com/Linutesto/wasteland-reborn-installer
cd wasteland-reborn-installer
./bootstrap.sh        # outils, profil RPU, APK (tu acceptes les licences du SDK Android)
windows/build.sh      # windows/dist/WastelandReborn-Setup.exe
```

Détails (paquets requis, structure du dépôt) : voir la section anglaise
« Build from source » plus haut.

## Crédits

- [Fallout 2 CE](https://github.com/alexbatalov/fallout2-ce) et le
  [fork mobile](https://github.com/imbaner/fallout2-ce-mobile)
- [Restoration Project (RPU)](https://github.com/BGforgeNet/Fallout2_Restoration_Project)
  et [FO2Tweaks](https://github.com/BGforgeNet/FO2tweaks) — BGforgeNet
- Python (embeddable), NSIS, Ollama

Fallout est une marque de Bethesda Softworks. Projet de fans, non officiel.
