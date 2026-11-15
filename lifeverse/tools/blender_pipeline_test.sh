#!/usr/bin/env bash
# Reproducible verification of the 3D asset pipeline: a headless Blender script builds
# a mesh with a material and a keyframe animation, renders it (Cycles, CPU) and exports
# .glb; Godot imports the .glb and must find the mesh, the material and the animation.
# Needs: setup_dev_env.sh --all
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="${here}/../build/blender_pipeline"
rm -rf "${work}"; mkdir -p "${work}/proj"
blender -b --python "${here}/blender_pipeline/make_test_asset.py" -- "${work}/proj/desk.glb" "${work}/render.png" >"${work}/blender.log" 2>&1
[ -s "${work}/proj/desk.glb" ] || { echo "BLENDER_PIPELINE_FAIL no .glb (see ${work}/blender.log)"; exit 1; }
[ -s "${work}/render.png" ] || { echo "BLENDER_PIPELINE_FAIL no render"; exit 1; }
printf 'config_version=5\n\n[application]\nconfig/name="blender_pipeline"\nconfig/features=PackedStringArray("4.7")\n' >"${work}/proj/project.godot"
cp "${here}/blender_pipeline/check_import.gd" "${work}/proj/"
godot --headless --path "${work}/proj" --import >/dev/null 2>&1
godot --headless --path "${work}/proj" --script check_import.gd 2>&1 | grep BLENDER_PIPELINE_
