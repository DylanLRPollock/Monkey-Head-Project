"""Direct coverage for small public data, safety, and media helpers."""

from __future__ import annotations

import importlib
import json

import pytest

from huey.ai.brain import HueyBrain
from huey.ai.neural_net import NeuralLayer, SimpleNeuralNetwork
from huey.ai.tokenizer import BasicTokenizer
from huey.ai.transformers import TransformerBlock
from huey.connectors.pyhuey import tool_manifest
from huey.data.loader import load_data, load_text
from huey.data.transformer import transform_records
from huey.data.validator import validate_required_fields, validate_schema
from huey.decision.context import DecisionContext
from huey.decision.multi_choice import ChoiceOption, choose_option
from huey.governance.compliance import ComplianceChecker
from huey.gui.safety import (
    SafetyPolicy,
    assert_action_allowed,
    default_safety_policy,
    is_dangerous_action,
    safety_banner,
)
from huey.hardware.actuators import ActuatorHub
from huey.hardware.cooling import CoolingController
from huey.hardware.gpio import GPIOController
from huey.hardware.legacy import LegacyHardwareBridge
from huey.hardware.optane import OptaneManager
from huey.hardware.power import PowerController
from huey.hardware.serial import SerialBus
from huey.network.messaging import MessageQueue
from huey.network.mqtt import MQTTClient, MQTTProfile
from huey.network.protocol import ProtocolEnvelope
from huey.network.websocket import WebSocketHub
from huey.os.cli.commands import system as system_cli

mkv_module = importlib.import_module("huey.media.convert_mkv_to_mp4")
gif_module = importlib.import_module("huey.media.convert_video_to_gif")
jpeg_module = importlib.import_module("huey.media.convert_png_to_jpeg")


def test_data_helpers_cover_file_and_mapping_inputs(tmp_path):
    source = tmp_path / "data.json"
    source.write_text('{"name": "huey"}', encoding="utf-8")
    assert load_text(source) == '{"name": "huey"}'
    assert load_data(source) == {"name": "huey"}
    assert load_data({"count": 1}) == {"count": 1}

    text = tmp_path / "notes.txt"
    text.write_text("hello", encoding="utf-8")
    assert load_data(text) == {"path": str(text), "text": "hello"}

    assert validate_required_fields(
        {"name": "Huey", "optional": ""}, ["name", "missing", "optional"]
    ) == ["missing", "optional"]
    assert validate_schema(
        {"name": "Huey", "age": "old"}, {"name": str, "age": int, "id": int}
    ) == {"age": "expected int, got str", "id": "missing"}
    assert transform_records(
        [{"name": "huey", "age": 3}], field_rules={"name": str.title}
    ) == [{"name": "Huey", "age": 3}]


def test_neural_network_and_transformer_helpers():
    assert NeuralLayer([1.0, 2.0], bias=1.0).activate([1.0]) > 0
    assert SimpleNeuralNetwork().forward([1.0]) == []
    network = SimpleNeuralNetwork([NeuralLayer([1.0])])
    assert len(network.forward([1.0, 2.0])) == 1

    block = TransformerBlock(tokenizer=BasicTokenizer())
    encoded = block.encode("Huey can learn")
    assert encoded["tokens"]
    assert block.summarize("Huey can learn", context="test").endswith("context=test")
    assert "salient=" in block.summarize("")


def test_brain_inference_and_learning_public_path():
    brain = HueyBrain()
    result = brain.think("Hello Huey", context={"goal": "greet"})
    assert result["prompt"] == "Hello Huey"
    assert "context=greet" in result["summary"]
    learned = brain.learn("prompt", "response", reward=1.0)
    assert learned["reward"] == 1.0
    assert brain.model_catalog()


def test_decision_and_compliance_helpers():
    context = DecisionContext(goal="select", signals={"confidence": 0.5})
    result = choose_option(
        context,
        [
            ChoiceOption("plain", 1.0),
            ChoiceOption("policy", 1.0, {"policy_boost": 0.5}),
        ],
    )
    assert result["winner"] == "policy"
    assert result["candidates"][0]["name"] == "policy"
    with pytest.raises(ValueError):
        choose_option(context, [])

    checker = ComplianceChecker()
    assert checker.check({"approved": True})["compliant"] is True
    assert checker.check({"approved": True, "violations": ["unsafe"]}) == {
        "compliant": False,
        "violation_count": 1,
        "rationale": "",
    }


def test_network_protocol_and_local_transport_helpers():
    envelope = ProtocolEnvelope("jobs", {"id": "1"}, {"trace": 5})
    decoded = ProtocolEnvelope.decode(envelope.encode())
    assert decoded.topic == "jobs"
    assert decoded.payload == {"id": "1"}
    assert decoded.headers == {"trace": "5"}

    queue = MessageQueue()
    assert queue.consume() is None
    queue.publish(envelope)
    assert queue.pending() == ["jobs"]
    assert queue.consume() == envelope

    mqtt = MQTTClient(MQTTProfile("localhost", topic_prefix="huey"))
    assert mqtt.publish("jobs", "ready")["topic"] == "huey/jobs"
    assert mqtt.snapshot() == {"huey/jobs": "ready"}
    hub = WebSocketHub()
    payload = {"status": "ok"}
    hub.publish("health", payload)
    payload["status"] = "changed"
    assert hub.history("health") == [{"status": "ok"}]
    assert hub.history("empty") == []


def test_hardware_simulation_helpers_and_legacy_profiles():
    cooling = CoolingController(target_celsius=50)
    assert cooling.adjust(current_celsius=100)["fan_percent"] == 90
    assert cooling.adjust(current_celsius=200)["fan_percent"] == 100
    assert cooling.adjust(current_celsius=-100)["fan_percent"] == 20

    gpio = GPIOController()
    assert gpio.read(1) is False
    assert gpio.write(1, 1) is True
    snapshot = gpio.snapshot()
    snapshot[2] = True
    assert gpio.read(2) is False

    optane = OptaneManager(capacity_gb=16)
    assert optane.allocate_tier("cache", 4)["remaining_gb"] == 12
    assert optane.snapshot()["tiers"] == {"cache": 4}
    power = PowerController(budget_watts=100)
    assert power.allocate("gpu", 60)["remaining"] == 40
    assert power.snapshot()["allocations"] == {"gpu": 60}

    serial = SerialBus()
    assert serial.receive("tty0") is None
    assert serial.send("tty0", "ping")["payload"] == "ping"
    assert serial.snapshot() == {"tty0": "ping"}
    assert LegacyHardwareBridge().profiles()[0] == {"system": "VIC-20", "bus": "IEC"}
    hub = ActuatorHub()
    assert hub.inventory() == []

    class Manager:
        def list_actuators(self):
            return [{"name": "test"}]

        def perform(self, name, operation, payload):
            return {"name": name, "operation": operation, "payload": payload}

    custom = ActuatorHub(Manager())
    assert custom.inventory() == [{"name": "test"}]
    assert custom.command("test", "move", {"degrees": 1})["result"]["payload"] == {
        "degrees": 1
    }


def test_system_check_cli_output_modes(monkeypatch, capsys):
    monkeypatch.setattr(
        "huey.os.system_checks.system_check", lambda: {"gpu": True, "audio": False}
    )
    parser = __import__("argparse").ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    system_cli.register_system_commands(subparsers)

    args = parser.parse_args(["system-check", "--json"])
    assert args.handler(args) == 0
    assert '"gpu": true' in capsys.readouterr().out
    args = parser.parse_args(["system-check", "--verbose"])
    assert args.handler(args) == 0
    output = capsys.readouterr().out
    assert "System check results:" in output
    assert "audio: WARN" in output

    args = parser.parse_args(["system-check"])
    assert args.handler(args) == 0
    assert "gpu: OK" in capsys.readouterr().out


def test_safety_policy_defaults_and_allow_list(monkeypatch):
    policy = default_safety_policy()
    assert policy.mock_only
    assert is_dangerous_action(" SHUTDOWN ")
    assert not is_dangerous_action("read_status")
    assert_action_allowed("read_status", policy)
    with pytest.raises(PermissionError):
        assert_action_allowed("shutdown", policy)
    from huey.gui import safety

    monkeypatch.setattr(
        safety, "DANGEROUS_ACTIONS", safety.DANGEROUS_ACTIONS | {"unmapped_action"}
    )
    with pytest.raises(PermissionError):
        assert_action_allowed("unmapped_action", SafetyPolicy())
    assert_action_allowed("shell_command", SafetyPolicy(allow_command_execution=True))
    banner = safety_banner()
    assert banner["mock_only"] is True
    assert "Read-only" in banner["summary"]


def test_tool_manifest_writes_and_cli_modes(tmp_path, capsys):
    manifest = tool_manifest.build_manifest()
    assert manifest["policy"]["blocks_arbitrary_shell"] is True
    assert len(manifest["tools"]) == 3
    assert manifest["tools"][-1]["deferred"] is True
    assert manifest["tools"][-1]["read_only"] is False

    output = tmp_path / "nested" / "manifest.json"
    assert tool_manifest.write_manifest(output) == manifest
    assert json.loads(output.read_text(encoding="utf-8")) == manifest
    with pytest.raises(FileExistsError):
        tool_manifest.write_manifest(output)
    tool_manifest.write_manifest(output, overwrite=True)
    assert tool_manifest.main(["--json"]) == 0
    assert json.loads(capsys.readouterr().out)["schema"] == manifest["schema"]
    assert tool_manifest.main(["--output", str(tmp_path / "cli.json")]) == 0
    assert "wrote:" in capsys.readouterr().out


def test_png_to_jpeg_converts_alpha_and_rgb_and_cli(tmp_path, monkeypatch):
    image_module = pytest.importorskip("PIL.Image")
    png = tmp_path / "source.png"
    image_module.new("RGBA", (2, 2), (10, 20, 30, 80)).save(png)
    output = tmp_path / "nested" / "result.jpg"
    assert jpeg_module.convert_png_to_jpeg(png, output, quality=75) == output.resolve()
    with image_module.open(output) as converted:
        assert converted.mode == "RGB"

    rgb = tmp_path / "rgb.png"
    image_module.new("RGB", (1, 1), (1, 2, 3)).save(rgb)
    assert jpeg_module.convert_png_to_jpeg(rgb, tmp_path / "rgb.jpg").is_file()
    with pytest.raises(FileNotFoundError):
        jpeg_module.convert_png_to_jpeg(tmp_path / "missing.png", output)
    monkeypatch.setattr(jpeg_module, "convert_png_to_jpeg", lambda *args: output)
    assert jpeg_module.main([str(png), str(output), "--quality", "80"]) == 0


@pytest.mark.parametrize(
    ("module", "function", "source_name", "target_name", "argv", "expected_args"),
    [
        (
            gif_module,
            "convert_video_to_gif",
            "movie.mp4",
            "movie.gif",
            ["movie.mp4", "movie.gif", "--fps", "12"],
            [
                "-i",
                "movie.mp4",
                "-vf",
                "fps=10,scale=320:-1:flags=lanczos",
                "movie.gif",
            ],
        ),
        (
            mkv_module,
            "convert_mkv_to_mp4",
            "movie.mkv",
            "movie.mp4",
            ["movie.mkv", "movie.mp4"],
            ["-i", "movie.mkv", "-c", "copy", "-map", "0", "movie.mp4"],
        ),
    ],
)
def test_ffmpeg_converter_arguments_and_cli(
    tmp_path,
    monkeypatch,
    module,
    function,
    source_name,
    target_name,
    argv,
    expected_args,
):
    source = tmp_path / source_name
    source.touch()
    target = tmp_path / "out" / target_name
    calls = []
    monkeypatch.setattr(module, "_ensure_source", lambda _path: source)
    monkeypatch.setattr(module, "_coerce_path", lambda _path: target)
    monkeypatch.setattr(
        module, "_run_ffmpeg", lambda args, **kw: calls.append((args, kw))
    )
    result = getattr(module, function)(source, target)
    assert result == target
    expected_args = [
        (
            str(source)
            if item == source_name
            else str(target) if item == target_name else item
        )
        for item in expected_args
    ]
    assert calls[-1][0] == expected_args
    assert calls[-1][1]["overwrite"] is True

    monkeypatch.setattr(module, function, lambda *args: target)
    assert module.main(argv) == 0
