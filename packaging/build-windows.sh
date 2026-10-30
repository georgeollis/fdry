#!/usr/bin/env bash
set -euo pipefail

: "${RUNNER_TEMP:?Set RUNNER_TEMP to a temporary build directory}"
: "${WINEPREFIX:?Set WINEPREFIX to an isolated Wine prefix}"
export WINEARCH=win64 WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml="

installer="$RUNNER_TEMP/python-3.15.2-amd64.exe"
curl --fail --location --retry 3 \
  https://www.python.org/ftp/python/3.15.2/python-3.15.2-amd64.exe \
  --output "$installer"
echo "06e225a228191b0f4d1dcf6905fbb21bf9f6970d13a2ec63137ab9bee76f15aa  $installer" | sha256sum --check
wine "$installer" /quiet InstallAllUsers=0 'TargetDir=C:\Python315' \
  Include_launcher=0 Include_test=0 Include_doc=0 Include_tcltk=0 \
  Shortcuts=0 PrependPath=0
wineserver --wait

python="$WINEPREFIX/drive_c/Python315/python.exe"
wine "$python" -c "import struct, sys; assert sys.platform == 'win32' and struct.calcsize('P') == 8; assert sys.version_info[:3] == (3, 15, 2)"
environment="$RUNNER_TEMP/windows-venv"
wine "$python" -m venv "$(winepath -w "$environment")"
python="$environment/Scripts/python.exe"

requirements="$RUNNER_TEMP/windows-requirements.txt"
uv export --locked --all-extras --no-dev --no-emit-project --output-file "$requirements"
wine "$python" -m pip install --require-hashes --only-binary=:all: -r "$(winepath -w "$requirements")"
wine "$python" -m pip install --no-deps --no-build-isolation --editable .
wine "$python" -m pip_audit --skip-editable
wine "$python" -m pytest -q -m "not binary"
wine "$python" -m PyInstaller --noconfirm --clean --log-level WARN packaging/fdry.spec
file dist/fdry.exe | grep --fixed-strings "PE32+ executable"

export FDRY_EXE
FDRY_EXE="$(winepath -w "$PWD/dist/fdry.exe")"
wine "$python" -m pytest -q tests/binary
