#!/usr/bin/env bash
# Installs what Godot 4.7 needs to export Android APKs with the prebuilt template:
# Android SDK command-line tools, platform-tools, build-tools 35.0.1, platform 35,
# and a debug keystore. Requires a JDK (17 or newer) already on PATH.
# NDK/CMake are NOT installed: they are only needed for custom Gradle builds.
#
# Installs to Godot's default locations so no editor setting has to be changed:
#   SDK       $HOME/Android/Sdk                     (override with ANDROID_HOME)
#   keystore  <data>/godot/keystores/debug.keystore (alias androiddebugkey / pass android)
# Idempotent. ~500 MB on disk.
set -euo pipefail

CLT_BUILD="16111833"
CLT_SHA1="e025545c62a8e64c7559119566a569fb1dec5f60"
SDK="${ANDROID_HOME:-$HOME/Android/Sdk}"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
KEYSTORE="${DATA_HOME}/godot/keystores/debug.keystore"
SM="${SDK}/cmdline-tools/latest/bin/sdkmanager"

command -v java >/dev/null || { echo "A JDK (17+) is required on PATH." >&2; exit 1; }

if [ ! -x "${SM}" ]; then
	mkdir -p "${SDK}/cmdline-tools"
	work="$(mktemp -d)"
	trap 'rm -rf "${work}"' EXIT
	echo "Downloading Android command-line tools..."
	curl -fsSL --retry 3 --max-time 600 \
		"https://dl.google.com/android/repository/commandlinetools-linux-${CLT_BUILD}_latest.zip" -o "${work}/clt.zip"
	echo "${CLT_SHA1}  ${work}/clt.zip" | sha1sum -c - >/dev/null
	unzip -q "${work}/clt.zip" -d "${work}/x"
	rm -rf "${SDK}/cmdline-tools/latest"
	mv "${work}/x/cmdline-tools" "${SDK}/cmdline-tools/latest"
fi

if [ ! -x "${SDK}/build-tools/35.0.1/apksigner" ] || [ ! -d "${SDK}/platforms/android-35" ] || [ ! -x "${SDK}/platform-tools/adb" ]; then
	echo "Installing Android SDK packages..."
	(yes || true) | "${SM}" --sdk_root="${SDK}" --licenses >/dev/null 2>&1 || true
	"${SM}" --sdk_root="${SDK}" "platform-tools" "build-tools;35.0.1" "platforms;android-35" >/dev/null 2>&1
fi

if [ ! -f "${KEYSTORE}" ]; then
	mkdir -p "$(dirname "${KEYSTORE}")"
	keytool -genkeypair -keyalg RSA -keysize 2048 -alias androiddebugkey -keypass android \
		-keystore "${KEYSTORE}" -storepass android -dname "CN=Android Debug,O=Android,C=US" \
		-validity 9999 -deststoretype pkcs12 >/dev/null 2>&1
fi

echo "Android SDK: ${SDK}"
"${SDK}/platform-tools/adb" version | head -1
echo "Debug keystore: ${KEYSTORE}"
