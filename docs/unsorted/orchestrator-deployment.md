# HostOS/SubOS/NanoOS Deployment Guide

The orchestrator CLIs can prepare workspaces and publish manifests that may be applied to a Kubernetes cluster.

## Running the orchestrators

Each orchestrator exposes a `setup`, `deploy`, or `all` command. The default `all` command performs the complete workflow:

```bash
python3 docker/hostos/hostos.py --workspace "$HOME/HostOS" all
python3 docker/subos/subos.py --workspace "$HOME/SubOS" --service-port 8080 all
python3 docker/nanoos/nanoos.py --workspace "$HOME/NanoOS" --service-port 8081 all
```

Use `--skip-os-check` or provide `--allow-os <name>` if you need to override distribution detection (for example on derivative Debian releases). The `setup` sub-command performs package installation, virtualization/firewall checks, and workspace creation without applying manifests. When running HostOS on nested hypervisors or macOS, ensure that `/dev/kvm` is available; otherwise the virtualization check will provide remediation guidance (e.g., enabling VT-x/AMD-V or using a KVM-capable host).

## Applying Kubernetes manifests

After running the orchestrator setup, the rendered manifests are stored inside each workspace (for example `~/HostOS/hostos.yaml`). Apply them with `kubectl`:

```bash
kubectl apply -f "$HOME/HostOS/hostos.yaml"
kubectl apply -f "$HOME/SubOS/subos.yaml"
kubectl apply -f "$HOME/NanoOS/nanoos.yaml"
```

The manifests include persistent volume claims, workload ConfigMaps, resource requests/limits, and health probes. Each deployment exposes HTTP endpoints for liveness (`/healthz`) and readiness (`/readyz`). The corresponding services publish ports 1995 (HostOS dashboard), 8080 (SubOS microservices), and 8081 (NanoOS control loops).

## Firewall considerations

The orchestrators configure Uncomplicated Firewall (UFW) rules for the exposed ports. You can change the port numbers with the `--vnc-port` (HostOS) or `--service-port` (SubOS/NanoOS) options before applying the manifests.
