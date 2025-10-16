#!/usr/bin/env bash
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Rst To Md shell script (huey/memory/SH)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.08.2025
# ==================================================
for f in *.rst; do
  filename="${f%.*}"
  echo "Converting $f to $filename.md"
  pandoc "$f" -f rst -t markdown -o "$filename.md"
done
