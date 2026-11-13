"""HueyOS custom kernel build framework.

This package provides a reproducible, auditable toolchain for producing a
version-matched custom Debian-compatible HueyOS kernel, its matching header
packages, the proprietary NVIDIA R580 kernel modules built for the exact
``KERNELRELEASE``, a target-version initramfs, and the accompanying
verification and release manifests.

Import safety
-------------
Importing this package performs **no work**:

* no subprocess is launched,
* no file is read or written,
* no optional third-party module (``yaml``, ``numpy``, ``torch``, vendor
  tooling) is eagerly imported,
* no logger is configured and no handler is attached.

All optional dependencies are imported lazily by the submodules that require
them. See ``kernel/huey-linux/README.md`` for the architecture and the
never-automated operations list.
"""

from __future__ import annotations

# ``__version__`` is hardcoded rather than resolved through
# ``importlib.metadata.version(...)`` on purpose: the metadata lookup reads
# the filesystem and would violate the "import performs no work" contract.
# When the package is installed, ``pyproject.toml`` in the repository root
# carries the canonical distribution version; this constant identifies the
# ``huey.kernel_build`` subpackage specifically.
__version__ = "0.1.0"

__all__ = ["__version__"]
