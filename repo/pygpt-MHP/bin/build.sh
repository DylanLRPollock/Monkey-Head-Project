#!/usr/bin/env bash
set -euo pipefail
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.07.2025
# ==================================================
# This script is used to build the app using pyinstaller

VERSION="2.5.8"

cd "$(dirname "$0")" || exit
DIR_CURRENT="$(pwd)"
DIR_PARENT="$(dirname "$DIR_CURRENT")"

cd "$DIR_PARENT" || exit

source ./venv/bin/activate
pyinstaller --noconfirm linux.spec

cp -rf "$DIR_PARENT"/LICENSE "$DIR_PARENT"/dist/Linux/
cp -rf "$DIR_PARENT"/README.md "$DIR_PARENT"/dist/Linux/
cp -rf "$DIR_PARENT"/CHANGELOG.md "$DIR_PARENT"/dist/Linux/
cp -rf "$DIR_PARENT"/SECURITY.md "$DIR_PARENT"/dist/Linux/
cp -rf "$DIR_PARENT"/icon.png "$DIR_PARENT"/dist/Linux/

mv "$DIR_PARENT"/dist/Linux "$DIR_PARENT"/dist/pygpt-$VERSION
cd "$DIR_PARENT"/dist || exit
zip -r pygpt-$VERSION.zip pygpt-$VERSION -9
cd "$DIR_PARENT" || exit

python -m build
twine check dist/*

if [ -f "$DIR_PARENT/dist/pygpt-$VERSION.zip" ]; then
        sha1sum "$DIR_PARENT"/dist/pygpt-$VERSION.zip
fi

if [ -f "$DIR_PARENT/dist/pygpt-$VERSION.msi" ]; then
        sha1sum "$DIR_PARENT"/dist/pygpt-$VERSION.msi
fi

# twine check dist/*
# twine upload dist/*
