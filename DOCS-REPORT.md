# DOCS-REPORT — install guides for non-developers (task D, 2026-10-30)

Windows install guides written from the real code, links added in every
linked repo, links and private-data checked. **No push, no `gh` write, no
branch switch, `linux/` untouched.**

## Files written, per repo

| Repo | Worktree (branch) | Files |
| --- | --- | --- |
| wasteland-reborn-installer | `~/agent-wt/installer` (`agent/release`) | `docs/INSTALL-WINDOWS.md`, `docs/INSTALL-WINDOWS.fr.md`, `docs/TROUBLESHOOTING.md`, `docs/TROUBLESHOOTING.fr.md`, links in `README.md` (EN section *📖 Install guides* + FR section *📖 Guides d'installation*), this report |
| wasteland-hd-assets | `~/agent-wt/assets` (`agent/docs`) | `README.md`: new *For players: install it with the installer or the app* (guide links), *Manual copy*, *packs.json, for players*; *Use it* trimmed to point at them |
| wasteland-hd-tools | `~/agent-wt/tools-docs` (`agent/docs`) | `README.md`: new *Just want to play? You don't need this repository* before the developer docs (which are kept unchanged) |
| fallout2-ce-mobile | `~/agent-wt/engine-docs` (`agent/docs`) | `README.md`: short *Wasteland Reborn* section at the top (after the fan-project notice), linking the guides; nothing else changed |

Working notes (not committed): `tmp-docs/PROGRESS.md` in this worktree.

## What the guides cover

`INSTALL-WINDOWS.md` / `.fr.md` — the nine required sections: before you
start (Windows 10/11 64-bit, ~3 GB, how to open the Epic/Steam/GOG folder
and check `master.dat` + `critter.dat`, phone arm64/Android 7.0+, Ollama
<https://ollama.com> and the model the setup offers) → download (classic
vs HD, SmartScreen *More info → Run anyway*, `certutil -hashfile … SHA256`
against `SHA256SUMS.txt`) → install on the PC (every installer page and
every console question) → prepare the phone (Developer options,
wireless debugging, pairing code, USB fallback) → install on the phone
(the menu, timings, the phone-only APK path) → HD art → AI NPCs (PC,
home, *Everywhere* with Tailscale) → update / backup / uninstall →
troubleshooting table. One action per step, each followed by what you
should see; French version in tutoiement, quoting the program's own
(unaccented) PC strings verbatim and Android's accented strings verbatim.

`TROUBLESHOOTING.md` / `.fr.md` — one anchored section per failure mode:
SmartScreen, antivirus quarantine, setup can't find Fallout 2, phone not
found / pairing fails, unauthorized, black screen, blank dialogue text, no
AI reply, HD download stuck, out of space, Epic files not downloaded or
not verified, plus "still stuck" (what to include in an issue).

### Sources read (labels quoted, not remembered)

- `windows/installer.nsi` — pages (Welcome → Directory → InstFiles →
  Finish), the `Language / Langue` dialog, EN/FR Welcome and Finish texts,
  Start-menu entries, `Desinstaller.exe`, uninstaller keeping
  `game\data\savegame` + `userdata`.
- `windows/setup/setup.py` — `1/3` game → HD art → `2/3` AI questions,
  model list (`qwen3:4b` default, ~2.6 GB), Epic/Steam/GOG detection and
  the manual folder-picker wording.
- `windows/setup/phone.py` — phone menu (default = *Skip*), pairing
  instructions block, adb download (~7 MB), arm64 refusal, Xiaomi
  "Install via USB", the ~1.3 GB copy, AI menu **1 Partout / 2 maison /
  3 sans IA (default 1)**, firewall UAC text.
- `windows/setup/tailscale.py`, `launcher.py` — Tailscale install/login
  texts, `Serveur IA pour le telephone : http://…:8822`, "keep this window
  open" text, Ollama errors.
- `windows/README.txt`, `windows/LISEZ-MOI.txt` — the quick text shipped
  in the installer.
- Engine `os/android`: `res/values/strings.xml` + `values-fr/strings.xml`,
  `ImportActivity` (*Files of the game*, *Choose the folder*, *Choose an
  archive*, *Copy*), `HdUpdateActivity` (7-second gate, *Download* /
  *Later*, resume), `build.gradle` (`minSdk 24` = Android 7.0),
  `AndroidManifest.xml` (launcher = `HdUpdateActivity`), flavor names
  `Wasteland` / `Wasteland HD`.
- Engine `src/game_dialog.cc` — `[Speak freely]` is fixed English in every
  language; `src/npc_brain.cc` — the option only appears when `ai enabled`
  *and* the brain server answered (hence "no `[Speak freely]` = AI off").
- `files/ce.dat/text/{english,french}/game/ce.msg` — French `ce.msg` is a
  518-byte stub, so engine UI labels stay English on French phones.
- NSIS stock strings (`nsis-dev/nsis` `Contrib/Language files/`): *Choose
  Install Location* / *Choisissez le dossier d'installation*,
  `&Next >` / `&Suivant >`, `&Install` / `&Installer`, `&Finish` /
  `&Fermer`; the directory page button is *Install* (NSIS docs: "the
  default install button text (of \"Install\")").
- French Windows SmartScreen wording checked on the web: **« Plus
  d'informations » → « Exécuter quand même »**.

## Checks run

- **Link check** (`tmp-docs/checklinks.mjs`, github-slugger anchors + file
  existence) over all eight edited markdown files: every relative link
  resolves to a file in a worktree and every `#anchor` matches a real
  heading — including the accented French anchors
  (`#le-téléphone-nest-pas-trouvé-ou-lassociation-échoue`, …).
  - The only unresolved targets are the **4 intentional
    `docs/INSTALL-LINUX.md` links** (2 in the guides, 2 in `README.md`),
    which Codex's `agent/linux` branch creates — the task says to link to
    them because they exist after merge.
- **URL policy**: every URL used is one the READMEs already use
  (`github.com/Linutesto/wasteland-reborn-installer/releases/latest…`,
  `ollama.com`, `tailscale.com`), plus, on the same host,
  `…/releases/latest/download/*.apk` (already in `README.md`),
  `…/blob/main/docs/…` (`main` is the default branch of this repo and of
  the assets repo) and `…/issues` (same repository, same host as the
  README's own links).
- **Private data scan** (`grep` for user home-directory paths, workspace
  paths, private IP ranges, loopback addresses and hostnames) over the
  eight files: clean. The two pairing examples were rewritten to
  `<address>:<port>` rather than a private-range pattern. (Pre-existing
  and untouched: the engine README's generic `example-user` home-folder
  path used in a copy example.)

## Where the code contradicts the existing README / shipped texts

1. **The phone's import screen is not translated.** `README.md` (FR,
   *Chemin A*) walks through **« Fichiers du jeu » → « Choisir le dossier
   » / « Choisir une archive »**, but
   `os/android/app/src/main/res/values-fr/strings.xml` only holds the
   `hd_update_*` strings; `import_title`, `import_choose_folder`,
   `import_choose_archive`, `import_copy`, … have no French entry, so a
   French phone shows *"Files of the game" / "Choose the folder"*. The
   guides say so explicitly instead of inventing French labels.
2. **Same for the engine's own UI texts.**
   `files/ce.dat/text/french/game/ce.msg` is a 518-byte stub, so
   in-game labels (*Game files*, *Export saves*, *Replace game*, …) stay
   English on French phones too.
3. **HD check button name.** `README.md` (FR) says
   **« Vérifier l'art HD »**; the actual string (`hd_update_check_menu`)
   is **« Vérifier les graphismes HD »** (EN *"Check for HD art"*).
4. **Start menu path.** `README.md` says *Start menu › **Wasteland** ›
   Install on phone* (and *› Serveur IA (téléphone)*). The installer
   creates the folder **`Wasteland Reborn`** (HD: `Wasteland Reborn HD`)
   with the items `Wasteland`, `Wasteland - Setup`,
   `Wasteland - Install on phone`, `Wasteland - AI server (phone)`,
   `Uninstall` — there is no `Wasteland` subfolder. The guides use the
   real names.
5. **SmartScreen wording.** `README.md` (FR) and `windows/LISEZ-MOI.txt`
   say **« Informations complémentaires »**; French Windows shows **« Plus
   d'informations »**. The guides use the real wording (the shipped
   `.txt` files were not in this task's file list, so they are unchanged).
6. **"Check for HD art" is only reachable once the game is imported.**
   The button is shown only when `HD_EDITION && replacing && !savesMode &&
   !busy`, i.e. after `GameImport.isInstalled()` — on a first launch with
   no game files it is hidden and only the startup offer appears.
7. **The phone AI menu defaults to *Partout / Everywhere*.**
   `phone.py` uses `ask('Choix', '1')`, so pressing Enter at
   `Choice [1] :` installs Tailscale on the PC and the phone. The README
   never mentions this; both guides warn about it explicitly.
8. **HD packs are listed as available but none is published yet.**
   `README.md`'s HD table marks the `world` pack *available*, while
   `wasteland-hd-assets`' `packs.json` is `{"packs": []}` (its last
   commit: "no downloadable packs until a release is published"). The
   setup/app handle it gracefully (`HD packs unavailable for now…` /
   no offer at all), and the assets README now explains what an empty
   list means.

## Open questions

- **Cross-repo links point at `blob/main/docs/…`.** They only resolve once
  `agent/release` (and `agent/linux`) are merged into `main`; the task's
  instruction to link `docs/INSTALL-LINUX.md` "because it will exist after
  merge" implies the same assumption for the Windows guides. Until then the
  four cross-repo links (and the four `INSTALL-LINUX.md` links) 404.
- **Should `values-fr/strings.xml` be completed** (import screen) and
  `french/game/ce.msg` filled in? That is an engine change, out of scope
  for this docs task — noted here for the engine maintainers.
- **Should `windows/README.txt` / `LISEZ-MOI.txt`** (the texts shipped
  inside the installer) get the corrected SmartScreen wording and Start
  menu path? They were not in this task's list, so they were left alone.
- **Linux links** are EN-only (`docs/INSTALL-LINUX.md`); no
  `INSTALL-LINUX.fr.md` link was added since the exact filename was not
  given.
- The **assets worktree's `origin` is a local path**, not
  `github.com/Linutesto/wasteland-hd-assets`; its README (before and after
  my change) links to the GitHub URL. Worth confirming the two are pushed
  in sync, otherwise the raw `packs.json` URL the tools and app read will
  not match this repo's content.

## Rules respected

No push, no `gh` command, no branch switch (each commit was made on the
worktree's own `agent/…` branch), `~/agent-wt/linux` never touched, no GPU
or service started, no phone/adb, nothing written outside the four
worktrees (in particular nothing in the private workspace and nothing
under `~/fallout2`), and no process killed by pattern.
