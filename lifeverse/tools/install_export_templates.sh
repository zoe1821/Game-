#!/usr/bin/env bash
# Installs the Godot export templates matching the pinned editor (all platforms).
# Needed only to EXPORT builds (Linux, Windows, macOS, Web, Android, iOS), not to
# run the game or its tests. Idempotent. ~1.2 GB download, ~2 GB on disk.
set -euo pipefail

GODOT_VERSION="4.7.2"
TEMPLATES_SHA256="f298490b8d44d934be425a5a65a51bf15f422428b229a06a6e11d9ffea248011"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
DEST="${DATA_HOME}/godot/export_templates/${GODOT_VERSION}.stable"
URL="https://downloads.godotengine.org/?version=${GODOT_VERSION}&flavor=stable&slug=export_templates.tpz&platform=templates"

if [ "$(cat "${DEST}/version.txt" 2>/dev/null || true)" != "${GODOT_VERSION}.stable" ]; then
	work="$(mktemp -d)"
	trap 'rm -rf "${work}"' EXIT
	echo "Downloading Godot ${GODOT_VERSION} export templates (~1.2 GB)..."
	curl -fsSL --retry 3 --max-time 1800 "${URL}" -o "${work}/templates.tpz"
	echo "${TEMPLATES_SHA256}  ${work}/templates.tpz" | sha256sum -c - >/dev/null
	unzip -o -q "${work}/templates.tpz" -d "${work}/x"
	mkdir -p "${DEST}"
	cp -f "${work}/x/templates/"* "${DEST}/"
fi

echo "Export templates: $(cat "${DEST}/version.txt") in ${DEST}"
