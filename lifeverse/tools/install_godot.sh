#!/usr/bin/env bash
# Installs the pinned Godot editor binary used by LIFEVERSE (Linux x86_64).
# Idempotent: does nothing if the pinned version is already installed.
#
#   lifeverse/tools/install_godot.sh            # installs to /opt/godot, links /usr/local/bin/godot
#   GODOT_HOME=$HOME/godot lifeverse/tools/install_godot.sh
#
# The version and checksum are pinned on purpose: the architecture and tests are
# verified against exactly this engine build (see lifeverse/docs/ARCHITECTURE.md §2).
set -euo pipefail

GODOT_VERSION="4.7.2"
GODOT_SHA256="cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4"
GODOT_HOME="${GODOT_HOME:-/opt/godot}"
BIN_NAME="Godot_v${GODOT_VERSION}-stable_linux.x86_64"
BIN_PATH="${GODOT_HOME}/${BIN_NAME}"
LINK_DIR="${GODOT_LINK_DIR:-/usr/local/bin}"
URL="https://downloads.godotengine.org/?version=${GODOT_VERSION}&flavor=stable&slug=linux.x86_64.zip&platform=linux.64"

if [ ! -x "${BIN_PATH}" ]; then
	mkdir -p "${GODOT_HOME}"
	tmp_zip="$(mktemp "${GODOT_HOME}/godot.XXXXXX.zip")"
	trap 'rm -f "${tmp_zip}"' EXIT
	echo "Downloading Godot ${GODOT_VERSION}..."
	curl -fsSL --retry 3 --max-time 600 "${URL}" -o "${tmp_zip}"
	echo "${GODOT_SHA256}  ${tmp_zip}" | sha256sum -c - >/dev/null
	unzip -o -q "${tmp_zip}" -d "${GODOT_HOME}"
	chmod +x "${BIN_PATH}"
fi

if [ -d "${LINK_DIR}" ] && [ -w "${LINK_DIR}" ]; then
	ln -sf "${BIN_PATH}" "${LINK_DIR}/godot"
fi

"${BIN_PATH}" --version
