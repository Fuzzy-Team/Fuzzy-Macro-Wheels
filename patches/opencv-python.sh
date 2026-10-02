#!/bin/bash
# Patch an extracted opencv-python 4.6.0.66 source tree so it builds with current Xcode.
#
# OpenCV 4.6 bundles old zlib and libpng that test `defined(TARGET_OS_MAC)`, which every
# current macOS SDK defines, and then take paths for classic Mac OS: zlib defines fdopen as
# NULL (clashing with <stdio.h>) and libpng includes <fp.h> (which no longer exists). Both
# checks were later removed upstream (zlib checks only MACOS; libpng 1.6.38 dropped fp.h).
#
# Usage: patches/opencv-python.sh <source dir>
set -euo pipefail
src="$1/opencv/3rdparty"

patch_line() {
	local file="$1" from="$2" to="$3"
	if ! grep -qF -- "$from" "$file"; then
		echo "patch target not found in $file: $from" >&2
		exit 1
	fi
	python3 - "$file" "$from" "$to" <<'EOF'
import sys
path, old, new = sys.argv[1:]
text = open(path).read()
open(path, "w").write(text.replace(old, new, 1))
EOF
	echo "patched $file"
}

patch_line "$src/zlib/zutil.h" \
	"#if defined(MACOS) || defined(TARGET_OS_MAC)" \
	"#if defined(MACOS)"
patch_line "$src/libpng/pngpriv.h" \
	"defined(THINK_C) || defined(__SC__) || defined(TARGET_OS_MAC)" \
	"defined(THINK_C) || defined(__SC__)"
