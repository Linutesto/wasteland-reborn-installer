# Linux install report — 2026-10-30

## Built

- `bootstrap.sh --linux-only` prepares the pinned engine submodule, HD downloader and RPU profile without Windows/Android toolchains.
- `linux/install.sh` detects an owned Fallout 2 copy (Steam native/Flatpak and VDF libraries, Heroic metadata, Lutris/Wine/GOG), validates both DATs, builds the Linux engine if needed, generates `ce.dat`, installs RPU and music, writes edition settings, downloads published HD packs, and creates a desktop entry, icon and `wasteland` launcher. `--ai` offers the small Ollama model and runs the local brain on `127.0.0.1`; `wasteland-brain` is an explicit network listener for phone AI.
- `linux/uninstall.sh` removes checksum-matching files listed in its per-prefix manifest. It preserves modified files and saves.
- `linux/phone.sh` supports local or latest-release APK, USB or wireless adb pairing, an explicit device serial, profile/game transfer, explicit phone AI server/token settings and HD art as one ZIP. Phone tests used `--dry-run` only. No app was installed or changed on a phone.
- English and French step-by-step guides are linked from the README.

## Fresh-clone proof

A `file://` recursive clone of the final scratch branch checked out the pinned engine submodule. `./bootstrap.sh --linux-only` completed with verified RPU and FO2Tweaks archives and generated `build/profile`. A prior fresh-clone run downloaded the full RPU archive; the final replay reused that verified archive to avoid a second large download. CMake/Ninja built `fallout2-ce` and `ce-dat-tool` from the submodule. The game source was a **copy** of the player's owned files in scratch storage; no source game/profile was written.

Both commands completed in the clone with `HOME` and `--prefix` directed to scratch locations:

```sh
linux/install.sh --edition classic --game SCRATCH_GAME --prefix SCRATCH_PREFIX
linux/install.sh --edition hd --game SCRATCH_GAME --prefix SCRATCH_PREFIX
```

`master.dat` and `critter.dat` were copied into both editions; uppercase source `DATA/SOUND/MUSIC` was found and copied. The classic config has `hd_art=0`, HD has `hd_art=1` and `hd_cache_mb=256`. The published HD manifest currently has no packs, so no enhanced image was downloaded. Both editions reached the main menu on Xvfb with Mesa software rendering and a dummy audio device. The installed `wasteland` launcher also reached the menu.

Screenshots: [classic main menu](linux/screenshots/classic-menu.png), [HD main menu](linux/screenshots/hd-menu.png). They show the same art because no HD pack is published. A default host Xvfb run crashed in its NVIDIA EGL driver; selecting the Mesa EGL vendor made the headless proof work. The game itself needed `SDL_AUDIODRIVER=dummy` in that headless environment.

`linux/uninstall.sh --prefix SCRATCH_PREFIX` removed the recorded files, desktop entry and launcher. One config intentionally changed after installation was preserved, as were untracked saves.

## Tests

- `python3 -m unittest discover -s linux/tests -v`: **5 passed** (Steam, Flatpak, Heroic/Lutris, libraryfolders.vdf, uppercase music, config and manifest).
- Python compile and `bash -n` on new scripts and bootstrap: passed.
- `linux/phone.sh --edition classic --dry-run` and `--edition hd --dry-run`: printed package-specific adb commands in the final clone. The final HD profile had no published art, so it printed an absence notice. A separate fake HD-art fixture printed one ZIP push plus phone unzip. No adb install or push was executed.
- Host package-manager commands, a real phone transfer, an Ollama model pull, and published HD art were not run in this sandbox. The guides include distro-specific and placeholder commands which cannot all be executed on one host; their clone/bootstrap/install/play/uninstall equivalents were exercised in scratch.

## Open issues

1. This worktree's Git metadata is outside the sandbox's writable roots. `git commit` here failed with `index.lock: Read-only file system`; changes are present but **not committed on `agent/linux`**. A writable scratch clone at `/tmp/wasteland-linux-proof` holds reviewable commits, and `/tmp/wasteland-linux.patch` is a binary-safe transfer patch. They must be transferred to this worktree branch by an environment with Git metadata write access. No push or GitHub write occurred.
2. HD visual quality remains unverified until published packs appear. The downloader ran against the current empty manifest.
3. Phone execution was restricted to dry runs. The device-side `unzip` command and app-owned storage behavior need a throwaway-package test before general use.
4. `--ai` was installed in scratch with the model pull declined; a token, enabled config and `wasteland-brain` command were verified. An Ollama conversation was not tested end to end.
