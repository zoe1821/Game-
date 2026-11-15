#!/usr/bin/env bash
# Installs the pinned Blender build used for LIFEVERSE's optional 3D assets (Linux x86_64).
# Idempotent: does nothing if the pinned version is already installed.
#
#   lifeverse/tools/install_blender.sh          # installs to /opt/blender, links /usr/local/bin/blender
#   BLENDER_HOME=$HOME/blender lifeverse/tools/install_blender.sh
#
# Blender is only needed to author or re-export 3D assets (.blend -> .glb). Running
# the game and its tests needs Godot only (see install_godot.sh).
set -euo pipefail

BLENDER_VERSION="5.3.0"
BLENDER_SERIES="5.3"
BLENDER_SHA256="dacb8264197a3f7fda6001285a5a506fc97ee943881261c2c3bd63c882f22e05"
BLENDER_HOME="${BLENDER_HOME:-/opt/blender}"
DIR_NAME="blender-${BLENDER_VERSION}-linux-x64"
BIN_PATH="${BLENDER_HOME}/${DIR_NAME}/blender"
LINK_DIR="${BLENDER_LINK_DIR:-/usr/local/bin}"
URL="https://download.blender.org/release/Blender${BLENDER_SERIES}/${DIR_NAME}.tar.xz"

if [ ! -x "${BIN_PATH}" ]; then
	mkdir -p "${BLENDER_HOME}"
	tmp_tar="$(mktemp "${BLENDER_HOME}/blender.XXXXXX.tar.xz")"
	trap 'rm -f "${tmp_tar}"' EXIT
	echo "Downloading Blender ${BLENDER_VERSION} (~400 MB)..."
	curl -fsSL --retry 3 --max-time 1200 "${URL}" -o "${tmp_tar}"
	echo "${BLENDER_SHA256}  ${tmp_tar}" | sha256sum -c - >/dev/null
	tar -xJf "${tmp_tar}" -C "${BLENDER_HOME}"
fi

if [ -d "${LINK_DIR}" ] && [ -w "${LINK_DIR}" ]; then
	ln -sf "${BIN_PATH}" "${LINK_DIR}/blender"
fi

"${BIN_PATH}" --version | head -1
