#!/usr/bin/env bash
# Reproducible verification of the export toolchain. Exports tools/export_smoke to
# Linux, Windows, Web and Android and checks each artifact as far as this machine can:
#   Linux    launched; must print the check line
#   Web      loaded in headless Chromium (needs node + playwright); must print the check line
#   Windows  file must be a PE x86-64 executable (cannot be executed on Linux)
#   Android  APK must pass apksigner verify and zipalign -c (not run on a device)
# Exit code 0 only if nothing FAILed. Needs: setup_dev_env.sh --all
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
proj="${here}/export_smoke"
out="${here}/../build/export_smoke"
sdk="${ANDROID_HOME:-$HOME/Android/Sdk}"
fail=0
report() { printf '%-8s %-5s %s\n' "$1" "$2" "$3"; [ "$2" = "FAIL" ] && fail=1; return 0; }

rm -rf "${out}"; mkdir -p "${out}/linux" "${out}/windows" "${out}/web" "${out}/android"
godot --headless --path "${proj}" --import >/dev/null 2>&1
for p in Linux Windows Web; do
	godot --headless --path "${proj}" --export-release "${p}" >"${out}/${p}.log" 2>&1 || true
done
godot --headless --path "${proj}" --export-debug Android >"${out}/Android.log" 2>&1 || true

# Linux
if [ -f "${out}/linux/smoke.x86_64" ]; then
	chmod +x "${out}/linux/smoke.x86_64"
	line="$(timeout 60 "${out}/linux/smoke.x86_64" --headless -- --quit-after-check 2>&1 | grep EXPORT_SMOKE_OK || true)"
	[ -n "${line}" ] && report Linux PASS "${line}" || report Linux FAIL "binary did not print the check line"
else report Linux FAIL "no binary (see ${out}/Linux.log)"; fi

# Windows
if [ -f "${out}/windows/smoke.exe" ]; then
	pe="$(python3 -c "
import struct,sys
d=open(sys.argv[1],'rb').read(4096); o=struct.unpack('<I',d[0x3c:0x40])[0]
print('ok' if d[:2]==b'MZ' and d[o:o+4]==b'PE\0\0' and struct.unpack('<H',d[o+4:o+6])[0]==0x8664 else 'bad')" "${out}/windows/smoke.exe")"
	[ "${pe}" = "ok" ] && report Windows PASS "valid PE x86-64 (not executed)" || report Windows FAIL "not a PE x86-64 file"
else report Windows FAIL "no exe (see ${out}/Windows.log)"; fi

# Web
if [ -f "${out}/web/index.wasm" ]; then
	if command -v node >/dev/null && node -e "require('playwright')" 2>/dev/null; then
		port=8765
		(cd "${out}/web" && exec python3 -m http.server "${port}" >/dev/null 2>&1) &
		srv=$!; sleep 1
		line="$(node "${proj}/web_check.js" "http://127.0.0.1:${port}/index.html" 2>&1 | grep EXPORT_SMOKE_OK || true)"
		kill "${srv}" 2>/dev/null
		[ -n "${line}" ] && report Web PASS "${line}" || report Web FAIL "check line not seen in browser console"
	else report Web SKIP "exported, but node/playwright not available to run it"; fi
else report Web FAIL "no wasm (see ${out}/Web.log)"; fi

# Android
if [ -f "${out}/android/smoke.apk" ]; then
	bt="${sdk}/build-tools/35.0.1"
	if "${bt}/apksigner" verify "${out}/android/smoke.apk" >/dev/null 2>&1 && "${bt}/zipalign" -c 4 "${out}/android/smoke.apk" >/dev/null 2>&1; then
		report Android PASS "signed and aligned APK (not run on a device)"
	else report Android FAIL "apksigner/zipalign check failed"; fi
else report Android FAIL "no apk (see ${out}/Android.log)"; fi

exit "${fail}"
