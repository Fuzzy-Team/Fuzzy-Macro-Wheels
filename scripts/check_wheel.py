#!/usr/bin/env python3
"""Fail if a wheel won't load on old Intel Macs.

Checks every Mach-O binary in each wheel:
  - it is x86_64,
  - it doesn't require a newer macOS than --max-macos (from LC_BUILD_VERSION or
    LC_VERSION_MIN_MACOSX),
  - it only links libraries that ship with macOS (/usr/lib, /System/Library) or that are
    bundled inside the wheel itself (@loader_path, @rpath).
Also checks the wheel's platform tag isn't newer than --max-macos.

Usage: check_wheel.py --max-macos 10.12 dist/*.whl
"""

import argparse
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

MACHO_MAGICS = {b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca"}
SYSTEM_PREFIXES = ("/usr/lib/", "/System/Library/", "@loader_path/", "@rpath/", "@executable_path/")


def version_tuple(text):
    return tuple(int(part) for part in text.split("."))


def is_macho(path):
    with open(path, "rb") as handle:
        return handle.read(4) in MACHO_MAGICS


def min_macos(path):
    """The lowest macOS version the binary declares it supports."""
    output = subprocess.run(["otool", "-l", str(path)], capture_output=True, text=True, check=True).stdout
    versions = []
    lines = output.splitlines()
    for index, line in enumerate(lines):
        command = line.strip()
        if command == "cmd LC_BUILD_VERSION":
            block = lines[index:index + 6]
            platform = next((l.split()[1] for l in block if l.strip().startswith("platform")), "")
            minos = next((l.split()[1] for l in block if l.strip().startswith("minos")), None)
            # platform 1 is macOS
            if minos and platform in ("1", "MACOS", "macos"):
                versions.append(minos)
        elif command == "cmd LC_VERSION_MIN_MACOSX":
            version = next((l.split()[1] for l in lines[index:index + 4] if l.strip().startswith("version")), None)
            if version:
                versions.append(version)
    return versions


def check_binary(path, label, max_macos):
    problems = []
    archs = subprocess.run(["lipo", "-archs", str(path)], capture_output=True, text=True).stdout.split()
    if "x86_64" not in archs:
        problems.append(f"{label}: architectures {archs}, needs x86_64")
    for version in min_macos(path):
        if version_tuple(version) > version_tuple(max_macos):
            problems.append(f"{label}: requires macOS {version}")
    links = subprocess.run(["otool", "-L", str(path)], capture_output=True, text=True, check=True).stdout
    for line in links.splitlines()[1:]:
        library = line.strip().split(" (")[0]
        if library and not library.startswith(SYSTEM_PREFIXES):
            problems.append(f"{label}: links {library}, which isn't part of macOS or the wheel")
    return problems


def check_wheel(wheel, max_macos):
    problems = []
    match = re.search(r"macosx_(\d+)_(\d+)_", wheel.name)
    if not match:
        problems.append(f"{wheel.name}: no macosx platform tag")
    elif version_tuple(f"{match.group(1)}.{match.group(2)}") > version_tuple(max_macos):
        problems.append(f"{wheel.name}: tagged for macOS {match.group(1)}.{match.group(2)}")

    binaries = 0
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(wheel) as archive:
            archive.extractall(tmp)
        for path in sorted(Path(tmp).rglob("*")):
            if path.is_file() and not path.is_symlink() and is_macho(path):
                binaries += 1
                problems += check_binary(path, f"{wheel.name}:{path.relative_to(tmp)}", max_macos)
    if binaries == 0:
        problems.append(f"{wheel.name}: no compiled binaries found")
    return binaries, problems


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--max-macos", required=True, help="oldest macOS the wheels must run on, e.g. 10.12")
    parser.add_argument("wheels", nargs="+", type=Path)
    args = parser.parse_args()

    failed = False
    for wheel in args.wheels:
        binaries, problems = check_wheel(wheel, args.max_macos)
        if problems:
            failed = True
            print(f"FAIL {wheel.name}")
            for problem in problems:
                print(f"  {problem}")
        else:
            print(f"OK   {wheel.name}: {binaries} binaries, all x86_64, macOS <= {args.max_macos}, system libraries only")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
