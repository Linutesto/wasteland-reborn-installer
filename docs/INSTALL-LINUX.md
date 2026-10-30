# Install Wasteland Reborn on Linux

You need your own installed copy of Fallout 2. This repository never downloads its game files. These steps work in Ubuntu, Fedora, Arch, or Steam Deck **Desktop Mode** on x86_64. Allow several gigabytes of space for the tools, game and optional HD art.

## 1. Install host packages

Use the line for your distribution in a terminal. Steam Deck's stock system is read-only; use a development container or unlock it before using pacman.

```sh
sudo apt install git cmake ninja-build rsync unzip curl tar xz-utils python3 imagemagick libsdl2-dev zlib1g-dev libpng-dev libfreetype-dev xvfb adb
sudo dnf install git cmake ninja-build rsync unzip curl tar xz python3 ImageMagick SDL2-devel zlib-devel libpng-devel freetype-devel xorg-x11-server-Xvfb android-tools
sudo pacman -S git cmake ninja rsync unzip curl tar xz python imagemagick sdl2 zlib libpng freetype2 xorg-server-xvfb android-tools
```

Run only the line that matches your system. `--linux-only` needs no Windows installer tools. To build the Windows installer too, install NSIS or Wine.

## 2. Get the installer and prepare the profile

```sh
git clone --recursive https://github.com/Linutesto/wasteland-reborn-installer.git
cd wasteland-reborn-installer
./bootstrap.sh --linux-only
```

`--linux-only` prepares the RPU profile and Linux build inputs without installing an Android SDK. If you want to build an APK too, run `./bootstrap.sh` for classic or `./bootstrap.sh --edition hd` for HD; accept the Android SDK licenses. That build takes longer. A published APK can also be downloaded by `linux/phone.sh`.

## 3. Install and play

```sh
linux/install.sh --edition classic
wasteland
```

The installer searches native Steam, Flatpak Steam and additional Steam libraries, plus common Heroic, Lutris and Wine/GOG locations. If detection fails, give it the directory that holds `master.dat` and `critter.dat`:

```sh
linux/install.sh --edition classic --game /path/to/Fallout2
```

For HD:

```sh
linux/install.sh --edition hd --game /path/to/Fallout2
wasteland
```

HD art is downloaded after your game files are verified. If packs are not published or your connection fails, you can play without them and rerun the installer later. A desktop menu entry and `~/.local/bin/wasteland` are installed. If `wasteland` is not found, add `~/.local/bin` to your shell's PATH or run `~/.local/bin/wasteland` directly.

## Optional AI NPCs

Install and start [Ollama](https://ollama.com/), then run:

```sh
linux/install.sh --edition classic --game /path/to/Fallout2 --ai
wasteland
```

The installer offers to pull the small `qwen3:4b` model. The local brain listens on `127.0.0.1:8822` while the game runs. Phone AI is off by default. To enable it, leave `wasteland-brain` running on the PC, find the PC's LAN or Tailscale address, and pass `--ai-server http://PC_IP:8822 --ai-token-file ~/.local/share/wasteland-reborn/brain/token` to `linux/phone.sh`. The phone must reach the PC on port 8822; use your own private network and keep the token private.

## Optional Android phone install

Enable USB debugging and accept your PC's prompt on the phone. With the phone connected:

```sh
adb devices
linux/phone.sh --edition classic --dry-run
linux/phone.sh --edition classic
```

For HD, use `--edition hd`. The script installs the matching APK, creates the app's storage and RPU profile, copies your game and music, and zips HD art before transfer. It does not overwrite phone saves. If no local APK exists, it downloads the current released APK. You may give `--apk /path/to/file.apk` instead.

For wireless debugging, open **Developer options → Wireless debugging → Pair device with pairing code**. The pairing address and six-digit code are different from the later connection port:

```sh
linux/phone.sh --edition classic --pair PHONE_IP:PAIR_PORT --code 123456 --connect PHONE_IP:CONNECT_PORT --dry-run
```

Remove `--dry-run` only after checking the printed commands and package. With several devices, use `--serial SERIAL` from `adb devices`.

## Update and remove

```sh
git pull --recurse-submodules
./bootstrap.sh --linux-only
linux/install.sh --edition classic --game /path/to/Fallout2
linux/uninstall.sh
```

The uninstall manifest removes files the installer placed and keeps modified files and saves. If both editions were installed under one prefix, one uninstall removes both. A custom install prefix uses `--prefix DIR` on install, phone and uninstall.

## Troubleshooting

- **No sound:** check your system audio output and SDL2/PipeWire packages; try another output device.
- **Black window:** check `master.dat` and `critter.dat`, then launch `~/.local/bin/wasteland` from a terminal to see engine errors. A missing mod profile calls for rerunning `./bootstrap.sh --linux-only`.
- **adb unauthorized:** unlock the phone, accept the USB debugging prompt and rerun `adb devices`.
- **Phone not found:** use a data capable cable or check that PC and phone share Wi-Fi for wireless debugging. The pairing and connection ports differ.
- **HD art missing:** rerun `linux/install.sh --edition hd --game /path/to/Fallout2` when the packs are published and reachable.
- **Brain not reachable:** check `ollama list`, start Ollama, and check for another program on local port 8822. Phone AI is intentionally off in the basic phone install.
