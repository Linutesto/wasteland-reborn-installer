#!/usr/bin/env bash
# Builds windows/dist/WastelandReborn-Setup.exe: Windows engine (llvm-mingw),
# RPU profile (no Fallout game files, no saves, no tokens), brain, embeddable
# Python, Android APK, then packs it with NSIS (native makensis, or under Wine).
# Run ./bootstrap.sh once first (toolchains, profile, APK).
set -euo pipefail
W=$(cd "$(dirname "$0")" && pwd)
F=$(dirname "$W")
T=$F/toolchain
ENGINE=$F/src/imbaner_fallout2-ce-mobile
# The profile mkprofile.py builds (build/profile), else the maintainer's.
PROFILE=${PROFILE:-$([ -d "$F/build/profile" ] && echo "$F/build/profile" || echo "$F/profiles/ai-rpu")}
# The newest released APK, else the one tools/android-build.sh made.
APK=${APK:-$(ls -t "$F"/apk/wasteland-reborn-*-arm64.apk 2>/dev/null | head -1)}
APK=${APK:-$ENGINE/os/android/app/build/outputs/apk/debug/app-debug.apk}
STAGE=$W/build/stage
OUT=$W/dist/WastelandReborn-Setup.exe

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
rsync -a --no-links \
    --exclude='/master.dat' --exclude='/critter.dat' --exclude='/patch000.dat' --exclude='/ce.dat' \
    --exclude='/backup/' --exclude='/data/savegame/' --exclude='/data/SAVEGAME/' \
    --exclude='/data/MAPS/' --exclude='/data/maps/' --exclude='/data/proto/' --exclude='/data/worldmap.dat' \
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
magick "$ENGINE/os/android/app/src/wasteland/res/mipmap-xxxhdpi/ic_launcher.png" \
    -define icon:auto-resize=256,64,48,32,16 "$STAGE/setup/wasteland.ico"

unzip -q -o "$T/win/python-embed.zip" -d "$STAGE/python"
# The ._pth file makes Python ignore the script's folder: list ours explicitly.
PTH=$(ls "$STAGE"/python/python3*._pth)
printf '../setup\n../brain\n' >> "$PTH"

echo "== pack ($(du -sh "$STAGE" | cut -f1), APK $(basename "$APK"))"
cd "$W"
if command -v makensis >/dev/null; then
    makensis -V2 "-DSTAGE=$STAGE" "-DOUTFILE=$OUT" installer.nsi
else
    WINEDEBUG=-all wine "$T/win/nsis-3.11/makensis.exe" -V2 \
        "-DSTAGE=$(winepath -w "$STAGE")" "-DOUTFILE=$(winepath -w "$OUT")" installer.nsi
fi
ls -la "$OUT"; (cd "$W/dist" && sha256sum "$(basename "$OUT")" | tee SHA256SUMS.txt)
