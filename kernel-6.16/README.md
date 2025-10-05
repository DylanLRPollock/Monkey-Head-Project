# Linux 6.16.x Custom Kernel Builder

This directory provides automation to download, configure, and build a custom
Linux kernel from the upstream 6.16.x release series.  The tooling works on
Linux hosts as well as inside WSL, Docker, or other POSIX environments.  A
Python orchestrator script powers the workflow, while small shell and batch
wrappers make it easy to launch from different platforms.

## Prerequisites

1. Install the build dependencies.  On Ubuntu/Debian systems, run:

   ```bash
   sudo apt-get update
   sudo apt-get install build-essential bc bison flex libelf-dev libssl-dev \
       dwarves wget ca-certificates python3 python3-venv
   ```

   When using WSL on Windows, the same command works inside the Linux
   distribution.
2. Ensure you have at least 40 GB of free disk space and sufficient time –
   building a kernel can take 30 minutes or more depending on hardware.
3. (Optional) Review and modify [`configs/custom-kernel.config`](configs/custom-kernel.config)
   to enable or disable kernel features before the build.

## Usage

### Python entrypoint (recommended)

```bash
python3 kernel-6.16/scripts/build_kernel.py \
    --version 6.16.12 \
    --config kernel-6.16/configs/custom-kernel.config \
    --output kernel-6.16/artifacts
```

The script downloads the requested tarball from kernel.org, prepares the build
workspace under `kernel-6.16/worktrees/<version>`, applies the custom
configuration, and finally invokes `make bindeb-pkg` to emit Debian packages in
the specified output directory.

### Shell wrapper

```bash
./kernel-6.16/scripts/build_kernel.sh 6.16.12
```

By default the wrapper builds the kernel using the custom configuration and
stores artifacts under `kernel-6.16/artifacts`.  Pass `--help` to see additional
options forwarded to the Python script.

### Windows batch wrapper

From a Windows terminal running inside WSL (or a Linux environment mounted in
Windows) execute:

```cmd
kernel-6.16\scripts\build_kernel.bat 6.16.12
```

The batch script simply proxies arguments to the Python entrypoint.  When
launching the batch file from native Windows, make sure the repository is
available inside your WSL distribution so the kernel build runs on Linux.

## Output

After a successful run you will find Debian packages similar to the following
in the output directory:

- `linux-image-<version>_amd64.deb`
- `linux-headers-<version>_amd64.deb`
- `linux-libc-dev_<version>_amd64.deb`

You can install the packages using `sudo dpkg -i <package>.deb`.

## Cleaning up

Use the `--clean` flag to remove intermediate build artifacts for the selected
version.  Alternatively, delete the `kernel-6.16/worktrees/<version>` directory
and any `.deb` packages you no longer need.

## Extending the configuration

The configuration file ships with a handful of useful tweaks that demonstrate
how to customize the kernel (for example enabling BPF and overlayfs features).
Feel free to edit the file, or supply an entirely different `.config` via the
`--config` argument to match your requirements.
