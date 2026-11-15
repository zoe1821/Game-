#!/usr/bin/env bash
# One command to prepare a development machine (Linux x86_64) for LIFEVERSE.
#
#   lifeverse/tools/setup_dev_env.sh          # core: Godot + Python dev tools (enough to run and test)
#   lifeverse/tools/setup_dev_env.sh --all    # core + Blender + export templates + Android SDK
#
# Every step is idempotent and checksum-pinned; see the individual scripts.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${here}/install_godot.sh"
python3 -m pip install -q --disable-pip-version-check --root-user-action=ignore -r "${here}/requirements-dev.txt"
echo "gdlint $(gdlint --version 2>&1 | awk '{print $2}')"

if [ "${1:-}" = "--all" ]; then
	"${here}/install_blender.sh"
	"${here}/install_export_templates.sh"
	"${here}/install_android_sdk.sh"
fi
echo "Development environment ready."
