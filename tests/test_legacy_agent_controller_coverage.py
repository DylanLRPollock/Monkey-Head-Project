"""Cover the vendored legacy agent controller with small API fakes."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest


class _Context:
    def __init__(self, cmds=None):
        self.cmds = list(cmds or [])
        self.internal = False
        self.first = False
        self.input_name = "user"
        self.output_name = "assistant"
        self.extra_ctx = None


class _ReplyContext:
    AGENT_CONTINUE = "agent-continue"

    def __init__(self):
        self.type = None
        self.ctx = None
        self.input = None


class _KernelEvent:
    AGENT_CONTINUE = "agent-continue"

    def __init__(self, event_type, data):
        self.event_type = event_type
        self.data = data


class _BridgeContext:
    pass


class _CheckBox:
    def __init__(self):
        self.checked = None

    def setChecked(self, value):
        self.checked = value


def _install_vendor_fakes(monkeypatch):
    packages = (
        "pygpt_net",
        "pygpt_net.core",
        "pygpt_net.core.ctx",
        "pygpt_net.item",
    )
    for name in packages:
        package = types.ModuleType(name)
        package.__path__ = []
        monkeypatch.setitem(sys.modules, name, package)

    modules = {
        "pygpt_net.core.bridge": {"BridgeContext": _BridgeContext},
        "pygpt_net.core.ctx.reply": {"ReplyContext": _ReplyContext},
        "pygpt_net.core.events": {"KernelEvent": _KernelEvent},
        "pygpt_net.core.types": {
            "MODE_AGENT": "agent",
            "MODE_AGENT_LLAMA": "agent-llama",
        },
        "pygpt_net.item.ctx": {"CtxItem": _Context},
        "pygpt_net.utils": {"trans": lambda value: f"translated:{value}"},
    }
    for name, attributes in modules.items():
        module = types.ModuleType(name)
        for key, value in attributes.items():
            setattr(module, key, value)
        monkeypatch.setitem(sys.modules, name, module)


def _make_window():
    calls = {
        "hooks": [],
        "applied": [],
        "status": [],
        "toggled": 0,
        "locked": 0,
        "unlocked": 0,
        "idx": [],
        "events": [],
        "messages": [],
        "errors": [],
        "saved": 0,
        "config_sets": [],
    }
    values = {
        "agent.auto_stop": True,
        "agent.continue.always": False,
        "agent.iterations": 2,
        "mode": "agent",
        "cmd": True,
        "agent.goal.notify": False,
    }
    boxes = {"agent.auto_stop": _CheckBox(), "agent.continue": _CheckBox()}

    class Config:
        def get(self, key):
            return values.get(key)

        def set(self, key, value):
            values[key] = value
            calls["config_sets"].append((key, value))

        def save(self):
            calls["saved"] += 1

    class Stack:
        def __init__(self):
            self.is_waiting = False

        def waiting(self):
            return self.is_waiting

        def lock(self):
            calls["locked"] += 1

    stack = Stack()
    prompt_values = {
        "agent.goal": "goal prompt",
        "agent.continue": "continue prompt",
        "agent.continue.always": "always continue",
    }
    plugins = SimpleNamespace(
        is_enabled=lambda _name: True,
        get_option=lambda *_args: 5,
        is_type_enabled=lambda _name: False,
    )
    legacy = SimpleNamespace()
    window = SimpleNamespace(
        core=SimpleNamespace(
            config=Config(),
            command=SimpleNamespace(is_native_enabled=lambda: False),
            prompt=SimpleNamespace(get=lambda key: prompt_values[key]),
            plugins=SimpleNamespace(get_option=lambda *_args: 5),
            debug=SimpleNamespace(error=lambda error: calls["errors"].append(error)),
        ),
        ui=SimpleNamespace(
            add_hook=lambda *args: calls["hooks"].append(args),
            config={"global": boxes},
            nodes={
                "status.agent": SimpleNamespace(
                    setText=lambda value: calls["status"].append(value)
                )
            },
            tray=SimpleNamespace(show_msg=lambda *args: calls["messages"].append(args)),
        ),
        controller=SimpleNamespace(
            config=SimpleNamespace(
                apply_value=lambda **kwargs: calls["applied"].append(kwargs)
            ),
            plugins=plugins,
            agent=SimpleNamespace(
                legacy=legacy,
                common=SimpleNamespace(
                    toggle_status=lambda: calls.__setitem__(
                        "toggled", calls["toggled"] + 1
                    )
                ),
            ),
            kernel=SimpleNamespace(stack=stack),
            chat=SimpleNamespace(
                common=SimpleNamespace(
                    unlock_input=lambda: calls.__setitem__(
                        "unlocked", calls["unlocked"] + 1
                    )
                )
            ),
            idx=SimpleNamespace(
                on_ctx_end=lambda **kwargs: calls["idx"].append(kwargs)
            ),
        ),
        update_status=lambda value: calls["status"].append(value),
        dispatch=lambda event: calls["events"].append(event),
    )
    return window, calls, values, boxes, stack, prompt_values, plugins


@pytest.fixture
def legacy(monkeypatch):
    _install_vendor_fakes(monkeypatch)
    source = (
        Path(__file__).parents[1]
        / "src"
        / "huey"
        / "connectors"
        / "pyhuey"
        / "controller"
        / "agent"
        / "legacy.py"
    )
    spec = importlib.util.spec_from_file_location(
        "huey.connectors.pyhuey.controller.agent.legacy", source
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    window, calls, values, boxes, stack, prompt_values, plugins = _make_window()
    controller = module.Legacy(window)
    window.controller.agent.legacy = controller
    return (
        module,
        controller,
        window,
        calls,
        values,
        boxes,
        stack,
        prompt_values,
        plugins,
    )


def test_setup_reload_and_status_updates(legacy):
    _module, agent, _window, calls, values, boxes, _stack, _prompts, _plugins = legacy
    agent.setup()
    assert calls["hooks"][0][0] == "update.global.agent.iterations"
    assert boxes["agent.auto_stop"].checked is True
    assert calls["applied"][0]["value"] == 2

    values["agent.auto_stop"] = False
    values["agent.continue.always"] = True
    agent.reload()
    assert boxes["agent.auto_stop"].checked is False
    assert boxes["agent.continue"].checked is True

    agent.iteration = 1
    agent.update()
    assert calls["status"][-1] == "1 / 2"
    values["mode"] = "chat"
    _plugins.is_type_enabled = lambda _name: True
    agent.update()
    assert calls["status"][-1] == "1 / 5"
    _plugins.is_enabled = lambda _name: False
    agent.update()
    assert calls["status"][-1] == "1 / -"
    values["mode"] = "agent"
    values["agent.iterations"] = 0
    agent.update()
    assert calls["status"][-1] == "1 / ∞"


def test_commands_prompt_input_and_user_send(legacy):
    _module, agent, window, calls, values, _boxes, _stack, _prompts, _plugins = legacy
    assert agent.get_functions()[0]["cmd"] == "goal_update"
    assert agent.on_system_prompt("base", " extra") == "base\n extra\n\ngoal prompt"
    window.core.command.is_native_enabled = lambda: True
    assert "STATUS UPDATE" in agent.on_system_prompt("base", None)
    assert agent.on_system_prompt("base", None, auto_stop=False) == "baseNone"
    assert agent.on_input_before("hello") == "user: hello"
    agent.is_user = False
    assert agent.on_input_before("hello") == "hello"

    agent.iteration = 4
    agent.prev_output = "old"
    agent.finished = True
    agent.stop = True
    agent.on_user_send("new")
    assert (
        agent.iteration,
        agent.prev_output,
        agent.is_user,
        agent.finished,
        agent.stop,
    ) == (
        0,
        None,
        True,
        False,
        False,
    )
    assert calls["toggled"] == 1
    assert values["mode"] == "agent"


def test_context_end_respects_stop_commands_experts_waiting_and_limits(legacy):
    _module, agent, _window, calls, values, _boxes, stack, _prompts, _plugins = legacy
    ctx = _Context()
    agent.stop = True
    agent.iteration = 3
    agent.prev_output = "clear"
    agent.on_ctx_end(ctx, iterations=5)
    assert agent.iteration == 0 and agent.prev_output is None and not agent.stop

    agent.on_ctx_end(_Context([{"cmd": "ordinary"}]), iterations=4)
    assert agent.iteration == 0
    agent.on_ctx_end(_Context([{"cmd": "expert_call"}]), iterations=4)
    assert agent.iteration == 1

    agent.prev_output = "continue"
    stack.is_waiting = True
    agent.on_ctx_end(ctx, iterations=4)
    assert calls["events"] == []
    stack.is_waiting = False
    agent.on_ctx_end(ctx, iterations=4)
    event = calls["events"][-1]
    assert event.data["context"].reply_context.input == "continue"

    agent.iteration = 2
    values["agent.goal.notify"] = True
    agent.on_ctx_end(ctx, iterations=2)
    assert agent.stop is True
    assert calls["idx"][-1] == {"ctx": None, "mode": "agent"}
    assert calls["messages"][-1][0] == "translated:notify.agent.stop.title"


def test_context_before_after_and_continue_precedence(legacy):
    _module, agent, _window, _calls, values, _boxes, _stack, _prompts, _plugins = legacy
    ctx = _Context()
    agent.on_ctx_before(ctx, reverse_roles=True)
    assert ctx.internal is True and ctx.first is True
    assert (ctx.input_name, ctx.output_name) == ("user", "assistant")
    agent.iteration = 1
    agent.on_ctx_before(ctx, reverse_roles=True)
    assert (ctx.input_name, ctx.output_name) == ("assistant", "user")

    agent.on_ctx_after(ctx)
    assert agent.prev_output == "continue prompt"
    values["agent.continue.always"] = True
    agent.on_ctx_after(ctx)
    assert agent.prev_output == "always continue"
    ctx.extra_ctx = "extra"
    agent.on_ctx_after(ctx)
    assert agent.prev_output == "extra"


def test_command_filter_status_notifications_and_error_handling(legacy):
    _module, agent, _window, calls, values, _boxes, _stack, _prompts, _plugins = legacy
    ctx = _Context()
    agent.on_cmd(ctx, [{"cmd": "goal_update", "params": {"status": "finished"}}])
    assert agent.finished is True

    values["agent.auto_stop"] = True
    values["agent.goal.notify"] = True
    agent.on_cmd(
        ctx,
        [
            {"cmd": "other", "params": {}},
            {"cmd": "goal_update", "params": {"status": "finished"}},
        ],
    )
    assert agent.finished is True
    assert agent.stop is True
    assert calls["messages"][-1][0] == "translated:notify.agent.goal.title"
    assert calls["status"][-1] == "translated:status.finished"

    values["agent.auto_stop"] = False
    finished_before = agent.finished
    agent.on_cmd(ctx, [{"cmd": "goal_update", "params": {"status": "pause"}}])
    assert agent.finished is finished_before
    values["agent.auto_stop"] = True
    agent.on_cmd(ctx, [{"cmd": "goal_update", "params": {"status": "pause"}}])
    assert agent.finished is True
    agent.on_cmd(ctx, [{"cmd": "goal_update", "params": {"status": "unknown"}}])
    assert not calls["errors"]

    agent.cmd(ctx, [{"cmd": "goal_update", "params": {}}])
    assert len(calls["errors"]) == 1


def test_inline_state_stop_and_update_hook(legacy):
    _module, agent, _window, calls, values, _boxes, _stack, _prompts, plugins = legacy
    plugins.is_type_enabled = lambda name: name == "agent"
    assert agent.is_inline() is True
    values["mode"] = "chat"
    assert agent.enabled() is True
    plugins.is_type_enabled = lambda _name: False
    assert agent.enabled() is False
    values["mode"] = "agent"
    assert agent.enabled() is True

    agent.iteration = 7
    agent.prev_output = "text"
    agent.finished = True
    agent.on_stop()
    assert agent.stop is True and agent.iteration == 0 and agent.prev_output is None
    assert calls["idx"] == []
    agent.on_stop(auto=True)
    assert calls["idx"][-1] == {"ctx": None, "mode": "agent"}

    agent.hook_update("agent.iterations", 2, "test")
    assert calls["saved"] == 0
    agent.hook_update("agent.iterations", "4", "test")
    assert calls["config_sets"][-1] == ("agent.iterations", 4)
    assert calls["saved"] == 1
    assert calls["status"][-1] == "0 / 4"
    agent.hook_update("agent.auto_stop", True, "test")
    assert calls["saved"] == 1
