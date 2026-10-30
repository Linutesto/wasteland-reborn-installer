# RELEASE-REPORT — task R: a public, working install of Wasteland Reborn HD

Branch: `agent/release`. Nothing was pushed, no GitHub release or workflow was
created or edited from here (only read-only `gh release list/view`), no GPU,
no phone/adb, nothing written under `/ai` or `~/fallout2` (read-only source of
the port).

## 1. What changed

### Editions (the port of `~/fallout2/windows/`, private paths removed)

| File | Change |
| --- | --- |
| `.gitmodules` + submodule pointer | engine pinned to **`wasteland-reborn-hd`** (`a0a43e7d`), which contains `wasteland-reborn`/`87f94eef` (13 commits ahead). One checkout builds both editions. |
| `bootstrap.sh` | `--edition normal\|hd` (default normal) picks the Gradle task and names the output; clones `src/wasteland-hd-tools` pinned to `7559487f…` (never its `art` submodule); outputs `apk/Wasteland-arm64.apk` or `apk/Wasteland-HD-arm64.apk`. |
| `windows/build.sh` | `EDITION=normal\|hd`: per-edition APK default, stage (`build/stage`, `build/stage-hd`), output EXE, HD icon, `setup/edition.json`, the `wasteland_hd` payload, generated `uninstall-$EDITION.nsh`, `STAGE_ONLY=1`, project-local Wine prefix. Private `$F/profiles/ai-rpu` and `$F/../wasteland-hd-tools` references replaced by repo-local ones. |
| `windows/installer.nsi` | `PRODUCT`/`PRODUCT_KEY` per edition (`Wasteland Reborn HD` / `WastelandRebornHD`), HD welcome/finish texts EN+FR, `/DUNINSTALL_MANIFEST`, NSIS `/S` → `setup.py --unattended`, uninstall driven by the generated manifest (saves and `userdata` kept). |
| `windows/setup/setup.py` | `EDITION_FILE` (staged `edition.json`), `setup_hd_art()` (offered only in HD, only after `master.dat`+`critter.dat` verified, failure logged and never fatal), `unattended_main()` writing `userdata/setup-install.log`. |
| `windows/setup/phone.py` | package/app name/APK from `edition.json` (`io.github.imbaner.fallout2ce.hd`, "Wasteland HD"), HD profile values (`hd_art=1`, `hd_cache_mb=256`, `dark_boost=2`), pushes `mods`, `appearance`, `translations`, never `savegame`. |
| `windows/README.txt`, `windows/LISEZ-MOI.txt` | HD edition + unattended `/S` section (EN and FR). |
| `windows/tests/` (new) | `test_setup.py`, `test_phone.py` (7 offline unittests) and `test_wine_install.sh` (both editions end-to-end under Wine; reports SKIP when the player's own files are absent from `gamedata/`, which is never in this repo). |
| `.gitignore` | `/src/wasteland-hd-tools/`, `/tmp-release/`, `/tests/` (Wine prefix), `/gamedata/`. |

### Release tooling and docs

- **`tools/release.sh`** — prints every command and runs nothing by default
  (`--dry-run`), executes them with `--publish`. Options: `--tag`, `--skip-build`,
  `--chunked`, `--notes-file`, `--branch`. It builds both editions, stages the
  seven release files into `windows/dist/`, regenerates `SHA256SUMS.txt`, creates
  a **draft** `gh release`, uploads the assets, publishes it, then verifies.
  An EXE over GitHub's 2 GiB per-asset limit (or any EXE with `--chunked`) is
  split into verified 24 MiB parts + a `github-release-chunks-v1` manifest and
  handed to the existing workflow, which assembles, verifies the SHA-256,
  uploads the single EXE and publishes the release.
- **`.github/workflows/assemble-wasteland-release.yml`** — the hardcoded
  `manifest['name'] == 'WastelandReborn-Setup.exe'` assertion became a general
  check (plain `.exe`/`.apk` file name, and it must equal the dispatched
  manifest asset), so both installers can take the chunked path. Everything
  else (per-part SHA-256, size, remote digest, draft publish, chunk cleanup)
  is unchanged.
- **`RELEASING.md`** — the v1.2 asset layout, build commands, `release.sh`
  usage, the chunk/workflow path, verification checklist, and the `packs.json`
  plan: field-by-field table checked against **both** parsers
  (`HdPacks.parseManifest` in the engine, `wasteland_hd.__main__.cmd_install`),
  ZIP rules (entries under `hd/`, standard ZIP, no ZIP64), placeholder
  replacement, and the publish order (upload ZIP first, manifest second) with
  the reason: the app offers every entry of a manifest immediately.
- **`tmp-release/packs.proposed.json`** (gitignored, as specified) — one
  `world` pack (tiles, walls, scenery, items, misc, heads, interface) and the
  `critters-01` template for the incremental critter packs, with
  `"<SIZE>"`/`"<SHA256>"` placeholders.
- **`README.md`** — rewritten phone-first, EN + FR: download table (4 assets +
  checksums), the rights statement up front, then three numbered install paths
  a non-developer can follow — (A) phone only, including where `master.dat`
  and `critter.dat` live for Steam / GOG / Epic and how to get them onto the
  phone (cable, cloud, messenger; folder or `.zip`/`.7z`/`.rar`), the in-app
  import screen and the HD app's art offer; (B) PC + phone with the Windows
  installer; (C) build from source (`--edition hd` included) — then the HD art
  table (world done, critters arriving as separate `critters-NN` packs), the
  AI notes and credits.

## 2. Fresh-clone build proof

```sh
git clone --recursive file:///home/yan/agent-wt/installer ~/agent-wt/proof-clone
yes | ./bootstrap.sh --edition hd     # `yes` accepts Google's SDK licenses, the way bootstrap.sh documents
EDITION=hd windows/build.sh
./bootstrap.sh
windows/build.sh
```

Log: `~/agent-wt/proof.log` (scratch clone left at `~/agent-wt/proof-clone`,
4.9 GB — delete when finished: `rm -rf ~/agent-wt/proof-clone ~/agent-wt/proof.log`).
Wall clock 12:39:40 → 13:10:12 (~31 min): clone, 4.0 GB toolchain, RPU profile,
two Gradle APK builds, two Windows engine builds, two NSIS packages under Wine.

| Step | Exit | Artifact | Size (bytes) | SHA-256 |
| --- | --- | --- | --- | --- |
| `./bootstrap.sh --edition hd` | 0 | `apk/Wasteland-HD-arm64.apk` | 3,657,535 | `53ce3a67d8bb54dbc8ec18b96a5c53e85845fbbbae77971a1810eff474216c9b` |
| `EDITION=hd windows/build.sh` | 0 | `windows/dist/WastelandRebornHD-Setup.exe` | 828,292,575 | `3de459c82a021f5a608d13cd79e6ca195f4f44a9ab44f66f8c097ea75c3d30a9` |
| `./bootstrap.sh` | 0 | `apk/Wasteland-arm64.apk` | 5,158,862 | `2e335f484c4e227cbb412e978e796326cf7e7bc1714b2cc13b73303642922b65` |
| `windows/build.sh` | 0 | `windows/dist/WastelandReborn-Setup.exe` | 829,700,972 | `01195dc9f17bd908697c25426fd46a283c7845a3b1c73eae90aaa6e86af53087` |

Identity checks in the same clone:

- `aapt dump badging` — `Wasteland-arm64.apk`: package
  `io.github.imbaner.fallout2ce.debug`, label *Wasteland*;
  `Wasteland-HD-arm64.apk`: package `io.github.imbaner.fallout2ce.hd`, label
  *Wasteland HD*. Both `native-code: arm64-v8a`, `versionName 1.3.0-mobile.6`.
- `7z t` on **both** setup EXEs: OK (NSIS PE32).
- Staged payloads: classic 132 files (no `edition.json`), HD 143 files
  (`+setup/edition.json` with the `.hd` package, `+setup/wasteland_hd/` 10
  modules, HD APK in `phone/`, HD icon); `uninstall-normal.nsh` 149 lines,
  `uninstall-hd.nsh` 161 lines.
- Gradle ran `lintVital*` for `assemblePhone` and passed — no lint exclusions
  needed.

## 3. Tests

```
$ python3 -m unittest discover -s windows/tests -v
test_classic_profile_does_not_force_hd ... ok
test_hd_profile_contains_all_rpu_directories_and_skips_saves ... ok
test_hd_art_rejects_missing_base_game ... ok
test_hd_download_failure_is_logged_and_game_remains_playable ... ok
test_missing_hd_art_module_keeps_installer_running ... ok
test_no_fallout_does_not_download_or_create_token ... ok
test_normal_never_attempts_hd_art ... ok

Ran 7 tests in 0.007s

OK
```

- `bash -n` on every shell script in the repo: `bootstrap.sh`,
  `windows/build.sh`, `tools/android-build.sh`, `tools/release.sh`,
  `windows/tests/test_wine_install.sh` — all parse.
- `python3 -m compileall -q windows/setup windows/tests` — OK.
- Workflow YAML parses (`yaml.safe_load`); `tmp-release/packs.proposed.json`
  parses as JSON.
- **Chunked path tested offline**: the chunker extracted verbatim from
  `tools/release.sh` split a 62 MB fixture into 3 verified parts, was
  idempotent on a second run, then a reassembly applying the workflow's own
  assertions (name/manifest match, per-part size + SHA-256, total size, whole
  SHA-256) reproduced the source byte-for-byte. A non-`.exe`/`.apk` name is
  correctly rejected by the generalized check.
- `tools/release.sh` dry run (the default) prints the five steps — build,
  stage, draft release + uploads, publish, verify — and executes nothing.
- `windows/tests/test_wine_install.sh` — **not run**: it needs real Fallout 2
  files in `gamedata/` (never shipped) plus a working Wine/Xvfb session; it
  prints `SKIP:` and exits 0 without them. Run it on a machine with the game.
- Private-path scan of the whole tree (tracked files): no `/home/…`,
  `~/fallout2`, `../wasteland-hd-tools`, tailnet IPs or tokens. Two legitimate
  matches remain and are not private data: `100.64.0.0/10` (Tailscale's shared
  CGNAT range, used for `adb reverse`) and the `grep` guard for `/home/` that
  `windows/build.sh` runs on the staged payload. The engine submodule also
  scans clean.

## 4. Decisions worth knowing

1. **Submodule on the HD branch.** `wasteland-reborn-hd` contains
   `wasteland-reborn`, so a single pinned checkout serves both editions; the
   classic build is simply the flag-less build (resource folder
   `src/wasteland/res` instead of `src/wasteland-hd/res`). This avoids two
   submodules and keeps `git clone --recursive` to one checkout.
2. **HD APK is `assemblePhone -Pfallout2ce.hd`.** Only the `phone` build type
   applies the `.hd` application-id suffix; the `debug` build type is hard-wired
   to `.debug`, so `assembleDebug -Pfallout2ce.hd` would produce an HD app
   under the classic package name. The classic APK stays exactly as before
   (`assembleDebug` → `.debug`).
3. **`wasteland-hd-tools` is cloned by `bootstrap.sh`, not a submodule.** As a
   submodule, `git clone --recursive` would also fetch its `art` submodule —
   209 MB today and growing with every HD pack — which a stranger does not
   need to build. The clone is pinned by commit like the toolchains and its
   `art` directory is never touched. Making it a submodule is the alternative
   if the tools repo ever drops `art`.
4. **`release.sh` is dry-run by default** so the publishing steps can be read
   and reviewed before anything is created; the chunk path reuses the existing
   workflow rather than a new one.

## 5. Open questions

1. **HD download links are dead until v1.2 exists.** The README points at
   `releases/latest/download/Wasteland-HD-arm64.apk` and
   `…/WastelandRebornHD-Setup.exe`; v1.1 has neither, so both 404 until v1.2
   is published (the classic links still work).
2. **Classic APK size changed**: 5,158,862 bytes now vs 8,180,794 bytes in the
   v1.1 asset. Same package, label and versionName, and the same machine's
   debug keystore signs it, so it should still install as an update — but
   confirm on a phone before announcing, and confirm which build v1.1 actually
   shipped (`assembleDebug` vs `assemblePhone`).
3. **Release notes for v1.2** must be written first
   (`tools/release.sh --publish --notes-file …`); without it the script falls
   back to `--generate-notes`.
4. **`packs.json` is a proposal.** `tmp-release/packs.proposed.json` has
   `<SIZE>`/`<SHA256>` placeholders (both parsers reject them) and the
   `critters-01` entry must not reach `main` of the assets repo before its ZIP
   is uploaded — see `RELEASING.md` §4 for the order.
5. **Chunked dispatch needs the workflow on the dispatched branch.**
   `agent/release` is not pushed (as instructed); if v1.2 is released from a
   merged `main`, `release.sh`'s `--branch` default (current branch) is right.
6. **Wine end-to-end test** (both installers installed, launched, uninstalled)
   still needs a machine with `gamedata/` — the offline suite covers the setup
   logic, not the runtime install.
7. **Should the classic APK move to `assemblePhone` too?** It would match the
   HD build (release-optimized native code) but changes what has been shipped
   so far; left as-is deliberately.
