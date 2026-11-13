"""Effective kernel .config builder for the HueyOS kernel build framework.

The builder:

1. Validates the kernel source tree (needs ``Makefile`` and
   ``scripts/kconfig/merge_config.sh``).
2. Validates each config fragment: exists, is small enough to plausibly be a
   fragment rather than a complete ``.config``.
3. Removes any stale ``.config`` in the output directory so the merge is
   deterministic across repeated runs.
4. Merges base + fragments via ``scripts/kconfig/merge_config.sh -m -O``
   using :class:`huey.kernel_build.runner.Runner`.
5. Resolves dependencies via ``make -C <source> O=<out> olddefconfig``.
6. Parses the resulting ``.config`` and produces a deterministic delta report
   (added / removed / changed / overrides) against the base config.
7. Validates critical symbols:
   - ``CONFIG_MODULES=y``
   - ``CONFIG_MODVERSIONS=y``
   - for the ``v100-workstation`` profile, ``CONFIG_DRM_NOUVEAU`` must not
     be ``y`` or ``m``.
8. Returns a :class:`ConfigBuildResult`; any blocking finding is recorded and
   a successful run's ``effective_config_path`` is still populated so the
   caller can inspect the offending config, but the caller must not promote a
   build that has blocking findings.

Dry run is fully non-destructive: no directory is created, no subprocess is
launched, no file is written.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

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
    "ConfigBuildResult",
    "ConfigBuilder",
    "ConfigDelta",
    "ConfigOverride",
    "ParsedConfig",
]

_CONFIG_LINE_RE = re.compile(r"^(CONFIG_[A-Za-z0-9_]+)=(.+)$")
_UNSET_RE = re.compile(r"^#\s*(CONFIG_[A-Za-z0-9_]+) is not set$")
_OVERRIDE_WARN_RE = re.compile(
    r"^Value of (CONFIG_[A-Za-z0-9_]+) is redefined by fragment (.+)$"
)

#: Hard upper bound for a fragment. Debian's base .config is ~9000+ lines; a
#: file above this threshold is treated as a complete config, not a fragment.
_MAX_FRAGMENT_LINES: int = 1000

#: Profile names that carry additional validation.
_PROFILE_V100_WORKSTATION = "v100-workstation"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ParsedConfig:
    """Parsed .config as ``symbol -> value``, with ``None`` meaning unset."""

    symbols: dict[str, str | None]

    @property
    def set_symbols(self) -> dict[str, str]:
        return {k: v for k, v in self.symbols.items() if v is not None}

    def get(self, name: str, default: str | None = None) -> str | None:
        return self.symbols.get(name, default)

    def is_set(self, name: str) -> bool:
        return self.symbols.get(name) is not None


@dataclass(frozen=True, slots=True)
class ConfigOverride:
    """A symbol redefined by a later fragment during merge."""

    symbol: str
    fragment: str
    previous_value: str | None = None
    new_value: str | None = None


@dataclass(frozen=True, slots=True)
class ConfigDelta:
    """Difference between base config and effective config."""

    added: tuple[tuple[str, str], ...]  # (symbol, value), set in effective only
    removed: tuple[tuple[str, str], ...]  # (symbol, value), set in base only
    changed: tuple[tuple[str, str, str], ...]  # (symbol, before, after)


@dataclass(frozen=True, slots=True)
class ConfigBuildResult:
    """Result of :meth:`ConfigBuilder.build`."""

    effective_config_path: Path | None
    delta_report_path: Path | None
    effective_config: ParsedConfig | None
    base_config: ParsedConfig | None
    delta: ConfigDelta
    overrides: tuple[ConfigOverride, ...]
    findings: tuple[ValidationFinding, ...]
    dry_run: bool

    def has_errors(self) -> bool:
        return any(
            f.severity in (Severity.ERROR, Severity.CRITICAL) for f in self.findings
        )


# ---------------------------------------------------------------------------
# ConfigBuilder
# ---------------------------------------------------------------------------


class ConfigBuilder:
    """Build the effective kernel .config from base config + fragments."""

    def __init__(self, runner: RunnerProtocol) -> None:
        self._runner = runner

    # ---- public API ------------------------------------------------------

    def build(
        self,
        source_dir: Path,
        base_config_path: Path,
        fragments: Sequence[Path],
        output_dir: Path,
        *,
        profile: str,
        dry_run: bool = False,
        workspace_root: Path | None = None,
    ) -> ConfigBuildResult:
        """Build the effective kernel .config.

        Parameters
        ----------
        source_dir:
            Extracted kernel source tree. Must contain ``Makefile`` and
            ``scripts/kconfig/merge_config.sh``.
        base_config_path:
            A known-good Debian base config (for example a saved
            ``/boot/config-*`` file).
        fragments:
            Ordered fragments to merge on top of the base config. Later
            fragments win. The base config is always applied first regardless
            of what is passed here.
        output_dir:
            Destination for ``.config`` and ``config-delta.txt``. Protected
            system paths and symlink escapes are always rejected.
        workspace_root:
            Optional mandatory boundary for output destinations. When supplied,
            the effective output directory must resolve within this root.
            Higher-level callers must supply their approved workspace root.
        profile:
            Target profile name; used for profile-specific validation.
        dry_run:
            When ``True``, no directory is created, no subprocess is invoked,
            and no file is written.
        """
        # Reject unsafe destinations before reading inputs or writing outputs.
        # A separate policy gate must approve any privileged host installation.
        output_dir = Path(output_dir)
        destination_findings = check_path_destination_safe(
            output_dir, workspace_root=workspace_root,
        )
        if destination_findings:
            return self._error_result(
                code=destination_findings[0].code,
                message=destination_findings[0].message,
            )
        # Match the path used by policy: a relative destination is rooted
        # under the explicitly approved workspace, not the caller's CWD.
        if workspace_root is not None and not output_dir.is_absolute():
            output_dir = Path(workspace_root) / output_dir
        output_resolved = output_dir.resolve(strict=False)

        # 1. Validate source tree.
        source_dir = Path(source_dir).resolve()
        merge_script = source_dir / "scripts" / "kconfig" / "merge_config.sh"
        if not (source_dir / "Makefile").is_file():
            return self._error_result(
                code="SOURCE_MISSING_MAKEFILE",
                message=f"Kernel source tree has no Makefile: {source_dir}",
            )
        if not merge_script.is_file():
            return self._error_result(
                code="SOURCE_MISSING_MERGE_SCRIPT",
                message=(
                    "Kernel source tree has no scripts/kconfig/merge_config.sh: "
                    f"{source_dir}"
                ),
            )
        # An out-of-tree build must not overwrite the pinned source tree.
        if output_resolved == source_dir or source_dir in output_resolved.parents:
            return self._error_result(
                code="OUTPUT_INSIDE_SOURCE_TREE",
                message="Kernel configuration output must not be inside the source tree.",
            )

        # 2. Validate base config.
        base_config_path = Path(base_config_path).resolve()
        if not base_config_path.is_file():
            return self._error_result(
                code="BASE_CONFIG_MISSING",
                message=f"Base kernel config missing: {base_config_path}",
            )

        # 3. Validate fragments.
        fragment_paths: list[Path] = []
        for frag in fragments:
            frag_path = Path(frag).resolve()
            if not frag_path.is_file():
                return self._error_result(
                    code="FRAGMENT_MISSING",
                    message=f"Config fragment missing: {frag_path}",
                )
            try:
                with frag_path.open("r", encoding="utf-8", errors="replace") as fh:
                    line_count = sum(1 for _ in fh)
            except OSError as exc:
                return self._error_result(
                    code="FRAGMENT_UNREADABLE",
                    message=f"Could not read fragment {frag_path}: {exc}",
                )
            if line_count > _MAX_FRAGMENT_LINES:
                return self._error_result(
                    code="FRAGMENT_TOO_LARGE",
                    message=(
                        f"Fragment {frag_path.name} has {line_count} lines, "
                        f"above the {_MAX_FRAGMENT_LINES}-line fragment "
                        "threshold. It looks like a complete .config; pass "
                        "only intentional deltas."
                    ),
                )
            fragment_paths.append(frag_path)

        # Input config files must never overlap either generated output file.
        output_files = {output_resolved / ".config", output_resolved / "config-delta.txt"}
        if base_config_path in output_files or any(f in output_files for f in fragment_paths):
            return self._error_result(
                code="OUTPUT_OVERWRITES_INPUT",
                message="Configuration output would overwrite a base or fragment input.",
            )

        # 4. Parse base config for later diff. An unreadable base is a blocker.
        try:
            base_config = self._parse_config_file(base_config_path)
        except OSError as exc:
            return self._error_result(
                code="BASE_CONFIG_UNREADABLE",
                message=f"Cannot parse base config {base_config_path}: {exc}",
            )

        # 5. Dry-run short circuit: no writes, no subprocesses.
        if dry_run:
            return ConfigBuildResult(
                effective_config_path=None,
                delta_report_path=None,
                effective_config=None,
                base_config=base_config,
                delta=ConfigDelta(added=(), removed=(), changed=()),
                overrides=(),
                findings=(
                    ValidationFinding(
                        severity=Severity.INFO,
                        code="CONFIG_BUILD_DRY_RUN",
                        message=(
                            f"Planned merge of {len(fragment_paths)} "
                            f"fragment(s) into {output_dir / '.config'} "
                            f"then 'make olddefconfig'."
                        ),
                        context={
                            "base_config": str(base_config_path),
                            "fragments": [str(p) for p in fragment_paths],
                            "source_dir": str(source_dir),
                            "output_dir": str(output_dir),
                            "profile": profile,
                        },
                    ),
                ),
                dry_run=True,
            )

        # 6. Prepare output directory. Delete any stale .config so the merge
        #    seeds from the caller-supplied base config, not from a previous
        #    run's artifact.
        # Do not follow pre-existing symlinks to arbitrary external files.
        effective_path = output_dir / ".config"
        delta_path = output_dir / "config-delta.txt"
        if effective_path.is_symlink() or delta_path.is_symlink():
            return self._error_result(
                code="OUTPUT_SYMLINK_REFUSED",
                message="Refusing a symlinked kernel config or delta report.",
            )
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return self._error_result(
                code="OUTPUT_DIR_CREATE_FAILED",
                message=f"Could not create configuration output directory: {exc}",
            )
        if effective_path.exists():
            try:
                effective_path.unlink()
            except OSError as exc:
                return self._error_result(
                    code="OUTPUT_CONFIG_UNLINK_FAILED",
                    message=f"Could not remove stale {effective_path}: {exc}",
                )

        # 7. Merge configs via merge_config.sh.
        merge_argv = (
            str(merge_script),
            "-m",
            "-O",
            str(output_dir),
            str(base_config_path),
            *[str(p) for p in fragment_paths],
        )
        merge_spec = CommandSpec(
            argv=merge_argv,
            cwd=source_dir,
            description="merge_config.sh: base + fragments",
            timeout_seconds=120.0,
        )
        try:
            merge_result = self._runner.run(merge_spec)
        except RunnerTimeout as exc:
            return self._error_result(
                code="MERGE_CONFIG_TIMEOUT",
                message=f"merge_config.sh timed out: {exc}",
            )
        except RunnerError as exc:
            return self._error_result(
                code="MERGE_CONFIG_LAUNCH_FAILED",
                message=f"merge_config.sh could not launch: {exc}",
            )
        if not merge_result.succeeded:
            return self._error_result(
                code="MERGE_CONFIG_FAILED",
                message=(
                    f"merge_config.sh exited {merge_result.command.returncode}; "
                    "see capture for details."
                ),
            )

        # 8. Parse override warnings.
        combined_output = (
            (merge_result.stderr or b"") + b"\n" + (merge_result.stdout or b"")
        ).decode("utf-8", errors="replace")
        overrides = self._parse_override_warnings(combined_output)

        # 9. Resolve dependencies via make olddefconfig.
        make_argv = (
            "make",
            "-C",
            str(source_dir),
            f"O={output_dir.resolve()}",
            "olddefconfig",
        )
        make_spec = CommandSpec(
            argv=make_argv,
            cwd=source_dir,
            description="make olddefconfig",
            timeout_seconds=900.0,
            env_overrides={"SOURCE_DATE_EPOCH": "0"},
        )
        try:
            make_result = self._runner.run(make_spec)
        except RunnerTimeout as exc:
            return self._error_result(
                code="OLDDEFCONFIG_TIMEOUT",
                message=f"make olddefconfig timed out: {exc}",
            )
        except RunnerError as exc:
            return self._error_result(
                code="OLDDEFCONFIG_LAUNCH_FAILED",
                message=f"make olddefconfig could not launch: {exc}",
            )
        if not make_result.succeeded:
            return self._error_result(
                code="OLDDEFCONFIG_FAILED",
                message=(
                    f"make olddefconfig exited "
                    f"{make_result.command.returncode}"
                ),
            )

        # 10. Parse effective config.
        if not effective_path.is_file():
            return self._error_result(
                code="EFFECTIVE_CONFIG_MISSING",
                message=(
                    "olddefconfig finished but did not produce "
                    f"{effective_path}"
                ),
            )
        if effective_path.is_symlink() or delta_path.is_symlink():
            return self._error_result(
                code="OUTPUT_SYMLINK_REFUSED",
                message="Refusing symlinked output generated by kernel tools.",
            )
        try:
            effective_config = self._parse_config_file(effective_path)
        except OSError as exc:
            return self._error_result(
                code="EFFECTIVE_CONFIG_UNREADABLE",
                message=f"Cannot read effective config {effective_path}: {exc}",
            )

        # 11. Validate critical symbols.
        findings: list[ValidationFinding] = list(
            self._validate_critical_symbols(effective_config, profile)
        )

        # 12. Compute and persist delta.
        delta = self._compute_delta(base_config, effective_config)
        try:
            delta_path.write_text(
                self._render_delta_report(
                    base_config_path, effective_path, delta, overrides
                ),
                encoding="utf-8",
            )
        except OSError as exc:
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="DELTA_REPORT_WRITE_FAILED",
                    message=f"Could not write delta report {delta_path}: {exc}",
                )
            )

        logger.info(
            "config.build complete profile=%s fragments=%d "
            "added=%d removed=%d changed=%d overrides=%d",
            profile,
            len(fragment_paths),
            len(delta.added),
            len(delta.removed),
            len(delta.changed),
            len(overrides),
        )

        return ConfigBuildResult(
            effective_config_path=effective_path,
            delta_report_path=delta_path if delta_path.exists() else None,
            effective_config=effective_config,
            base_config=base_config,
            delta=delta,
            overrides=overrides,
            findings=tuple(findings),
            dry_run=False,
        )

    # ---- internals -------------------------------------------------------

    @staticmethod
    def _error_result(code: str, message: str) -> ConfigBuildResult:
        return ConfigBuildResult(
            effective_config_path=None,
            delta_report_path=None,
            effective_config=None,
            base_config=None,
            delta=ConfigDelta(added=(), removed=(), changed=()),
            overrides=(),
            findings=(
                ValidationFinding(
                    severity=Severity.ERROR, code=code, message=message
                ),
            ),
            dry_run=False,
        )

    def _parse_config_file(self, path: Path) -> ParsedConfig:
        symbols: dict[str, str | None] = {}
        text = path.read_text(encoding="utf-8", errors="replace")
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            m = _CONFIG_LINE_RE.match(line)
            if m:
                symbols[m.group(1)] = m.group(2)
                continue
            m = _UNSET_RE.match(line)
            if m:
                symbols[m.group(1)] = None
        return ParsedConfig(symbols=symbols)

    def _parse_override_warnings(
        self, text: str
    ) -> tuple[ConfigOverride, ...]:
        overrides: list[ConfigOverride] = []
        for raw in text.splitlines():
            m = _OVERRIDE_WARN_RE.match(raw.strip())
            if m:
                overrides.append(
                    ConfigOverride(
                        symbol=m.group(1), fragment=m.group(2).strip()
                    )
                )
        return tuple(overrides)

    def _compute_delta(
        self, base: ParsedConfig, effective: ParsedConfig
    ) -> ConfigDelta:
        base_set = base.set_symbols
        eff_set = effective.set_symbols

        added = tuple(
            sorted((k, v) for k, v in eff_set.items() if k not in base_set)
        )
        removed = tuple(
            sorted((k, v) for k, v in base_set.items() if k not in eff_set)
        )
        changed = tuple(
            sorted(
                (k, base_set[k], eff_set[k])
                for k in base_set
                if k in eff_set and base_set[k] != eff_set[k]
            )
        )
        return ConfigDelta(added=added, removed=removed, changed=changed)

    def _render_delta_report(
        self,
        base_path: Path,
        effective_path: Path,
        delta: ConfigDelta,
        overrides: tuple[ConfigOverride, ...],
    ) -> str:
        lines: list[str] = [
            "# HueyOS kernel config delta report",
            f"# Base config:      {base_path}",
            f"# Effective config: {effective_path}",
            "#",
            "# Note: 'removed' means set in the base config and not set in the",
            "# effective config (whether explicitly unset or dropped entirely).",
            "",
            f"# Overrides -- {len(overrides)}",
        ]
        if overrides:
            for ov in overrides:
                lines.append(f"  {ov.symbol}: redefined by {ov.fragment}")
        else:
            lines.append("  (none)")
        lines.append("")
        lines.append(f"# Added -- {len(delta.added)}")
        if delta.added:
            for sym, val in delta.added:
                lines.append(f"  + {sym}={val}")
        else:
            lines.append("  (none)")
        lines.append("")
        lines.append(f"# Removed -- {len(delta.removed)}")
        if delta.removed:
            for sym, val in delta.removed:
                lines.append(f"  - {sym}={val} -> (unset)")
        else:
            lines.append("  (none)")
        lines.append("")
        lines.append(f"# Changed -- {len(delta.changed)}")
        if delta.changed:
            for sym, before, after in delta.changed:
                lines.append(f"  ~ {sym}: {before} -> {after}")
        else:
            lines.append("  (none)")
        lines.append("")
        return "\n".join(lines)

    def _validate_critical_symbols(
        self, cfg: ParsedConfig, profile: str
    ) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []

        modules_val = cfg.get("CONFIG_MODULES")
        if modules_val != "y":
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="MODULES_NOT_ENABLED",
                    message=(
                        "CONFIG_MODULES=y is required; effective value is "
                        f"{'unset' if modules_val is None else repr(modules_val)}."
                    ),
                    context={"actual": modules_val},
                )
            )

        modversions_val = cfg.get("CONFIG_MODVERSIONS")
        if modversions_val != "y":
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="MODVERSIONS_NOT_ENABLED",
                    message=(
                        "CONFIG_MODVERSIONS=y is required for the proprietary "
                        "NVIDIA external module build; effective value is "
                        f"{'unset' if modversions_val is None else repr(modversions_val)}."
                    ),
                    context={"actual": modversions_val},
                )
            )

        if profile == _PROFILE_V100_WORKSTATION:
            amdgpu_val = cfg.get("CONFIG_DRM_AMDGPU")
            if amdgpu_val != "m":
                findings.append(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="AMDGPU_MODULE_REQUIRED",
                        message=(
                            "CONFIG_DRM_AMDGPU=m is required to preserve the "
                            "RX 570 display path in this workstation profile."
                        ),
                        context={"actual": amdgpu_val},
                    )
                )
            nouveau_val = cfg.get("CONFIG_DRM_NOUVEAU")
            if nouveau_val in ("y", "m"):
                findings.append(
                    ValidationFinding(
                        severity=Severity.CRITICAL,
                        code="NOUVEAU_FORCED_FOR_V100",
                        message=(
                            "CONFIG_DRM_NOUVEAU must not be enabled in the "
                            "v100-workstation profile: it would claim the "
                            f"Tesla V100. Effective value: CONFIG_DRM_NOUVEAU="
                            f"{nouveau_val}. Review the delta report to find "
                            "the overriding fragment."
                        ),
                        context={"actual": nouveau_val, "profile": profile},
                    )
                )

        return findings
