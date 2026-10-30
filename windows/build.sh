#!/usr/bin/env bash
# Builds windows/dist/WastelandReborn-Setup.exe (or WastelandRebornHD-Setup.exe
# with EDITION=hd): Windows engine (llvm-mingw), RPU profile (no Fallout game
# files, no saves, no tokens), brain, embeddable Python, Android APK, then packs
# it with NSIS (native makensis, or under Wine).
#
# Everything comes from this repository: the engine submodule (src/), brain/,
# windows/, and what ./bootstrap.sh makes once (toolchain/, build/profile, the
# APKs in apk/). PROFILE=<dir> or APK=<file> override the last two.
#
#   EDITION=normal windows/build.sh     (default) WastelandReborn-Setup.exe
#   EDITION=hd windows/build.sh          WastelandRebornHD-Setup.exe
#   STAGE_ONLY=1 ...                     stage payload + uninstall list, no NSIS
set -euo pipefail
W=$(cd "$(dirname "$0")" && pwd)
F=$(dirname "$W")
T=$F/toolchain
ENGINE=$F/src/imbaner_fallout2-ce-mobile
PROFILE=${PROFILE:-$F/build/profile}
EDITION=${EDITION:-normal}
case "$EDITION" in
    normal) APK=${APK:-$F/apk/Wasteland-arm64.apk} ;;
    hd)     APK=${APK:-$F/apk/Wasteland-HD-arm64.apk} ;;
    *) echo "invalid EDITION=$EDITION (normal or hd)" >&2; exit 2 ;;
esac
for need in "$ENGINE/CMakeLists.txt" "$PROFILE/fallout2.cfg" "$APK" "$T/mingw-w64.cmake" "$T/win/python-embed.zip"; do
    [ -e "$need" ] || { echo "missing $need: run ./bootstrap.sh first" >&2; exit 1; }
done
case "$EDITION" in
    normal) STAGE=$W/build/stage; OUT=$W/dist/WastelandReborn-Setup.exe ;;
    hd)     STAGE=$W/build/stage-hd; OUT=$W/dist/WastelandRebornHD-Setup.exe ;;
esac
# The HD installer ships the pack downloader (wasteland_hd) next to setup.py.
HD_TOOLS=$F/src/wasteland-hd-tools/wasteland_hd
if [ "$EDITION" = hd ] && [ ! -f "$HD_TOOLS/__main__.py" ]; then
    echo "missing $HD_TOOLS: run ./bootstrap.sh first (it clones wasteland-hd-tools)" >&2; exit 1
fi

echo "== engine (Windows x64)"
[ -d "$ENGINE/build-win64" ] || cmake -S "$ENGINE" -B "$ENGINE/build-win64" -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE="$T/mingw-w64.cmake" -DCMAKE_BUILD_TYPE=Release
cmake --build "$ENGINE/build-win64" --target fallout2-ce

echo "== ce.dat tool (host)"
DATTOOL=$ENGINE/build/ce-dat-tool
if [ ! -x "$DATTOOL" ]; then
    DATTOOL=$ENGINE/build-host/ce-dat-tool
    [ -d "$ENGINE/build-host" ] || cmake -S "$ENGINE" -B "$ENGINE/build-host" -DCMAKE_BUILD_TYPE=Release
    cmake --build "$ENGINE/build-host" --target ce-dat-tool
fi

echo "== stage"
rm -rf "$STAGE"; mkdir -p "$STAGE"/{game,brain/personas,python,setup,phone} "$W/dist"
# Profile: regular files only. Symlinks are the base game (master/critter.dat,
# music), which comes from the player's own copy at setup time. Original
# executables/DLLs are not needed by the CE engine. Files the engine writes
# while playing (map states, protos, worldmap, data detection) are left out.
# HD art is never staged: the player downloads packs into data/hd at setup time.
rsync -a --no-links \
    --exclude='/master.dat' --exclude='/critter.dat' --exclude='/patch000.dat' --exclude='/ce.dat' \
    --exclude='/backup/' --exclude='/data/savegame/' --exclude='/data/SAVEGAME/' \
    --exclude='/data/MAPS/' --exclude='/data/maps/' --exclude='/data/proto/' --exclude='/data/worldmap.dat' \
    --exclude='/data/hd/' --exclude='/data/HD/' \
    --exclude='/ce-game-*.txt' --exclude='*.log' --exclude='*.exe' --exclude='*.dll' \
    --exclude='/ce-saves.txt' --exclude='/profile.json' \
    "$PROFILE"/ "$STAGE/game/"
# The engine's own data (mobile UI texts, font, art), from the engine source.
"$DATTOOL" create "$ENGINE/files/ce.dat" "$STAGE/game/ce.dat" >/dev/null
mkdir -p "$STAGE/game/data/savegame" "$STAGE/game/data/sound/music"
cp "$ENGINE/build-win64/fallout2-ce.exe" "$STAGE/game/"
# No secrets or personal paths in the shipped config.
python3 - "$STAGE/game/fallout2.cfg" <<'EOF'
import re, sys
p = sys.argv[1]; s = open(p, encoding='latin-1').read()
s = re.sub(r'(?m)^token=.*$', 'token=', s)
s = re.sub(r'(?m)^server=.*$', 'server=http://127.0.0.1:8822', s)
s = re.sub(r'(?m)^enabled=1$', 'enabled=0', s)
s = re.sub(r'(?m)^console_output_path=.*$', 'console_output_path=', s)
s = re.sub(r'(?m)^mode=log$', 'mode=', s)
open(p, 'w', encoding='latin-1').write(s)
EOF
if grep -rIl "\.ts\.net\|100\.[0-9]*\.[0-9]*\.[0-9]*:\|/home/" "$STAGE/game" --include='*.cfg' --include='*.ini' --include='*.txt'; then
    echo "personal data left in the staged profile" >&2; exit 1
fi

cp "$F"/brain/*.py "$STAGE/brain/"
cp "$F"/brain/personas/*.json "$STAGE/brain/personas/"
cp "$W"/setup/*.py "$STAGE/setup/"
cp "$APK" "$STAGE/phone/wasteland.apk"
ICON=$ENGINE/os/android/app/src/wasteland/res/mipmap-xxxhdpi/ic_launcher.png
if [ "$EDITION" = hd ]; then
    ICON=$ENGINE/os/android/app/src/wasteland-hd/res/mipmap-xxxhdpi/ic_launcher.png
    rsync -a --exclude='__pycache__' --exclude='*.pyc' \
        "$HD_TOOLS/" "$STAGE/setup/wasteland_hd/"
    # The staged scripts read this to know which app they install and configure.
    python3 - "$STAGE/setup/edition.json" <<'PY'
import json, sys
with open(sys.argv[1], 'w', encoding='utf-8') as f:
    json.dump({'edition': 'hd', 'package': 'io.github.imbaner.fallout2ce.hd',
               'app_name': 'Wasteland HD', 'apk': 'phone/wasteland.apk'}, f)
PY
fi
magick "$ICON" \
    -define icon:auto-resize=256,64,48,32,16 "$STAGE/setup/wasteland.ico"

unzip -q -o "$T/win/python-embed.zip" -d "$STAGE/python"
# The ._pth file makes Python ignore the script's folder: list ours explicitly.
PTH=$(ls "$STAGE"/python/python3*._pth)
printf '../setup\n../brain\n' >> "$PTH"

# Uninstall only files shipped by this edition; leave saves and userdata
# intact. Generate the list from the actual stage, including nested RPU files.
UNINSTALL_MANIFEST=$W/build/uninstall-$EDITION.nsh
python3 - "$STAGE" "$UNINSTALL_MANIFEST" <<'PY'
from pathlib import Path
import sys

stage, target = map(Path, sys.argv[1:])
def nsis_path(path):
    return str(path.relative_to(stage)).replace('/', '\\').replace('$', '$$')

files = sorted((p for p in stage.rglob('*') if p.is_file()), reverse=True)
dirs = sorted((p for p in stage.rglob('*') if p.is_dir()),
              key=lambda p: (-len(p.relative_to(stage).parts), str(p)))
with target.open('w', encoding='utf-8') as out:
    out.write('; Generated from the staged installer payload.\n')
    for p in files:
        out.write(f'Delete "$INSTDIR\\{nsis_path(p)}"\n')
    for p in dirs:
        out.write(f'RMDir "$INSTDIR\\{nsis_path(p)}"\n')
PY

echo "== pack ($(du -sh "$STAGE" | cut -f1), APK $(basename "$APK"))"
if [ "${STAGE_ONLY:-0}" = 1 ]; then
    echo "STAGE_ONLY=1: stage and uninstall manifest ready; NSIS packaging skipped"
    exit 0
fi
cd "$W"
if command -v makensis >/dev/null; then
    if [ "$EDITION" = hd ]; then
        makensis -V2 "-DSTAGE=$STAGE" "-DOUTFILE=$OUT" "-DUNINSTALL_MANIFEST=$UNINSTALL_MANIFEST" -DHD_EDITION installer.nsi
    else
        makensis -V2 "-DSTAGE=$STAGE" "-DOUTFILE=$OUT" "-DUNINSTALL_MANIFEST=$UNINSTALL_MANIFEST" installer.nsi
    fi
else
    # Wine's default ~/.wine can contain a user's unrelated apps/settings.
    # Reserve a project-local prefix for NSIS packaging unless the caller
    # supplied an explicit, non-default Wine prefix.
    if [ -z "${WINEPREFIX:-}" ] || [ "$WINEPREFIX" = "$HOME/.wine" ]; then
        export WINEPREFIX="$W/build/wine-nsis"
    fi
    mkdir -p "$WINEPREFIX"
    NSIS_ARGS=()
    if [ "$EDITION" = hd ]; then NSIS_ARGS+=(-DHD_EDITION); fi
    WINEDEBUG=-all wine "$T/win/nsis-3.11/makensis.exe" -V2 \
        "-DSTAGE=$(winepath -w "$STAGE")" "-DOUTFILE=$(winepath -w "$OUT")" \
        "-DUNINSTALL_MANIFEST=$(winepath -w "$UNINSTALL_MANIFEST")" "${NSIS_ARGS[@]}" installer.nsi
fi
ls -la "$OUT"; (cd "$W/dist" && sha256sum "$(basename "$OUT")" | tee SHA256SUMS.txt)
