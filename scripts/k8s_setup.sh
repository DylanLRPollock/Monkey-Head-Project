#!/bin/bash
set -e

K8S_DIR="k8s"

if [ ! -d "$K8S_DIR" ]; then
    echo "Kubernetes manifests not found in $K8S_DIR" >&2
    exit 1
fi

kubectl apply -f "$K8S_DIR"/

kubectl get pods
kubectl get services
