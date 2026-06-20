from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
AUTOMATION_ROOT = SCRIPTS_ROOT / "automation"
MEMORY_ROOT = REPO_ROOT / "src" / "huey" / "memory"


def _file_names(directory: Path) -> set[str]:
    return {path.name for path in directory.iterdir() if path.is_file()}


def test_script_layout_has_structured_domains() -> None:
    assert (SCRIPTS_ROOT / "repo").is_dir()
    assert (SCRIPTS_ROOT / "media").is_dir()
    assert (SCRIPTS_ROOT / "security").is_dir()
    assert (AUTOMATION_ROOT / "py").is_dir()
    assert (AUTOMATION_ROOT / "sh").is_dir()
    assert (AUTOMATION_ROOT / "bat").is_dir()
    assert (AUTOMATION_ROOT / "ps1").is_dir()


def test_legacy_flat_script_paths_still_exist() -> None:
    expected = {
        "check_canon_terms.py",
        "check_dependency_sync.py",
        "check_inter_program_connectivity.py",
        "check_legacy_hueyos_imports.py",
        "check_repo_drift.py",
        "check_stale_platform_strings.py",
        "convert_avi_to_mkv.py",
        "decompress_audio_to_flac.py",
        "repackage_files.py",
        "security_check.sh",
    }
    assert expected.issubset(_file_names(SCRIPTS_ROOT))


def test_memory_shell_wrappers_cover_preserved_shell_scripts() -> None:
    memory_scripts = _file_names(MEMORY_ROOT / "SH")
    wrapper_scripts = _file_names(AUTOMATION_ROOT / "sh") - {"_dispatch.sh"}
    assert wrapper_scripts == memory_scripts


def test_memory_batch_wrappers_cover_preserved_batch_scripts() -> None:
    memory_scripts = _file_names(MEMORY_ROOT / "BAT")
    wrapper_scripts = _file_names(AUTOMATION_ROOT / "bat") - {"_dispatch.bat"}
    assert wrapper_scripts == memory_scripts


def test_memory_powershell_wrappers_cover_preserved_powershell_scripts() -> None:
    memory_scripts = _file_names(MEMORY_ROOT / "PS1")
    wrapper_scripts = _file_names(AUTOMATION_ROOT / "ps1") - {"_dispatch.ps1"}
    assert wrapper_scripts == memory_scripts


def test_memory_python_surface_exposes_curated_entrypoints() -> None:
    wrappers = _file_names(AUTOMATION_ROOT / "py")
    expected = {
        "_dispatch.py",
        "api.py",
        "check_inter_program_connectivity.py",
        "cli.py",
        "convert_mkv_to_mp4.py",
        "convert_pdf_to_text.py",
        "convert_png_to_jpeg.py",
        "convert_video_to_gif.py",
        "environment_setup.py",
        "installer.py",
        "launcher.py",
        "main.py",
        "media_conversion.py",
        "repair.py",
        "run-memory.py",
        "run.py",
        "startup.py",
        "sync_pygpt_structure.py",
        "uninstaller.py",
        "updates.py",
    }
    assert expected.issubset(wrappers)

    for script_name in expected - {"_dispatch.py", "run-memory.py"}:
        assert (MEMORY_ROOT / "PY" / script_name).is_file()
