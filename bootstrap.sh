#!/usr/bin/env bash
# One-time setup for building Wasteland Reborn from this repository on Linux x86_64:
# engine submodule, toolchains (into toolchain/), the HD pack tools, the RPU game
# profile (build/profile) and the Android APK (apk/). Then: windows/build.sh makes
# the Windows installer.
#
#   ./bootstrap.sh                 the classic edition's APK: apk/Wasteland-arm64.apk
#   ./bootstrap.sh --edition hd    the HD edition's APK:   apk/Wasteland-HD-arm64.apk
#   ./bootstrap.sh --linux-only    Linux PC prerequisites only (no Windows/Android toolchain)
#   ./bootstrap.sh --no-android    skip the Android SDK and the APK
#                                  (windows/build.sh then needs APK=<path to an APK>)
#
# The engine submodule is pinned to its wasteland-reborn-hd branch, which contains
# wasteland-reborn: one checkout builds both editions (the edition is the Gradle flag
# -Pfallout2ce.hd, not a different source tree).
#
# Host packages: git cmake ninja rsync unzip curl tar xz python3 ImageMagick (magick),
# SDL2 and zlib development files (host build of the engine's ce-dat-tool), and
# makensis or Wine (to run the bundled NSIS). Nothing from Fallout 2 itself is
# downloaded: players add their own game files at install time.
set -euo pipefail
F=$(cd "$(dirname "$0")" && pwd)
T=$F/toolchain
ENGINE=$F/src/imbaner_fallout2-ce-mobile
# The installer module (wasteland_hd) the HD edition ships; pinned like the
# toolchains below. Its own `art` submodule (the HD image source) is never cloned.
HDTOOLS_URL=https://github.com/Linutesto/wasteland-hd-tools.git
HDTOOLS_COMMIT=7559487f518ab9f832d9fb25f0b84983ffad1f30
ANDROID=1
WINDOWS=1
EDITION=normal
while [ $# -gt 0 ]; do
    case "$1" in
        --no-android) ANDROID=0 ;;
        --linux-only) ANDROID=0; WINDOWS=0 ;;
        --edition)
            [ $# -ge 2 ] || { echo "--edition needs normal or hd" >&2; exit 2; }
            EDITION=$2; shift ;;
        --edition=*) EDITION=${1#--edition=} ;;
        -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
        *) echo "bootstrap.sh: unknown argument: $1 (see --help)" >&2; exit 2 ;;
    esac
    shift
done
case "$EDITION" in
    normal|hd) ;;
    *) echo "invalid --edition $EDITION (normal or hd)" >&2; exit 2 ;;
esac

LLVM_MINGW=llvm-mingw-20261020-ucrt-ubuntu-22.04-x86_64
LLVM_MINGW_URL=https://github.com/mstorsjo/llvm-mingw/releases/download/20261020/$LLVM_MINGW.tar.xz
JDK_URL=https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.21%2B9/OpenJDK17U-jdk_x64_linux_hotspot_17.0.21_9.tar.gz
SDK_TOOLS_URL=https://dl.google.com/android/repository/commandlinetools-linux-15859902_latest.zip
PYTHON_URL=https://www.python.org/ftp/python/3.13.9/python-3.13.9-embed-amd64.zip
PYTHON_SHA256=91d828c2da3a029b41699e918674a0cb379c02cf20dab9c501306885f837402a
NSIS_URL=https://downloads.sourceforge.net/project/nsis/NSIS%203/3.11/nsis-3.11.zip
NSIS_SHA256=c7d27f780ddb6cffb4730138cd1591e841f4b7edb155856901cdf5f214394fa1

need() { command -v "$1" >/dev/null || { echo "missing host tool: $1" >&2; exit 1; }; }
for tool in git cmake ninja rsync unzip curl tar python3; do need "$tool"; done
if [ "$WINDOWS" = 1 ]; then
    need magick
    command -v makensis >/dev/null || need wine
fi

# download <url> <file> [sha256]
download() {
    if [ ! -f "$2" ]; then
        echo "  downloading $(basename "$2")"
        curl -fL --retry 3 -o "$2.part" "$1" && mv "$2.part" "$2"
    fi
    if [ -n "${3:-}" ] && ! echo "$3  $2" | sha256sum -c --quiet; then
        echo "sha256 mismatch: $2" >&2; exit 1
    fi
}

echo "== engine (submodule, wasteland-reborn-hd)"
git -C "$F" submodule update --init

echo "== HD pack tools (wasteland-hd-tools, pinned)"
HDTOOLS=$F/src/wasteland-hd-tools
if [ ! -d "$HDTOOLS/.git" ]; then
    git clone -q "$HDTOOLS_URL" "$HDTOOLS"
fi
if ! git -C "$HDTOOLS" cat-file -e "$HDTOOLS_COMMIT^{commit}" 2>/dev/null; then
    git -C "$HDTOOLS" fetch -q origin
fi
if ! git -C "$HDTOOLS" cat-file -e "$HDTOOLS_COMMIT^{commit}" 2>/dev/null; then
    echo "wasteland-hd-tools: pinned commit $HDTOOLS_COMMIT is not available" >&2
    echo "(update HDTOOLS_COMMIT in bootstrap.sh after checking src/wasteland-hd-tools)" >&2
    exit 1
fi
git -C "$HDTOOLS" checkout -q --detach "$HDTOOLS_COMMIT"

mkdir -p "$T/downloads"
if [ "$WINDOWS" = 1 ]; then
mkdir -p "$T/win"
echo "== llvm-mingw (Windows cross compiler)"
if [ ! -d "$T/$LLVM_MINGW" ]; then
    download "$LLVM_MINGW_URL" "$T/downloads/$LLVM_MINGW.tar.xz"
    tar -xJf "$T/downloads/$LLVM_MINGW.tar.xz" -C "$T"
fi

echo "== embeddable Python for Windows"
download "$PYTHON_URL" "$T/win/python-embed.zip" "$PYTHON_SHA256"

if ! command -v makensis >/dev/null; then
    echo "== NSIS (runs under Wine)"
    download "$NSIS_URL" "$T/win/nsis.zip" "$NSIS_SHA256"
    [ -d "$T/win/nsis-3.11" ] || unzip -q "$T/win/nsis.zip" -d "$T/win"
fi

fi
echo "== game profile (RPU + FO2Tweaks, from their GitHub releases)"
python3 "$F/tools/mkprofile.py"

if [ "$ANDROID" = 1 ]; then
    echo "== JDK 17 + Android SDK"
    if ! ls -d "$T"/jdk-17* >/dev/null 2>&1; then
        download "$JDK_URL" "$T/downloads/jdk17.tar.gz"
        tar -xzf "$T/downloads/jdk17.tar.gz" -C "$T"
    fi
    SDK=$T/android-sdk
    if [ ! -x "$SDK/cmdline-tools/latest/bin/sdkmanager" ]; then
        download "$SDK_TOOLS_URL" "$T/downloads/cmdline-tools.zip"
        rm -rf "$SDK/cmdline-tools"; mkdir -p "$SDK/cmdline-tools"
        unzip -q "$T/downloads/cmdline-tools.zip" -d "$SDK/cmdline-tools"
        mv "$SDK/cmdline-tools/cmdline-tools" "$SDK/cmdline-tools/latest"
    fi
    export JAVA_HOME=$(ls -d "$T"/jdk-17*)
    # Google's SDK licenses: read and accept them yourself (once).
    [ -d "$SDK/licenses" ] || "$SDK/cmdline-tools/latest/bin/sdkmanager" --sdk_root="$SDK" --licenses
    "$SDK/cmdline-tools/latest/bin/sdkmanager" --sdk_root="$SDK" \
        "platforms;android-35" "build-tools;35.0.0" "ndk;27.3.13750724" "cmake;3.22.1" "platform-tools"

    # The edition is one Gradle flag: -Pfallout2ce.hd builds the .hd app (own
    # icon, own files and saves) from the same engine source.
    if [ "$EDITION" = hd ]; then
        GRADLE_TASK="assemblePhone -Pfallout2ce.hd"
        BUILT=$ENGINE/os/android/app/build/outputs/apk/phone/app-phone.apk
        APK_NAME=Wasteland-HD-arm64.apk
    else
        GRADLE_TASK="assembleDebug"
        BUILT=$ENGINE/os/android/app/build/outputs/apk/debug/app-debug.apk
        APK_NAME=Wasteland-arm64.apk
    fi
    echo "== APK ($EDITION): $GRADLE_TASK"
    "$F/tools/android-build.sh" "$GRADLE_TASK"
    [ -f "$BUILT" ] || { echo "gradle did not produce $BUILT" >&2; exit 1; }
    mkdir -p "$F/apk"
    cp "$BUILT" "$F/apk/$APK_NAME"
    ls -la "$F/apk/$APK_NAME"
    APK_DONE=$F/apk/$APK_NAME
else
    APK_DONE='(skipped: --no-android)'
fi

echo
echo "Done. APK: $APK_DONE"
if [ "$WINDOWS" = 1 ]; then
echo "Build the Windows installer with:"
if [ "$EDITION" = hd ]; then
    echo "  EDITION=hd windows/build.sh    # windows/dist/WastelandRebornHD-Setup.exe"
else
    echo "  windows/build.sh               # windows/dist/WastelandReborn-Setup.exe"
    echo "  EDITION=hd windows/build.sh    # the HD edition (needs its APK: ./bootstrap.sh --edition hd)"
fi

fi
