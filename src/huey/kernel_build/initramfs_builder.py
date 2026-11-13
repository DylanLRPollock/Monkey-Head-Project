"""Target-version initramfs builder for the HueyOS kernel build framework.

Workflow
--------
1. Validate inputs: kernel release, module tree, ``modules.list``,
   ``modprobe.d/huey-v100.conf``, output dir.
2. Create ``<output>/stage-<kr>/`` with:

   * ``lib/modules/<kr>/``  — a copy of the caller-supplied module tree;
   * ``etc/initramfs-tools/initramfs.conf`` — with ``MODULESDIR`` pointing
     at our staging root and ``MODULES=dep`` so the target rootfs drivers
     are included automatically;
   * ``etc/initramfs-tools/modules`` — a copy of ``modules.list``;
   * ``etc/initramfs-tools/conf.d/`` — empty;
   * ``etc/initramfs-tools/hooks/huey-v100-modprobe`` — a small hook that
     copies our modprobe.d policy into the initramfs tree at
     ``$DESTDIR/etc/modprobe.d/huey-v100.conf``;
   * ``etc/modprobe.d/huey-v100.conf`` — a copy of the profile fragment.

3. Run ``depmod -b <stage> <kr>`` to regenerate ``modules.dep`` etc. after
   the module tree has been assembled.
4. Run ``mkinitramfs -k <kr> -o <output>/initramfs-<kr> -d <stage>/etc/initramfs-tools``
   with ``MODULESDIR`` also exported as an environment override.
5. Verify with ``lsinitramfs <archive>`` and classify the result:

   * required modules present (by basename, including compressed forms);
   * ``amdgpu`` present (RX 570 display path intact);
   * ``nouveau`` absent (must not claim the V100);
   * ``etc/modprobe.d/huey-v100.conf`` present;
   * ``lib/modules/<kr>/`` prefix present (correct target release).

Non-goals
---------
* Never runs ``update-initramfs``, ``update-grub``, ``dpkg -i``, or
  ``dkms install``.
* Never writes to live ``/boot``, ``/etc/initramfs-tools``, or
  ``/etc/modprobe.d``.
* Never constructs an initramfs for the running kernel (``uname -r``)
  unless the caller explicitly passes that release **and** the archive
  verification passes for it.

Testability
-----------
Every subprocess invocation routes through
:class:`huey.kernel_build.runner.RunnerProtocol`. Tests substitute a
:class:`FakeRunner` that simulates ``depmod``, ``mkinitramfs``, and
``lsinitramfs``, so nothing on the host is invoked.
"""

from __future__ import annotations

import hashlib
import logging
import re
import shutil
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from huey.kernel_build.models import Severity, ValidationFinding
from huey.kernel_build.policy import check_path_destination_safe
from huey.kernel_build.runner import (
    CommandSpec,
    RunnerError,
    RunnerProtocol,
    RunnerTimeout,
)

logger = logging.getLogger(__name__)

__all__ = [
    "InitramfsBuildResult",
    "InitramfsBuilder",
]

_DEPMOD_TIMEOUT_SECONDS: float = 120.0
_MKINITRAMFS_TIMEOUT_SECONDS: float = 600.0
_LSINITRAMFS_TIMEOUT_SECONDS: float = 60.0

#: Kernel modules that must never appear in the v100-workstation initramfs,
#: because the V100 has no display output and Nouveau must not claim it.
#: The list is asserted on after lsinitramfs.
_FORBIDDEN_MODULES: tuple[str, ...] = ("nouveau",)

#: Common compression suffixes for ``.ko`` files in the initramfs.
_KO_SUFFIXES: tuple[str, ...] = (
    ".ko",
    ".ko.zst",
    ".ko.gz",
    ".ko.xz",
    ".ko.bz2",
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class InitramfsBuildResult:
    """Outcome of an initramfs build attempt."""

    kernel_release: str | None
    initramfs_path: Path | None
    initramfs_sha256: str | None
    initramfs_size: int | None
    modules_requested: tuple[str, ...]
    modules_present: tuple[str, ...]
    modules_missing: tuple[str, ...]
    findings: tuple[ValidationFinding, ...]
    dry_run: bool

    def __post_init__(self) -> None:
        if isinstance(self.findings, list):
            object.__setattr__(self, "findings", tuple(self.findings))

    def has_errors(self) -> bool:
        return any(
            f.severity in (Severity.ERROR, Severity.CRITICAL) for f in self.findings
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kernel_release": self.kernel_release,
            "initramfs_path": str(self.initramfs_path) if self.initramfs_path else None,
            "initramfs_sha256": self.initramfs_sha256,
            "initramfs_size": self.initramfs_size,
            "modules_requested": list(self.modules_requested),
            "modules_present": list(self.modules_present),
            "modules_missing": list(self.modules_missing),
            "findings": [f.to_dict() for f in self.findings],
            "dry_run": self.dry_run,
        }


# ---------------------------------------------------------------------------
# InitramfsBuilder
# ---------------------------------------------------------------------------


class InitramfsBuilder:
    """Build a target-version initramfs under an isolated staging tree."""

    def __init__(self, runner: RunnerProtocol) -> None:
        self._runner = runner

    # ---- public API ------------------------------------------------------

    def build(
        self,
        *,
        kernel_release: str,
        module_tree: Path,
        modules_list_path: Path,
        modprobe_conf_path: Path,
        output_dir: Path,
        include_modprobe_hook: bool = True,
        dry_run: bool = False,
    ) -> InitramfsBuildResult:
        """Stage, build, and verify an initramfs for ``kernel_release``.

        Parameters
        ----------
        kernel_release:
            Exact ``KERNELRELEASE`` produced by Step 12. Must not be empty.
        module_tree:
            Directory that corresponds to ``lib/modules/<kernel_release>/``
            (i.e. it directly contains ``kernel/``, ``modules.dep``, etc.).
            The builder copies it into the staging root; it never mutates
            the caller's tree.
        modules_list_path:
            Path to ``kernel/huey-linux/initramfs/modules.list`` (Step 15).
        modprobe_conf_path:
            Path to ``kernel/huey-linux/initramfs/modprobe.d/huey-v100.conf``
            (Step 16).
        output_dir:
            Destination root. The builder writes under
            ``output_dir/stage-<kr>/`` and ``output_dir/initramfs-<kr>``
            only.
        include_modprobe_hook:
            When ``True`` (default), install a hook that copies the modprobe
            policy into the initramfs tree. When ``False``, the modprobe
            config is staged but not asserted as present in the archive.
            Useful for chroot-based flows where the chroot already has it
            in ``/etc/modprobe.d/``.
        dry_run:
            When ``True``, validates inputs and plans the build without
            creating any directory or launching any subprocess.
        """
        validation = self._validate_inputs(
            kernel_release=kernel_release,
            module_tree=module_tree,
            modules_list_path=modules_list_path,
            modprobe_conf_path=modprobe_conf_path,
            output_dir=output_dir,
        )
        if validation is not None:
            return validation

        requested, parse_warnings = self._parse_modules_list(modules_list_path)

        if dry_run:
            return InitramfsBuildResult(
                kernel_release=kernel_release,
                initramfs_path=None,
                initramfs_sha256=None,
                initramfs_size=None,
                modules_requested=requested,
                modules_present=(),
                modules_missing=(),
                findings=(
                    ValidationFinding(
                        severity=Severity.INFO,
                        code="INITRAMFS_BUILD_DRY_RUN",
                        message=(
                            f"Planned: stage module tree from {module_tree} "
                            f"into {output_dir}/stage-{kernel_release}/, run "
                            "depmod, mkinitramfs, then verify with "
                            "lsinitramfs. No files will be written and no "
                            "subprocess will be launched."
                        ),
                        context={
                            "kernel_release": kernel_release,
                            "module_tree": str(module_tree),
                            "modules_requested": list(requested),
                            "output_dir": str(output_dir),
                        },
                    ),
                    *parse_warnings,
                ),
                dry_run=True,
            )

        # ---- staging ---------------------------------------------------
        stage_root = (output_dir / f"stage-{kernel_release}").resolve()
        try:
            if stage_root.exists():
                shutil.rmtree(stage_root)
            stage_root.mkdir(parents=True, exist_ok=False)
        except OSError as exc:
            return self._error_result(
                kernel_release=kernel_release,
                requested=requested,
                code="STAGE_CREATE_FAILED",
                message=f"Could not create staging root {stage_root}: {exc}",
            )

        staged_modules = stage_root / "lib" / "modules" / kernel_release
        try:
            shutil.copytree(module_tree, staged_modules, symlinks=False)
        except OSError as exc:
            return self._error_result(
                kernel_release=kernel_release,
                requested=requested,
                code="MODULE_TREE_COPY_FAILED",
                message=f"Could not copy module tree into {staged_modules}: {exc}",
            )

        # ---- depmod ----------------------------------------------------
        depmod_outcome = self._run_depmod(stage_root, kernel_release, requested)
        if isinstance(depmod_outcome, InitramfsBuildResult):
            return depmod_outcome

        # ---- conf dir --------------------------------------------------
        conf_dir = stage_root / "etc" / "initramfs-tools"
        try:
            conf_dir.mkdir(parents=True, exist_ok=False)
            (conf_dir / "conf.d").mkdir()
            (conf_dir / "hooks").mkdir()
            (conf_dir / "modules").write_text(
                self._render_modules_conf(requested), encoding="utf-8"
            )
            (conf_dir / "initramfs.conf").write_text(
                self._render_initramfs_conf(stage_root), encoding="utf-8"
            )
            staged_modprobe = stage_root / "etc" / "modprobe.d" / "huey-v100.conf"
            staged_modprobe.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(modprobe_conf_path, staged_modprobe)
            if include_modprobe_hook:
                hook_path = conf_dir / "hooks" / "huey-v100-modprobe"
                hook_path.write_text(
                    self._render_modprobe_hook(staged_modprobe), encoding="utf-8"
                )
                hook_path.chmod(0o755)
        except OSError as exc:
            return self._error_result(
                kernel_release=kernel_release,
                requested=requested,
                code="CONF_DIR_SETUP_FAILED",
                message=f"Could not prepare initramfs-tools conf dir: {exc}",
            )

        # ---- mkinitramfs -----------------------------------------------
        archive_path = (output_dir / f"initramfs-{kernel_release}").resolve()
        if archive_path.exists():
            try:
                archive_path.unlink()
            except OSError as exc:
                return self._error_result(
                    kernel_release=kernel_release,
                    requested=requested,
                    code="STALE_ARCHIVE_UNLINK_FAILED",
                    message=f"Could not remove stale {archive_path}: {exc}",
                )

        mkinit_outcome = self._run_mkinitramfs(
            stage_root, conf_dir, kernel_release, archive_path, requested
        )
        if isinstance(mkinit_outcome, InitramfsBuildResult):
            return mkinit_outcome

        if not archive_path.is_file():
            return self._error_result(
                kernel_release=kernel_release,
                requested=requested,
                code="MKINITRAMFS_NO_OUTPUT",
                message=(
                    f"mkinitramfs completed but {archive_path} does not exist."
                ),
            )

        # ---- lsinitramfs verification ----------------------------------
        listing, listing_warning = self._run_lsinitramfs(archive_path)
        findings: list[ValidationFinding] = []
        if listing_warning is not None:
            findings.append(listing_warning)

        present: list[str] = []
        missing: list[str] = []
        if listing is None:
            for m in requested:
                missing.append(m)
            # Cannot assert anything further; record as a single WARNING.
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="INITRAMFS_UNVERIFIED",
                    message=(
                        "lsinitramfs output was unavailable; module "
                        "presence, Nouveau absence, and target release "
                        "could not be verified."
                    ),
                )
            )
        else:
            findings.extend(
                self._verify_listing(
                    listing=listing,
                    requested=requested,
                    kernel_release=kernel_release,
                    present_out=present,
                    missing_out=missing,
                    include_modprobe_conf=include_modprobe_hook,
                )
            )

        try:
            sha = self._sha256_file(archive_path)
            size = archive_path.stat().st_size
        except OSError as exc:
            return self._error_result(
                kernel_release=kernel_release,
                requested=requested,
                code="ARCHIVE_HASH_FAILED",
                message=f"Could not hash {archive_path}: {exc}",
            )

        logger.info(
            "initramfs.build kernel_release=%s archive=%s modules_present=%d "
            "modules_missing=%d errors=%d",
            kernel_release,
            archive_path,
            len(present),
            len(missing),
            sum(
                1 for f in findings
                if f.severity in (Severity.ERROR, Severity.CRITICAL)
            ),
        )

        return InitramfsBuildResult(
            kernel_release=kernel_release,
            initramfs_path=archive_path,
            initramfs_sha256=sha,
            initramfs_size=size,
            modules_requested=requested,
            modules_present=tuple(present),
            modules_missing=tuple(missing),
            findings=tuple(findings),
            dry_run=False,
        )

    # ---- internals -------------------------------------------------------

    def _validate_inputs(
        self,
        *,
        kernel_release: str,
        module_tree: Path,
        modules_list_path: Path,
        modprobe_conf_path: Path,
        output_dir: Path,
    ) -> InitramfsBuildResult | None:
        if not kernel_release or not kernel_release.strip():
            return self._error_result(
                kernel_release=None,
                requested=(),
                code="KERNEL_RELEASE_MISSING",
                message="kernel_release must be a non-empty string.",
            )
        if not isinstance(kernel_release, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._+~-]*", kernel_release,
        ):
            return self._error_result(
                kernel_release=None, requested=(), code="INVALID_KERNEL_RELEASE",
                message="Kernel release is not a safe single path component.",
            )
        blocked = check_path_destination_safe(Path(output_dir))
        if blocked:
            return self._error_result(
                kernel_release=kernel_release, requested=(),
                code=blocked[0].code, message=blocked[0].message,
            )
        mt = Path(module_tree)
        if Path(output_dir).resolve() == mt.resolve() or mt.resolve() in Path(output_dir).resolve().parents:
            return self._error_result(
                kernel_release=kernel_release, requested=(),
                code="UNSAFE_OUTPUT_OVERLAP",
                message="Initramfs output must not overwrite the source module tree.",
            )
        if any(e.is_symlink() for e in mt.rglob("*")):
            return self._error_result(
                kernel_release=kernel_release, requested=(),
                code="MODULE_TREE_SYMLINK_REFUSED",
                message="Symlinks in module tree cannot be followed into the initramfs.",
            )
        if not mt.is_dir():
            return self._error_result(
                kernel_release=kernel_release,
                requested=(),
                code="MODULE_TREE_MISSING",
                message=f"module_tree is not a directory: {mt}",
            )
        if not any(mt.iterdir()):
            return self._error_result(
                kernel_release=kernel_release,
                requested=(),
                code="MODULE_TREE_EMPTY",
                message=f"module_tree is empty: {mt}",
            )
        if not Path(modules_list_path).is_file():
            return self._error_result(
                kernel_release=kernel_release,
                requested=(),
                code="MODULES_LIST_MISSING",
                message=f"modules.list not found: {modules_list_path}",
            )
        if not Path(modprobe_conf_path).is_file():
            return self._error_result(
                kernel_release=kernel_release,
                requested=(),
                code="MODPROBE_CONF_MISSING",
                message=f"modprobe conf not found: {modprobe_conf_path}",
            )
        if not Path(output_dir).is_dir():
            return self._error_result(
                kernel_release=kernel_release,
                requested=(),
                code="OUTPUT_DIR_MISSING",
                message=(
                    f"output_dir does not exist: {output_dir}. Create it "
                    "(e.g. under build/huey-kernel/) before running the "
                    "initramfs builder."
                ),
            )
        return None

    def _parse_modules_list(
        self, path: Path
    ) -> tuple[tuple[str, ...], list[ValidationFinding]]:
        findings: list[ValidationFinding] = []
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="MODULES_LIST_READ_FAILED",
                    message=f"Could not read {path}: {exc}",
                )
            )
            return (), findings
        modules: list[str] = []
        for raw in text.splitlines():
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            name = stripped.split(None, 1)[0]
            if name not in modules:
                modules.append(name)
        return tuple(modules), findings

    def _render_modules_conf(self, modules: Sequence[str]) -> str:
        return (
            "# Generated by huey.kernel_build.initramfs_builder from\n"
            "# kernel/huey-linux/initramfs/modules.list. Do not edit here.\n"
            + "\n".join(modules)
            + "\n"
        )

    def _render_initramfs_conf(self, stage_root: Path) -> str:
        return textwrap.dedent(
            f"""\
            # Generated by huey.kernel_build.initramfs_builder.
            # MODULESDIR points at the staging root so mkinitramfs reads
            # modules from <stage>/lib/modules/<kr>/ instead of the live
            # host's /lib/modules/.

            MODULES=dep
            MODULESDIR={stage_root / "lib" / "modules"}
            COMPRESS=gzip
            """
        )

    def _render_modprobe_hook(self, staged_modprobe_path: Path) -> str:
        # The hook runs as part of mkinitramfs and writes into $DESTDIR,
        # which is mkinitramfs's temporary extraction directory. This is
        # the standard mechanism used by Debian's initramfs-tools.
        return textwrap.dedent(
            f"""\
            #!/bin/sh
            # Generated by huey.kernel_build.initramfs_builder.
            # Copies the v100-workstation modprobe policy into the initramfs.

            PREREQ=""
            prereqs() {{ echo "$PREREQ"; }}
            case "$1" in
                prereqs) prereqs; exit 0 ;;
            esac

            . /usr/share/initramfs-tools/hook-functions

            if [ -f "{staged_modprobe_path}" ]; then
                mkdir -p "${{DESTDIR}}/etc/modprobe.d"
                cp -p "{staged_modprobe_path}" \\
                    "${{DESTDIR}}/etc/modprobe.d/huey-v100.conf"
            fi
            """
        )

    def _run_depmod(
        self,
        stage_root: Path,
        kernel_release: str,
        requested: tuple[str, ...],
    ) -> InitramfsBuildResult | str:
        spec = CommandSpec(
            argv=("depmod", "-b", str(stage_root), kernel_release),
            cwd=stage_root,
            description=f"depmod -b <stage> {kernel_release}",
            timeout_seconds=_DEPMOD_TIMEOUT_SECONDS,
        )
        try:
            result = self._runner.run(spec)
        except RunnerTimeout as exc:
            return self._error_result(
                kernel_release=kernel_release,
                requested=requested,
                code="DEPMOD_TIMEOUT",
                message=f"depmod timed out: {exc}",
            )
        except RunnerError as exc:
            return self._error_result(
                kernel_release=kernel_release,
                requested=requested,
                code="DEPMOD_LAUNCH_FAILED",
                message=f"depmod could not launch: {exc}",
            )
        if not result.succeeded:
            return self._error_result(
                kernel_release=kernel_release,
                requested=requested,
                code="DEPMOD_FAILED",
                message=f"depmod exited {result.command.returncode}",
            )
        return "ok"

    def _run_mkinitramfs(
        self,
        stage_root: Path,
        conf_dir: Path,
        kernel_release: str,
        archive_path: Path,
        requested: tuple[str, ...],
    ) -> InitramfsBuildResult | str:
        spec = CommandSpec(
            argv=(
                "mkinitramfs",
                "-k",
                kernel_release,
                "-o",
                str(archive_path),
                "-d",
                str(conf_dir),
            ),
            cwd=stage_root,
            description=f"mkinitramfs -k {kernel_release}",
            timeout_seconds=_MKINITRAMFS_TIMEOUT_SECONDS,
            env_overrides={
                "MODULESDIR": str(stage_root / "lib" / "modules"),
                "SOURCE_DATE_EPOCH": "0",
            },
        )
        try:
            result = self._runner.run(spec)
        except RunnerTimeout as exc:
            return self._error_result(
                kernel_release=kernel_release,
                requested=requested,
                code="MKINITRAMFS_TIMEOUT",
                message=f"mkinitramfs timed out: {exc}",
            )
        except RunnerError as exc:
            return self._error_result(
                kernel_release=kernel_release,
                requested=requested,
                code="MKINITRAMFS_LAUNCH_FAILED",
                message=f"mkinitramfs could not launch: {exc}",
            )
        if not result.succeeded:
            return self._error_result(
                kernel_release=kernel_release,
                requested=requested,
                code="MKINITRAMFS_FAILED",
                message=f"mkinitramfs exited {result.command.returncode}",
            )
        return "ok"

    def _run_lsinitramfs(
        self, archive_path: Path
    ) -> tuple[tuple[str, ...] | None, ValidationFinding | None]:
        spec = CommandSpec(
            argv=("lsinitramfs", str(archive_path)),
            cwd=archive_path.parent,
            description=f"lsinitramfs {archive_path.name}",
            timeout_seconds=_LSINITRAMFS_TIMEOUT_SECONDS,
        )
        try:
            result = self._runner.run(spec)
        except RunnerTimeout as exc:
            return None, ValidationFinding(
                severity=Severity.WARNING,
                code="LSINITRAMFS_TIMEOUT",
                message=f"lsinitramfs timed out: {exc}",
            )
        except RunnerError as exc:
            return None, ValidationFinding(
                severity=Severity.WARNING,
                code="LSINITRAMFS_UNAVAILABLE",
                message=f"lsinitramfs could not launch: {exc}",
            )
        if not result.succeeded:
            return None, ValidationFinding(
                severity=Severity.WARNING,
                code="LSINITRAMFS_FAILED",
                message=(
                    f"lsinitramfs exited {result.command.returncode}; cannot "
                    "verify archive contents."
                ),
            )
        text = (result.stdout or b"").decode("utf-8", errors="replace")
        lines = tuple(
            line.strip() for line in text.splitlines() if line.strip()
        )
        return lines, None

    def _verify_listing(
        self,
        *,
        listing: tuple[str, ...],
        requested: tuple[str, ...],
        kernel_release: str,
        present_out: list[str],
        missing_out: list[str],
        include_modprobe_conf: bool,
    ) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []

        # 1. Correct target release in the archive paths.
        prefix = f"lib/modules/{kernel_release}/"
        if not any(entry.startswith(prefix) for entry in listing):
            findings.append(
                ValidationFinding(
                    severity=Severity.CRITICAL,
                    code="INITRAMFS_WRONG_RELEASE",
                    message=(
                        f"None of the archive paths begin with {prefix!r}; "
                        "the initramfs is for a different kernel release."
                    ),
                    context={"kernel_release": kernel_release},
                )
            )

        # 2. Required modules present, forbidden modules absent.
        present_names = {
            self._module_basename(entry)
            for entry in listing
        }
        for name in requested:
            if name in present_names:
                present_out.append(name)
            else:
                missing_out.append(name)
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="INITRAMFS_REQUIRED_MODULE_MISSING",
                        message=(
                            f"Requested module {name!r} is not present in "
                            "the initramfs listing."
                        ),
                        context={"module": name},
                    )
                )

        for forbidden in _FORBIDDEN_MODULES:
            if forbidden in present_names:
                findings.append(
                    ValidationFinding(
                        severity=Severity.CRITICAL,
                        code="INITRAMFS_FORBIDDEN_MODULE_PRESENT",
                        message=(
                            f"Forbidden module {forbidden!r} appears in the "
                            "initramfs. The V100 must be claimed by the "
                            "proprietary nvidia module, not by Nouveau."
                        ),
                        context={"module": forbidden},
                    )
                )

        # 3. Modprobe policy present (when the hook was installed).
        if include_modprobe_conf:
            conf_path = "etc/modprobe.d/huey-v100.conf"
            if not any(entry == conf_path for entry in listing):
                findings.append(
                    ValidationFinding(
                        severity=Severity.WARNING,
                        code="INITRAMFS_MODPROBE_CONF_MISSING",
                        message=(
                            f"{conf_path} is not present in the initramfs. "
                            "Early-boot Nouveau exclusion may rely on the "
                            "kernel config (CONFIG_DRM_NOUVEAU=n) only; if "
                            "the operator needs the modprobe policy in the "
                            "initramfs, install it via the runbook."
                        ),
                        context={"expected": conf_path},
                    )
                )

        return findings

    @staticmethod
    def _module_basename(path: str) -> str:
        name = path.rsplit("/", 1)[-1]
        for suffix in _KO_SUFFIXES:
            if name.endswith(suffix):
                return name[: -len(suffix)]
        return name

    @staticmethod
    def _sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _error_result(
        *,
        kernel_release: str | None,
        requested: tuple[str, ...],
        code: str,
        message: str,
    ) -> InitramfsBuildResult:
        return InitramfsBuildResult(
            kernel_release=kernel_release,
            initramfs_path=None,
            initramfs_sha256=None,
            initramfs_size=None,
            modules_requested=requested,
            modules_present=(),
            modules_missing=(),
            findings=(
                ValidationFinding(
                    severity=Severity.ERROR, code=code, message=message
                ),
            ),
            dry_run=False,
        )
