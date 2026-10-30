# Releasing Wasteland Reborn

How a public release is built, verified and published. Everything is produced
from this repository; **no Fallout 2 file is ever part of a release** — players
supply their own copy at install time.

Commands below are printed (not run) by `tools/release.sh` by default, so read
them first, then re-run with `--publish`.

## 1. What a release contains

Release `v1.2` (next) carries these assets, nothing else:

| Asset | Built by | Notes |
| --- | --- | --- |
| `Wasteland-arm64.apk` | `./bootstrap.sh` | classic edition, Android 64-bit, ≈ 4 MB |
| `Wasteland-HD-arm64.apk` | `./bootstrap.sh --edition hd` | HD edition (`io.github.imbaner.fallout2ce.hd`), own icon, files and saves |
| `WastelandReborn-Setup.exe` | `windows/build.sh` | Windows 10/11 installer, EN/FR, ≈ 830 MB |
| `WastelandRebornHD-Setup.exe` | `EDITION=hd windows/build.sh` | installs beside the classic edition (`%LOCALAPPDATA%\WastelandRebornHD`) |
| `SHA256SUMS.txt` | `tools/release.sh` | checksums of the four files above plus the two texts |
| `README.txt`, `LISEZ-MOI.txt` | `windows/` | the instructions shipped with the installer (EN / FR) |

Both APKs are signed with the same Android debug key the previous releases
used, so an APK install is an update over `v1.1` and keeps saves. The two
installers keep separate settings, saves and registry keys, so they can be
installed together.

## 2. Build

On Linux x86_64, from a clean checkout of the branch being released:

```sh
./bootstrap.sh                  # toolchains, profile, classic APK
./bootstrap.sh --edition hd     # HD APK (same engine checkout)
windows/build.sh                # windows/dist/WastelandReborn-Setup.exe
EDITION=hd windows/build.sh     # windows/dist/WastelandRebornHD-Setup.exe
```

Notes:

- The engine submodule is pinned to `wasteland-reborn-hd`, which contains
  `wasteland-reborn`: one checkout builds both editions. The edition is the
  Gradle flag `-Pfallout2ce.hd`, not a different source tree.
- `bootstrap.sh` pins `src/wasteland-hd-tools` (the HD pack downloader the HD
  installer ships) by commit. It never clones that repo's `art` submodule —
  the HD image source is not needed to build anything here.
- The Android SDK license prompt appears once per `toolchain/android-sdk`.
  Accept it the way `bootstrap.sh` says, i.e. read Google's licenses and
  answer `y` (`yes | ./bootstrap.sh --edition hd` accepts them non-interactively).
- `windows/build.sh` needs `makensis` or Wine, ImageMagick and the toolchain
  `bootstrap.sh` downloaded. `STAGE_ONLY=1` stages the payload and the
  generated uninstall list without running NSIS.

## 3. Publish with `tools/release.sh`

```sh
tools/release.sh                        # DRY RUN (default): prints every command
tools/release.sh --publish              # build, upload, publish
tools/release.sh --publish --skip-build # reuse apk/ and windows/dist/
tools/release.sh --publish --notes-file notes-v1.2.md
tools/release.sh --publish --chunked    # force chunked EXE uploads
```

What it does, in order:

1. Builds both editions (unless `--skip-build`).
2. Copies the four binaries and the two instruction texts into
   `windows/dist/` and regenerates `SHA256SUMS.txt` over all six.
3. `gh release create v1.2 --draft`, then uploads each asset.
4. Publishes it: `gh release edit v1.2 --draft=false --latest`.
5. `gh release view` to list the assets of the draft/final release.

Write the release notes first (a `--notes-file` markdown file: what is new in
v1.2, the four download links with their sizes, and the "no game files
included" line). Without it the script falls back to `--generate-notes`.

### Large or flaky uploads: chunks + the assemble workflow

GitHub refuses assets over 2 GiB, and an 830 MB upload can drop. When an EXE
is over the limit, or when `--chunked` is given, `tools/release.sh`:

- splits it into verified 24 MiB parts under `windows/dist/.chunks-v1.2/`,
- writes `<name>.manifest.json` (`github-release-chunks-v1`: whole size and
  SHA-256, plus a SHA-256 per part; the split is re-usable on a retry),
- uploads the manifest and the parts,
- dispatches `.github/workflows/assemble-wasteland-release.yml` with
  `tag=` and `manifest=`.

The workflow downloads the chunks, reassembles the file, checks its size and
SHA-256 against the manifest, uploads the single EXE, verifies the remote
digest, publishes the draft, and deletes the chunk assets. **In the chunked
path the workflow publishes, not the script** — watch it:

```sh
gh run watch Linutesto/wasteland-reborn-installer
gh release view v1.2 -R Linutesto/wasteland-reborn-installer
```

`--branch` (default: the current branch) selects the branch the workflow runs
on; the workflow file must exist on that branch.

### Verify before announcing

- `python3 -m unittest discover -s windows/tests -v` → 7 tests, OK.
- `bash -n bootstrap.sh windows/build.sh tools/*.sh windows/tests/*.sh`.
- `sha256sum -c SHA256SUMS.txt` inside `windows/dist/`.
- `gh release view v1.2` shows all seven assets and `isDraft: false`.
- On a phone: install the APK from the release link over an existing install
  (saves must survive), then fresh-install on a second device and complete the
  game-files import.

## 4. `packs.json` — the HD art manifest (assets repo)

The HD app and the HD installer both read
`https://raw.githubusercontent.com/Linutesto/wasteland-hd-assets/main/packs.json`
(`HdPacks.MANIFEST_URL` in the engine, `ASSETS` in `wasteland_hd`). The
proposed next version is `tmp-release/packs.proposed.json`.

### Plan: one `world` pack now, `critters-NN` later

- **`world`** — everything that is finished and joins as one piece: tiles,
  walls, scenery, items, misc, heads, interface. One download, one ZIP.
- **`critters-NN`** — critters arrive as separate packs as production
  finishes them (`critters-01`, `critters-02`, …), so a phone downloads only
  what exists, then tops up later instead of re-downloading a growing ZIP.

Each pack is a **separate entry with a permanent `name`**. The phone records
installed packs in `data/hd/.installed-packs.json` (name → SHA-256) and the PC
installer in `data/hd/.<name>.sha256`; a changed `sha256` under the same name
is offered as an update, while a new name is simply one more download. Never
rename a published pack, and never reuse a name for different content.

### Fields, checked against both parsers

| Field | Android updater (`HdPacks.parseManifest`) | PC installer (`wasteland_hd.__main__.cmd_install`) |
| --- | --- | --- |
| `name` | `[A-Za-z0-9][A-Za-z0-9_.-]{0,63}`, not `.`/`..`, no duplicates | identical regex |
| `file` | `[A-Za-z0-9][A-Za-z0-9_.-]*\.zip` | identical regex |
| `url` | `https://`, `http://` or `file://` | any URL `urllib` can open |
| `size` | JSON **integer**, `0 < size < 16 GiB` | integer, same bounds |
| `sha256` | 64 hex digits (case-insensitive) | 64 hex digits |
| `covers` | string, **≤ 300 characters** (shown in the offer) | not read |

Top level must be an object with a `packs` array; unknown fields are ignored.
The manifest itself is limited to 2 MB by the app.

ZIP rules enforced by the app before anything is published into the profile:

- entries only under `hd/` (e.g. `hd/art/tiles/...`), no `..`, no backslash,
  no absolute paths, no duplicates, no symlinks/special files;
- **standard ZIP only — ZIP64 is rejected** by the app's archive inspection;
- every entry CRC-checked; the whole download is SHA-256 checked first;
- the app installs into the *active profile's* `data/hd/` and never deletes
  art a manifest does not mention.

### Replacing the placeholders

`"<SIZE>"` and `"<SHA256>"` are placeholders: both parsers reject them, so
they must be replaced before the manifest reaches `main`:

```sh
sha256sum WastelandHD-World.zip          # -> "sha256"
stat -c %s WastelandHD-World.zip          # -> "size" as a bare JSON number
```

Then, **in this order** (the manifest must never point at a file that is not
there — the updater offers every entry immediately):

1. Build and verify the ZIP (`wasteland_hd pack`; entries under `hd/`,
   standard ZIP, no ZIP64).
2. Upload it to the assets repo as a release asset of tag `packs-v1`
   (`gh release create packs-v1 --repo Linutesto/wasteland-hd-assets` …).
3. Put its real `size` and `sha256` in `packs.json`; keep `url` pointing at
   that asset.
4. Commit `packs.json` to `main` of `Linutesto/wasteland-hd-assets` — that raw
   URL is what every installed app reads on launch.
5. Test on a phone: the offer appears with the right name, MB and `covers`;
   **Later** starts the game; a kill mid-download resumes (HTTP 206); a second
   launch does not re-offer an installed pack.

Publish `critters-NN` entries only once their ZIP is live (step 2): an entry
whose URL 404s makes the app offer a download that always fails.

## 5. Rules

- Releases are created **as drafts** and published only after the verification
  above; the chunk workflow publishes automatically once the digest matches.
- Never rewrite a published asset: re-upload a new tag instead (the workflow
  refuses to replace an EXE whose digest differs).
- No game files, no personal paths, no tokens in any asset: `windows/build.sh`
  already fails the build if the staged profile contains one.
