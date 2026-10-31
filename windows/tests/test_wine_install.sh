#!/usr/bin/env bash
# End-to-end test of both installers, run on a machine that permits wineserver
# Unix sockets. Only the dedicated tests/wine-hd prefix and its private XDG
# dirs are used. It installs the player's own Fallout 2, which is never in this
# repository: put your copies in gamedata/ (gitignored) or the test skips.
set -euo pipefail
set -o errtrace  # the ERR trap must also cover check_edition
# A failing bare 'test' must not stop the run silently: show what failed.
trap 'rc=$?; echo "FAILED (exit $rc): $BASH_COMMAND" >&2' ERR
F=$(cd "$(dirname "$0")/../.." && pwd)
TEST_ROOT="$F/tests/wine-hd"

for need in MASTER.DAT CRITTER.DAT; do
  [ -f "$F/gamedata/$need" ] || {
    echo "SKIP: your own Fallout 2 goes in gamedata/ ($need missing); the offline tests are windows/tests/test_*.py" >&2
    exit 0
  }
done
export WINEPREFIX="$TEST_ROOT"
REAL_HOME=$HOME
REAL_DESKTOP="$REAL_HOME/Desktop"
REAL_WINE_APPS="$REAL_HOME/.local/share/applications/wine"
BEFORE="$TEST_ROOT/real-shortcuts-before.json"
mkdir -p "$TEST_ROOT"
python3 - "$REAL_DESKTOP" "$REAL_WINE_APPS" "$BEFORE" <<'PY'
import json,sys
from pathlib import Path
locations=map(Path,sys.argv[1:3])
Path(sys.argv[3]).write_text(json.dumps(sorted(str(p) for d in locations if d.exists() for p in d.rglob('*') if p.is_file())))
PY

XVFB_PID=''
finish() {
  if [ -n "$XVFB_PID" ]; then
    kill "$XVFB_PID" 2>/dev/null || true
    wait "$XVFB_PID" 2>/dev/null || true
  fi
  # Stop the prefix's wineserver so no Wine process outlives the test.
  WINEPREFIX="$TEST_ROOT" wineserver -k 2>/dev/null || true
  WINEPREFIX="$TEST_ROOT" wineserver -w 2>/dev/null || true
  # Clean up only NEW entries linked to this test; preserve pre-existing items.
  python3 - "$REAL_DESKTOP" "$REAL_WINE_APPS" "$BEFORE" <<'PY'
import json,sys
from pathlib import Path
roots=[Path(v) for v in sys.argv[1:3]]
before=set(json.loads(Path(sys.argv[3]).read_text()))
for path in (p for root in roots if root.exists() for p in root.rglob('*') if p.is_file()):
    if str(path) in before: continue
    if 'wasteland' in path.name.lower() or (path.suffix=='.desktop' and b'Wasteland Reborn' in path.read_bytes()):
        print(f'Removing leaked test shortcut: {path}')
        path.unlink()
    else:
        print(f'Unexpected new real-home item (kept): {path}')
PY
}
trap finish EXIT

export HOME="$TEST_ROOT/host-home"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_DESKTOP_DIR="$HOME/Desktop"
export WINEDLLOVERRIDES='winemenubuilder.exe=d'
export WINEDEBUG=-all
export WINEARCH=win64
mkdir -p "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_CACHE_HOME" "$HOME/Desktop"
printf 'XDG_DESKTOP_DIR="%s"\n' "$HOME/Desktop" > "$XDG_CONFIG_HOME/user-dirs.dirs"

# Xvfb must be listening before Wine starts: an install launched on a
# half-started display is the historical source of flaky failures.
Xvfb :91 -screen 0 1280x720x24 -nolisten tcp > "$TEST_ROOT/xvfb.log" 2>&1 &
XVFB_PID=$!
export DISPLAY=:91
for _ in $(seq 1 50); do
  [ -S /tmp/.X11-unix/X91 ] && break
  sleep 0.2
done
[ -S /tmp/.X11-unix/X91 ] || { echo 'Xvfb :91 did not start' >&2; exit 1; }

wineboot --init
SOURCE="$WINEPREFIX/drive_c/GOG Games/Fallout 2"
mkdir -p "$SOURCE/data/sound/music"
cp --reflink=auto "$F/gamedata/MASTER.DAT" "$SOURCE/master.dat"
cp --reflink=auto "$F/gamedata/CRITTER.DAT" "$SOURCE/critter.dat"
cp -a "$F/gamedata/DATA/SOUND/MUSIC/." "$SOURCE/data/sound/music/"
wine reg add 'HKLM\SOFTWARE\GOG.com\Games\1440151285' /v path /t REG_SZ /d 'C:\GOG Games\Fallout 2' /f >/dev/null

LOCALAPPDATA_WIN=$(wine cmd /c echo %LOCALAPPDATA% | tr -d '\r' | tail -1)
LOCALAPPDATA_LINUX=$(winepath -u "$LOCALAPPDATA_WIN")
test -n "$LOCALAPPDATA_LINUX"
case "$LOCALAPPDATA_LINUX" in
  "$WINEPREFIX"/*) ;;
  *) echo "Unsafe LOCALAPPDATA outside prefix: $LOCALAPPDATA_LINUX" >&2; exit 1 ;;
esac

check_edition() {
  local key=$1 product=$2 exe=$3
  local inst="$LOCALAPPDATA_LINUX/$key"
  echo "Installing $product in $WINEPREFIX"
  timeout 420s wine "$exe" /S > "$TEST_ROOT/install-$key.log" 2>&1
  for file in game/fallout2-ce.exe game/fallout2.cfg game/ce.dat game/master.dat game/critter.dat \
              brain/server.py python/python.exe setup/setup.py setup/launcher.py phone/wasteland.apk \
              Desinstaller.exe userdata/setup-install.log; do
    test -f "$inst/$file" || { echo "Missing $key/$file" >&2; return 1; }
  done
  if [ "$key" = WastelandRebornHD ]; then
    test -f "$inst/setup/edition.json"
    test -f "$inst/setup/wasteland_hd/__main__.py"
    rg -q 'HD packs unavailable for now:|world: installed' "$inst/userdata/setup-install.log"
  else
    test ! -e "$inst/setup/edition.json"
  fi
  rg -q 'Game setup complete' "$inst/userdata/setup-install.log"
  wine reg query "HKCU\\Software\\$key" /v InstallDir >/dev/null
  wine reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\$key" /v UninstallString >/dev/null
  test "$(find "$WINEPREFIX" -type f -name "$product.lnk" | wc -l)" -ge 1
  test "$(find "$WINEPREFIX" -type f -path "*/Start Menu/Programs/$product/*.lnk" | wc -l)" -ge 4
  echo "Starting engine for $product (timeout 40s)"
  (cd "$inst/game" && timeout 40s wine "$inst/game/fallout2-ce.exe" > "$TEST_ROOT/engine-$key.log" 2>&1) || true
  find "$inst/game" -type f \( -iname 'debug.log' -o -iname 'ce-game-*.txt' -o -iname '*.log' \) -print > "$TEST_ROOT/game-logs-$key.txt"
  test -s "$TEST_ROOT/game-logs-$key.txt" || { echo "No engine startup log for $key" >&2; return 1; }
  echo "Uninstalling $product"
  timeout 180s wine "$inst/Desinstaller.exe" /S > "$TEST_ROOT/uninstall-$key.log" 2>&1
  # NSIS silent uninstallers copy themselves to %TEMP%, relaunch there and let
  # the first process exit at once, so the removal keeps running afterwards.
  # Poll for the real end instead of racing (and later killing) that process.
  for _ in $(seq 1 180); do
    [ ! -e "$inst/Desinstaller.exe" ] && [ ! -e "$inst/game/fallout2-ce.exe" ] && break
    sleep 1
  done
  test ! -e "$inst/game/fallout2-ce.exe" || { echo "Uninstall left $key/game/fallout2-ce.exe" >&2; return 1; }
  test ! -e "$inst/python/python.exe"
  test ! -e "$inst/setup/setup.py"
  wine reg query "HKCU\\Software\\$key" >/dev/null 2>&1 && { echo 'Registry key survived uninstall' >&2; return 1; }
  wine reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\$key" >/dev/null 2>&1 && { echo 'Uninstall key survived' >&2; return 1; }
  test "$(find "$WINEPREFIX" -type f -name "$product.lnk" | wc -l)" -eq 0
}

check_edition WastelandRebornHD 'Wasteland Reborn HD' "$F/windows/dist/WastelandRebornHD-Setup.exe"
check_edition WastelandReborn 'Wasteland Reborn' "$F/windows/dist/WastelandReborn-Setup.exe"
echo 'Both Wine installs, launches, and uninstalls passed.'
