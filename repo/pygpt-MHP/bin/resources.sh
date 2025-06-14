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

cd "$(dirname "$0")" || exit
DIR_CURRENT="$(pwd)"
DIR_PARENT="$(dirname "$DIR_CURRENT")"

cd "$DIR_PARENT" || exit

source ./venv/bin/activate
python3 bin/resources.py "$@"

cd "$DIR_PARENT"/src/pygpt_net || exit
pyside6-rcc icons.qrc -o icons_rc.py
pyside6-rcc js.qrc -o js_rc.py
pyside6-rcc css.qrc -o css_rc.py
pyside6-rcc fonts.qrc -o fonts_rc.py

echo "Resources compiled to: src/pygpt_net/icons_rc.py"
echo "Resources compiled to: src/pygpt_net/js_rc.py"
echo "Resources compiled to: src/pygpt_net/css_rc.py"
echo "Resources compiled to: src/pygpt_net/fonts_rc.py"
