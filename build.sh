#!/usr/bin/env bash
# Builds windows/dist/WastelandReborn-Setup.exe: Windows engine (llvm-mingw),
# RPU profile (no Fallout game files, no saves, no tokens), brain, embeddable
# Python, Android APK, then packs it with NSIS under Wine.
set -euo pipefail
W=$(cd "$(dirname "$0")" && pwd)
F=$(dirname "$W")
T=$F/toolchain
ENGINE=$F/src/imbaner_fallout2-ce-mobile
PROFILE=$F/profiles/ai-rpu
APK=${APK:-$F/apk/wasteland-reborn-20261026-arm64.apk}
STAGE=$W/build/stage
OUT=$W/dist/WastelandReborn-Setup.exe

echo "== engine (Windows x64)"
[ -d "$ENGINE/build-win64" ] || cmake -S "$ENGINE" -B "$ENGINE/build-win64" -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE="$T/mingw-w64.cmake" -DCMAKE_BUILD_TYPE=Release
ninja -C "$ENGINE/build-win64" fallout2-ce

echo "== stage"
rm -rf "$STAGE"; mkdir -p "$STAGE"/{game,brain/personas,python,setup,phone} "$W/dist"
# Profile: regular files only. Symlinks are the base game (master/critter.dat,
# music), which comes from the player's own copy at setup time. Original
# executables/DLLs are not needed by the CE engine.
rsync -a --no-links \
    --exclude='/master.dat' --exclude='/critter.dat' --exclude='/backup/' \
    --exclude='/data/savegame/' --exclude='/data/SAVEGAME/' --exclude='*.log' \
    --exclude='*.exe' --exclude='*.dll' --exclude='/ce-saves.txt' --exclude='/profile.json' \
    "$PROFILE"/ "$STAGE/game/"
cp -L "$PROFILE/ce.dat" "$STAGE/game/ce.dat"
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

echo "== pack ($(du -sh "$STAGE" | cut -f1))"
cd "$W"
WINEDEBUG=-all wine "$T/win/nsis-3.11/makensis.exe" -V2 \
    "-DSTAGE=$(winepath -w "$STAGE")" "-DOUTFILE=$(winepath -w "$OUT")" installer.nsi
ls -la "$OUT"; sha256sum "$OUT" | tee "$OUT.sha256"
