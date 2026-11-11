"""Cover the vendored experts, common, and Llama agent controllers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "src" / "huey" / "connectors" / "pyhuey" / "controller" / "agent"


class _BridgeContext:
    pass


class _ReplyContext:
    EXPERT_CALL = "expert-call"

    def __init__(self):
        self.type = self.ctx = self.parent_id = self.input = None


class _Event:
    END = "end"
    AGENT_CALL = "agent-call"
    REQUEST_NEXT = "request-next"

    def __init__(self, event_type, data=None):
        self.event_type = event_type
        self.data = data


def _install_fakes(monkeypatch):
    for name in (
        "pygpt_net",
        "pygpt_net.core",
        "pygpt_net.core.bridge",
        "pygpt_net.core.ctx",
        "pygpt_net.item",
    ):
        package = ModuleType(name)
        package.__path__ = []
        monkeypatch.setitem(sys.modules, name, package)

    bridge = sys.modules["pygpt_net.core.bridge"]
    bridge.BridgeContext = _BridgeContext
    bridge_context = ModuleType("pygpt_net.core.bridge.context")
    bridge_context.BridgeContext = _BridgeContext
    monkeypatch.setitem(sys.modules, bridge_context.__name__, bridge_context)

    reply = ModuleType("pygpt_net.core.ctx.reply")
    reply.ReplyContext = _ReplyContext
    monkeypatch.setitem(sys.modules, reply.__name__, reply)

    events = ModuleType("pygpt_net.core.events")
    events.KernelEvent = _Event
    events.RenderEvent = _Event
    monkeypatch.setitem(sys.modules, events.__name__, events)

    types = ModuleType("pygpt_net.core.types")
    types.MODE_AGENT = "agent"
    types.MODE_EXPERT = "expert"
    monkeypatch.setitem(sys.modules, types.__name__, types)

    context_item = ModuleType("pygpt_net.item.ctx")
    context_item.CtxItem = object
    monkeypatch.setitem(sys.modules, context_item.__name__, context_item)

    utils = ModuleType("pygpt_net.utils")
    utils.trans = lambda key: f"translated:{key}"
    monkeypatch.setitem(sys.modules, utils.__name__, utils)


def _load(name):
    path = AGENT_DIR / f"{name}.py"
    module_name = f"huey.connectors.pyhuey.controller.agent.{name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_common_controller_toggles_config_and_status(monkeypatch):
    _install_fakes(monkeypatch)
    common_module = _load("common")
    calls = []
    values = {"agent.iterations": 0, "mode": "chat"}
    config = SimpleNamespace(
        get=lambda key: values.get(key),
        set=lambda key, value: calls.append((key, value)),
        save=lambda: calls.append("save"),
    )
    visible = []
    legacy = SimpleNamespace(is_inline=lambda: False)
    plugins = SimpleNamespace(is_enabled=lambda _name: False)
    window = SimpleNamespace(
        core=SimpleNamespace(
            config=config,
            plugins=SimpleNamespace(get_option=lambda *_args: 0),
        ),
        controller=SimpleNamespace(
            plugins=plugins, agent=SimpleNamespace(legacy=legacy)
        ),
        ui=SimpleNamespace(
            dialogs=SimpleNamespace(confirm=lambda **kwargs: calls.append(kwargs)),
            nodes={
                "status.agent": SimpleNamespace(
                    setVisible=lambda value: visible.append(value)
                )
            },
        ),
    )
    common = common_module.Common(window)

    common.toggle_auto_stop(True)
    common.toggle_auto_stop(False)
    common.toggle_continue(True)
    common.toggle_continue(False)
    common.toggle_loop(True)
    common.toggle_loop(False)
    assert calls.count("save") == 6
    assert common.is_infinity_loop("agent") is True
    assert common.is_infinity_loop("chat") is False
    plugins.is_enabled = lambda _name: True
    window.core.plugins.get_option = lambda *_args: 0
    assert common.is_infinity_loop("chat") is True
    common.display_infinity_loop_confirm()
    values["mode"] = "agent"
    common.toggle_status()
    legacy.is_inline = lambda: True
    common.toggle_status()
    values["mode"] = "chat"
    legacy.is_inline = lambda: False
    common.toggle_status()
    assert visible == [True, True, False]
    assert calls[-1] == {
        "type": "agent.infinity.run",
        "id": 0,
        "msg": "translated:agent.infinity.confirm.content",
    }


def test_experts_prompt_branches_and_multiple_mentions(monkeypatch):
    _install_fakes(monkeypatch)
    module = _load("experts")
    events, logs, replies, updates = [], [], [], []
    config_values = {"mode": "chat", "stream": True, "agent.auto_stop": False}
    agent_enabled = {"value": False}
    expert_enabled = {"value": False}
    legacy = SimpleNamespace(
        enabled=lambda: agent_enabled["value"],
        on_system_prompt=lambda prompt, **_kwargs: f"wrapped:{prompt}",
    )
    expert_store = SimpleNamespace(
        get_prompt=lambda: "expert prompt",
        extract_calls=lambda _ctx: {
            "alpha": "first",
            "unknown": "skip",
            "beta": "second",
        },
        exists=lambda identity: identity in {"alpha", "beta"},
        reply=lambda ctx: replies.append(ctx),
    )
    window = SimpleNamespace(
        core=SimpleNamespace(
            config=SimpleNamespace(get=lambda key: config_values.get(key)),
            prompt=SimpleNamespace(get=lambda _key: "agent prompt"),
            experts=expert_store,
            ctx=SimpleNamespace(update_item=lambda ctx: updates.append(ctx)),
            debug=SimpleNamespace(info=lambda message: logs.append(message)),
        ),
        controller=SimpleNamespace(
            plugins=SimpleNamespace(is_type_enabled=lambda _name: False),
            agent=SimpleNamespace(
                legacy=legacy,
                experts=SimpleNamespace(enabled=lambda: expert_enabled["value"]),
            ),
        ),
        dispatch=events.append,
    )
    experts = module.Experts(window)
    assert experts.enabled() is False
    window.core.config.get = lambda key: "expert" if key == "mode" else None
    assert experts.enabled() is True
    assert experts.append_prompts("chat", "base") == "base"

    agent_enabled["value"] = True
    expert_enabled["value"] = True
    assert (
        experts.append_prompts("agent", " base ")
        == "wrapped:agent prompt\n\n base \n\nexpert prompt"
    )
    expert_enabled["value"] = False
    assert experts.append_prompts("chat", "") == "agent prompt"
    assert experts.append_prompts("chat", None) == "agent prompt"
    expert_enabled["value"] = True
    agent_enabled["value"] = False
    assert experts.append_prompts("chat", "base") == "expert prompt"
    assert experts.append_prompts("chat", "base", parent_id="child") == "base"

    ctx = SimpleNamespace(meta={"id": 1}, sub_reply=True, reply=False, sub_calls=0)
    assert experts.handle(ctx) == 0
    assert updates == [ctx] and replies == [ctx]
    ctx.sub_reply = False
    ctx.reply = True
    assert experts.handle(ctx) == 0
    ctx.reply = False
    expert_enabled["value"] = False
    assert experts.handle(ctx) == 0
    expert_enabled["value"] = True
    expert_store.extract_calls = lambda _ctx: {}
    assert experts.handle(ctx) == 0
    expert_store.extract_calls = lambda _ctx: {"unknown": "skip"}
    assert experts.handle(ctx) == 0
    expert_store.extract_calls = lambda _ctx: {
        "alpha": "first",
        "unknown": "skip",
        "beta": "second",
    }
    assert experts.handle(ctx) == 2
    assert ctx.sub_calls == 2
    assert [event.event_type for event in events] == [
        "end",
        "end",
        "agent-call",
        "agent-call",
    ]
    assert "Expert not found: unknown" in logs
    experts.stop()
    assert experts.stopped() is True
    experts.unlock()
    assert experts.stopped() is False


def test_llama_controller_lifecycle_and_loop_guards(monkeypatch):
    _install_fakes(monkeypatch)
    module = _load("llama")
    calls, values, messages, events = (
        [],
        {
            "agent.llama.loop.enabled": False,
            "agent.llama.loop.score": 75,
            "agent.llama.max_eval": 2,
            "agent.goal.notify": False,
        },
        [],
        [],
    )
    checkbox = SimpleNamespace(
        setChecked=lambda value: calls.append(("checked", value))
    )
    config = SimpleNamespace(
        get=lambda key: values.get(key),
        set=lambda key, value: values.__setitem__(key, value),
        save=lambda: calls.append("saved"),
    )
    stopped = {"value": False}
    ctx = SimpleNamespace(meta=SimpleNamespace(id="meta"))
    window = SimpleNamespace(
        core=SimpleNamespace(
            config=config,
            ctx=SimpleNamespace(all=lambda **kwargs: [("history", kwargs)]),
        ),
        ui=SimpleNamespace(
            add_hook=lambda *args: calls.append(("hook", args)),
            config={"global": {"agent.llama.loop.enabled": checkbox}},
            nodes={
                "status.agent": SimpleNamespace(
                    setText=lambda value: calls.append(("status", value))
                )
            },
            tray=SimpleNamespace(show_msg=lambda *args: messages.append(args)),
        ),
        controller=SimpleNamespace(
            config=SimpleNamespace(
                apply_value=lambda **kwargs: calls.append(("apply", kwargs))
            ),
            kernel=SimpleNamespace(
                stopped=lambda: stopped["value"],
                stop=lambda: calls.append("stop"),
            ),
            agent=SimpleNamespace(
                common=SimpleNamespace(toggle_status=lambda: calls.append("toggle"))
            ),
        ),
        update_status=lambda value: calls.append(("update", value)),
        dispatch=events.append,
    )
    llama = module.Llama(window)
    llama.setup()
    assert checkbox.setChecked
    assert calls[0][0] == "hook"
    values["agent.llama.loop.enabled"] = True
    llama.reload()
    assert calls[-1][0] == "apply"
    llama.on_user_send("new input")
    assert llama.get_eval_step() == 0
    values["agent.goal.notify"] = False
    llama.on_end()
    values["agent.goal.notify"] = True
    llama.on_end()
    assert len(messages) == 1

    values["agent.llama.loop.enabled"] = False
    llama.eval_step = 2
    llama.on_finish(ctx)  # loop disabled
    values["agent.llama.loop.enabled"] = True
    stopped["value"] = True
    llama.on_finish(ctx)
    stopped["value"] = False
    llama.eval_step = 2
    llama.on_finish(ctx)  # max steps reached
    assert llama.get_eval_step() == 0
    values["agent.llama.max_eval"] = 0
    llama.on_finish(ctx)
    assert llama.get_eval_step() == 1
    assert events[-1].event_type == "request-next"
    assert events[-1].data["context"].history == [("history", {"meta_id": "meta"})]

    llama.on_stop()
    assert "stop" in calls
    llama.update()
    assert "toggle" in calls
    llama.hook_update("agent.llama.loop.score", 80, "test")
    assert values["agent.llama.loop.score"] == 80
    assert "saved" in calls
    llama.hook_update("agent.llama.loop.score", 80, "test")  # unchanged
    llama.hook_update("unrelated", 1, "test")
