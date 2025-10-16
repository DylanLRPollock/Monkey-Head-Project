#!/usr/bin/env bash
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: K8S Cleanup shell script (huey/memory/SH)

set -euo pipefail
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.05.2025
# ==================================================
set -e

K8S_DIR="k8s"

if [ ! -d "$K8S_DIR" ]; then
    echo "Kubernetes manifests not found in $K8S_DIR" >&2
    exit 1
fi

kubectl delete -f "$K8S_DIR"/ || true
