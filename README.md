# Fuzzy Macro Wheels

Prebuilt Python wheels for [Fuzzy Macro](https://github.com/Fuzzy-Team/Fuzzy-Macro) on
Intel Macs below macOS 10.15.

On those Macs, `install_dependencies.command` installs python.org Python 3.7.9, and two
packages have no wheel for it on PyPI, so pip compiles them on the user's Mac:

| Package | Why it builds from source | Cost on the user's Mac |
| --- | --- | --- |
| `opencv-python==4.6.0.66` | No Intel macOS wheel below 10.15 | An hour or more, and a "you need to install a JDK" popup |
| `aiohttp==3.7.4.post0` | The only macOS wheel is for 10.14 | A few minutes on 10.12–10.13 |

This repo builds them once, for macOS 10.12 and Python 3.7.9 on Intel, and publishes them to
a GitHub Release that the installer can download instead.

## Building

Actions → **Build legacy macOS wheels** → **Run workflow**.

- Leave **release_tag** empty for a test build. The wheels are attached to the run as an
  artifact.
- Set **release_tag** (e.g. `legacy-macos-1`) to also publish the wheels and a
  `SHA256SUMS` file to that release.

Each build runs on GitHub's Intel macOS runner (`macos-15-intel`) and:

1. Installs the same python.org Python 3.7.9 package the installer uses (hash-checked).
2. Builds the wheel from source with `MACOSX_DEPLOYMENT_TARGET=10.12`.
3. Runs `scripts/check_wheel.py`, which fails the build if any binary isn't x86_64, needs a
   macOS newer than 10.12, or links a library that isn't part of macOS or the wheel.
4. Installs the wheel into a fresh venv and runs `scripts/smoke_test.py`, which uses the
   compiled code the way Fuzzy Macro does.

## Before the installer uses a release

The runner's Xcode officially supports macOS 10.13 and newer. The build still targets 10.12
and the check above verifies every binary says so, but only a real Mac can prove nothing
newer slipped in. Before pointing the installer at a release, on a Mac running 10.12 (or
at least 10.13/10.14):

```bash
python3.7 -m venv /tmp/wheel-test
/tmp/wheel-test/bin/pip install "numpy<2" opencv_python-*.whl aiohttp-*.whl
/tmp/wheel-test/bin/python scripts/smoke_test.py opencv-python
/tmp/wheel-test/bin/python scripts/smoke_test.py aiohttp
```

Then run an AI gather in Fuzzy Macro with the wheel installed.

## Using a release in the installer

Install the wheel by URL with its hash, and fall back to building from source if the
download fails, for example:

```bash
OPENCV_WHEEL="https://github.com/Fuzzy-Team/Fuzzy-Macro-Wheels/releases/download/<tag>/<opencv wheel>#sha256=<hash>"
install_pip_package "$OPENCV_WHEEL" || install_pip_package "opencv-python==4.6.0.66"
```

pip checks the `#sha256=` fragment and refuses a file that doesn't match.

## Adding a package

Add an entry to the `matrix` in `.github/workflows/build-wheels.yml` and a test to
`scripts/smoke_test.py`.
