#!/usr/bin/env bash
# Builds the debug APK of the engine fork (arm64). Usage: android-build.sh [gradle task]
# The APK is signed with this machine's Android debug key (~/.android/debug.keystore):
# it installs as an update only over an APK signed with the same key.
set -eu
F=$(cd "$(dirname "$0")/.." && pwd)
export JAVA_HOME=$(ls -d "$F"/toolchain/jdk-17*)
export ANDROID_HOME=$F/toolchain/android-sdk ANDROID_SDK_ROOT=$F/toolchain/android-sdk
export JAVA_TOOL_OPTIONS="-Djava.net.preferIPv6Addresses=true -Dorg.gradle.internal.http.connectionTimeout=30000 -Dorg.gradle.internal.repository.max.retries=6"
cd "$F/src/imbaner_fallout2-ce-mobile/os/android"
./gradlew --no-daemon ${1:-assembleDebug} -PabiFilters=arm64-v8a
find app/build/outputs/apk -name '*.apk' -newer gradlew -printf '%p %s bytes\n'
