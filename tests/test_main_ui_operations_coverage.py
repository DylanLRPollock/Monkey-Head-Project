"""Exercise the launcher's operator and media command dispatch paths."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from huey.memory.PY import main_ui
from huey.memory.PY.main_ui import MainUI


def _ui(*, confirmed=True):
    ui = MainUI.__new__(MainUI)
    ui.submitted = []
    ui.started = []
    ui.logs = []
    ui.statuses = []
    ui.confirmations = []
    ui.confirm_result = confirmed
    ui._confirm_container_operation = lambda action, destructive=False: (
        ui.confirmations.append((action, destructive)) or ui.confirm_result
    )
    ui._submit_task = lambda *args, **kwargs: ui.submitted.append((args, kwargs))
    ui._track_started = lambda *args, **kwargs: ui.started.append((args, kwargs))
    ui.log_message = ui.logs.append
    ui._set_status = ui.statuses.append
    ui._start_progress = lambda: ui.logs.append("progress started")
    ui._get_logs = lambda *args: None
    ui._convert_media_thread = lambda *args: None
    return ui


@pytest.mark.parametrize(
    ("method", "operation", "label", "role", "destructive"),
    [
        ("build_image", "build_docker_image", "Build Image", "operator", False),
        (
            "start_containers",
            "manage_containers",
            "Start Containers",
            "operator",
            False,
        ),
        ("stop_containers", "stop_containers", "Stop Containers", "admin", True),
        ("cleanup_images", "cleanup_images", "Cleanup Images", "admin", True),
        ("manage_volumes", "manage_volumes", "Manage Volumes", "reader", None),
        ("manage_networks", "manage_networks", "Manage Networks", "reader", None),
        ("deploy_kubernetes", "deploy_kubernetes", "Deploy", "operator", False),
        ("cleanup_kubernetes", "cleanup_kubernetes", "Cleanup", "admin", True),
    ],
)
def test_runtime_action_dispatch_uses_expected_role_and_confirmation(
    method, operation, label, role, destructive
):
    ui = _ui()

    getattr(MainUI, method)(ui)

    args, kwargs = ui.submitted[0]
    assert args[1] is getattr(main_ui, operation)
    assert args[2] == label
    assert kwargs["actor_role"] == role
    if destructive is not None:
        assert ui.confirmations == [
            (
                {
                    "build_image": "build the Docker image",
                    "start_containers": "start project containers",
                    "stop_containers": "stop project containers",
                    "cleanup_images": "prune Docker images",
                    "deploy_kubernetes": "apply Kubernetes resources",
                    "cleanup_kubernetes": "delete Kubernetes resources",
                }[method],
                destructive,
            )
        ]
        assert kwargs["confirmed"] is True
    else:
        assert ui.confirmations == []
        assert "confirmed" not in kwargs
    assert ui.statuses
    assert ui.started


@pytest.mark.parametrize(
    "method",
    [
        "build_image",
        "start_containers",
        "stop_containers",
        "cleanup_images",
        "deploy_kubernetes",
        "cleanup_kubernetes",
    ],
)
def test_confirmed_runtime_actions_stop_on_decline(method):
    ui = _ui(confirmed=False)

    getattr(MainUI, method)(ui)

    assert ui.submitted == []
    assert ui.started == []
    assert ui.statuses == []


def test_scale_deployment_handles_cancel_and_dispatch(monkeypatch):
    ui = _ui()
    calls = []
    prompts = iter(["", "demo", "demo"])
    replicas = iter([None, 3])
    monkeypatch.setattr(
        main_ui,
        "simpledialog",
        SimpleNamespace(
            askstring=lambda *_args: next(prompts),
            askinteger=lambda *_args: next(replicas),
        ),
    )

    MainUI.scale_deployment_prompt(ui)
    assert ui.confirmations == []
    MainUI.scale_deployment_prompt(ui)
    assert ui.confirmations == []

    ui._confirm_container_operation = lambda action, destructive=False: (
        calls.append((action, destructive)) or True
    )
    MainUI.scale_deployment_prompt(ui)
    args, kwargs = ui.submitted[-1]
    assert args[1] is main_ui.scale_deployment
    assert args[4:] == ("demo", 3)
    assert kwargs == {"confirmed": True, "actor_role": "operator"}
    assert calls == [("scale deployment demo to 3 replicas", False)]


def test_scale_deployment_stops_when_confirmation_is_declined(monkeypatch):
    ui = _ui(confirmed=False)
    monkeypatch.setattr(
        main_ui,
        "simpledialog",
        SimpleNamespace(askstring=lambda *_args: "demo", askinteger=lambda *_args: 2),
    )

    MainUI.scale_deployment_prompt(ui)

    assert ui.confirmations == [("scale deployment demo to 2 replicas", False)]
    assert ui.submitted == []


def test_get_pod_logs_prompt_handles_cancel_and_dispatch(monkeypatch):
    ui = _ui()
    answers = iter([None, "pod-a"])
    monkeypatch.setattr(
        main_ui,
        "simpledialog",
        SimpleNamespace(askstring=lambda *_args: next(answers)),
    )

    MainUI.get_pod_logs_prompt(ui)
    assert ui.submitted == []
    MainUI.get_pod_logs_prompt(ui)

    args, kwargs = ui.submitted[0]
    assert args == (ui._get_logs, "pod-a", "Get Pod Logs", "kubernetes")
    assert kwargs == {}


@pytest.mark.parametrize(
    ("source", "destination", "expected_calls"),
    [
        ("", "", 0),
        ("input.wav", "", 0),
        ("input.wav", "output.mp3", 1),
    ],
)
def test_convert_media_prompt_collects_paths_and_dispatches(
    monkeypatch, source, destination, expected_calls
):
    ui = _ui()
    monkeypatch.setattr(
        main_ui,
        "filedialog",
        SimpleNamespace(
            askopenfilename=lambda **_kwargs: source,
            asksaveasfilename=lambda **_kwargs: destination,
        ),
    )
    monkeypatch.setattr(
        main_ui,
        "simpledialog",
        SimpleNamespace(askstring=lambda *_args, **_kwargs: "128k"),
    )

    MainUI.convert_media_prompt(ui)

    assert len(ui.submitted) == expected_calls
    if expected_calls:
        args, kwargs = ui.submitted[0]
        assert args == (
            ui._convert_media_thread,
            source,
            destination,
            "128k",
            "128k",
            "media",
        )
        assert kwargs == {}
        assert ui.started


def test_convert_media_prompt_reports_missing_gui(monkeypatch):
    ui = _ui()
    errors = []
    monkeypatch.setattr(main_ui, "filedialog", None)
    monkeypatch.setattr(
        main_ui,
        "messagebox",
        SimpleNamespace(showerror=lambda *args: errors.append(args)),
    )

    MainUI.convert_media_prompt(ui)

    assert errors == [("Error", "Tkinter is not available")]
    assert ui.submitted == []
