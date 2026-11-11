"""Cover WSGI routing and FFmpeg readiness outcomes without host tools."""

from __future__ import annotations

import json
from types import SimpleNamespace

from huey import wsgi
from huey.media import ffmpeg_validator as validator


def test_wsgi_routes_health_kernel_routes_and_not_found(monkeypatch):
    kernel = SimpleNamespace(
        health_report=lambda: {"status": "ok"}, snapshot=lambda: {"kernel": "snapshot"}
    )
    bridge = SimpleNamespace(describe=lambda: [{"path": "/healthz"}])
    monkeypatch.setattr(
        wsgi, "_CONTEXT", SimpleNamespace(kernel=kernel, api_bridge=bridge)
    )

    for path, expected_status, expected in (
        ("/", "200 OK", {"status": "ok"}),
        ("/health", "200 OK", {"status": "ok"}),
        ("/healthz", "200 OK", {"status": "ok"}),
        ("/kernel", "200 OK", {"kernel": "snapshot"}),
        ("/routes", "200 OK", {"routes": [{"path": "/healthz"}]}),
        ("/missing", "404 Not Found", {"error": "not found", "path": "/missing"}),
    ):
        response = {}

        def start_response(status, headers, response=response):
            response["status"] = status
            response["headers"] = dict(headers)

        payload = wsgi.application({"PATH_INFO": path}, start_response)
        assert response["status"] == expected_status
        assert json.loads(payload[0]) == expected
        assert response["headers"]["Content-Type"] == "application/json"
        assert response["headers"]["Content-Length"] == str(len(payload[0]))


def test_ffmpeg_and_ffprobe_readiness_branches(monkeypatch):
    monkeypatch.setattr(
        validator.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"ffmpeg", "ffprobe"} else None,
    )

    def command_result(command, **_kwargs):
        if command[-1] == "-version":
            return SimpleNamespace(
                returncode=0, stdout=f"{command[0]} version 1.2\nmore"
            )
        return SimpleNamespace(
            returncode=0,
            stdout="loudnorm silencedetect showwavespic showspectrumpic",
        )

    monkeypatch.setattr(validator.subprocess, "run", command_result)
    assert validator._version_line("ffmpeg") == "ffmpeg version 1.2"
    assert validator.check_ffprobe()
    report = validator.validate_ffmpeg_environment()
    assert report.ready is True
    assert report.ffmpeg_version == "ffmpeg version 1.2"
    assert report.ffprobe_version == "ffprobe version 1.2"
    assert all(report.required_filters.values())

    monkeypatch.setattr(
        validator.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="ignored"),
    )
    assert validator._command_stdout(["ffmpeg"]) == ""


def test_ffmpeg_missing_tools_filters_and_cli_strict_mode(monkeypatch, capsys):
    monkeypatch.setattr(validator.shutil, "which", lambda _name: None)
    missing = validator.validate_ffmpeg_environment(required_filters=("loudnorm",))
    assert missing.available is False
    assert missing.ffprobe_available is False
    assert missing.ready is False
    assert "ffmpeg not found on PATH" in missing.errors
    assert "ffprobe not found on PATH" in missing.errors
    assert validator.validate_media_environment()["ready"] is False

    monkeypatch.setattr(
        validator,
        "check_ffmpeg",
        lambda **_kwargs: validator.FFmpegValidationReport(False, errors=["missing"]),
    )
    assert validator.main(["--strict"]) == 1
    assert "FFmpeg is unavailable." in capsys.readouterr().out
    assert validator.main(["--json"]) == 0
    assert json.loads(capsys.readouterr().out)["available"] is False


def test_ffmpeg_report_ready_property_precedence():
    assert validator.FFmpegValidationReport(False, v1_ready=True).ready is True
    assert validator.FFmpegValidationReport(True, ffprobe_available=None).ready is True
    assert (
        validator.FFmpegValidationReport(True, ffprobe_available=False).ready is False
    )
