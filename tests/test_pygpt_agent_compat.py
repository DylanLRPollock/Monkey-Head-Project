"""Verify legacy PyGPT agent controllers with small protocol-compatible stubs."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def agent_modules(monkeypatch):
    names = (
        "pygpt_net",
        "pygpt_net.core",
        "pygpt_net.core.bridge",
        "pygpt_net.core.bridge.context",
        "pygpt_net.core.ctx",
        "pygpt_net.core.ctx.reply",
        "pygpt_net.core.events",
        "pygpt_net.core.types",
        "pygpt_net.item",
        "pygpt_net.item.ctx",
        "pygpt_net.utils",
    )
    modules = {name: types.ModuleType(name) for name in names}
    for name in names:
        if name in {
            "pygpt_net",
            "pygpt_net.core",
            "pygpt_net.core.ctx",
            "pygpt_net.item",
        }:
            modules[name].__path__ = []
        monkeypatch.setitem(sys.modules, name, modules[name])

    class Context:
        pass

    class ReplyContext:
        EXPERT_CALL = "expert-call"

    class KernelEvent:
        AGENT_CALL = "agent-call"
        REQUEST_NEXT = "request-next"

        def __init__(self, event_type, data):
            self.event_type = event_type
            self.data = data

    class RenderEvent:
        END = "end"

        def __init__(self, event_type, data):
            self.event_type = event_type
            self.data = data

    modules["pygpt_net.core.bridge"].BridgeContext = Context
    modules["pygpt_net.core.bridge.context"].BridgeContext = Context
    modules["pygpt_net.core.ctx.reply"].ReplyContext = ReplyContext
    modules["pygpt_net.core.events"].KernelEvent = KernelEvent
    modules["pygpt_net.core.events"].RenderEvent = RenderEvent
    modules["pygpt_net.core.types"].MODE_AGENT = "agent"
    modules["pygpt_net.core.types"].MODE_EXPERT = "expert"
    modules["pygpt_net.item.ctx"].CtxItem = type("CtxItem", (), {})
    modules["pygpt_net.utils"].trans = lambda key: f"translated:{key}"

    source_dir = (
        Path(__file__).resolve().parents[1]
        / "src/huey/connectors/pyhuey/controller/agent"
    )

    def load(name, filename):
        spec = importlib.util.spec_from_file_location(name, source_dir / filename)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
        return module

    experts = load("coverage_pygpt_experts", "experts.py")
    llama = load("coverage_pygpt_llama", "llama.py")
    common = load("coverage_pygpt_common", "common.py")
    return SimpleNamespace(
        experts=experts, llama=llama, common=common, reply_context=ReplyContext
    )


class _Config:
    def __init__(self, values=None):
        self.values = dict(values or {})
        self.saved = 0

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def save(self):
        self.saved += 1


def test_experts_stop_enabled_and_prompt_composition(agent_modules):
    expert_controller = agent_modules.experts.Experts()
    assert not expert_controller.stopped()
    expert_controller.stop()
    assert expert_controller.stopped()
    expert_controller.unlock()
    assert not expert_controller.stopped()

    config = _Config({"mode": "expert", "agent.auto_stop": True})
    window = SimpleNamespace(
        core=SimpleNamespace(
            config=config,
            prompt=SimpleNamespace(get=lambda _key: "agent base"),
            experts=SimpleNamespace(get_prompt=lambda: "expert base"),
        ),
        controller=SimpleNamespace(
            plugins=SimpleNamespace(is_type_enabled=lambda _kind: False),
            agent=SimpleNamespace(
                legacy=SimpleNamespace(
                    enabled=lambda: True,
                    on_system_prompt=lambda prompt, **_kwargs: f"wrapped:{prompt}",
                ),
                experts=SimpleNamespace(enabled=lambda: True),
            ),
        ),
    )
    expert_controller = agent_modules.experts.Experts(window)
    assert expert_controller.enabled()
    assert expert_controller.append_prompts("expert", "previous") == (
        "agent base\n\nprevious\n\nexpert base"
    )
    assert expert_controller.append_prompts("agent", "previous").startswith(
        "wrapped:agent base"
    )

    window.controller.agent.legacy.enabled = lambda: False
    assert expert_controller.append_prompts("chat", "previous") == "expert base"
    window.core.config.values["mode"] = "chat"
    window.controller.plugins.is_type_enabled = lambda _kind: True
    assert expert_controller.enabled()


def test_experts_handles_subreplies_missing_experts_and_calls(agent_modules):
    dispatched = []
    debug = []
    updated = []
    replied = []
    window = SimpleNamespace(
        core=SimpleNamespace(
            config=_Config({"stream": True}),
            ctx=SimpleNamespace(update_item=updated.append),
            experts=SimpleNamespace(
                reply=replied.append,
                extract_calls=lambda _ctx: {
                    "missing": "skip",
                    "specialist": "explain this",
                },
                exists=lambda expert_id: expert_id == "specialist",
            ),
            debug=SimpleNamespace(info=debug.append),
        ),
        controller=SimpleNamespace(
            agent=SimpleNamespace(
                experts=SimpleNamespace(enabled=lambda: True),
                legacy=SimpleNamespace(enabled=lambda: False),
            )
        ),
        dispatch=dispatched.append,
    )
    controller = agent_modules.experts.Experts(window)
    ctx = SimpleNamespace(sub_reply=True, reply=False, meta={}, sub_calls=0)
    assert controller.handle(ctx) == 0
    assert updated == [ctx] and replied == [ctx]

    ctx.sub_reply = False
    ctx.reply = True
    assert controller.handle(ctx) == 0

    ctx.reply = False
    assert controller.handle(ctx) == 1
    assert ctx.sub_calls == 1
    assert [event.event_type for event in dispatched] == ["end", "agent-call"]
    assert debug == [
        "Calling experts...",
        "Expert not found: missing",
        "Calling: specialist",
    ]
    call_context = dispatched[-1].data["context"]
    assert call_context.ctx is ctx
    assert call_context.reply_context.parent_id == "specialist"
    assert call_context.reply_context.input == "explain this"
    assert call_context.reply_context.type == agent_modules.reply_context.EXPERT_CALL

    window.controller.agent.experts.enabled = lambda: False
    assert controller.handle(ctx) == 0


def _llama_window(config_values):
    config = _Config(config_values)
    calls = SimpleNamespace(hooks=[], applied=[], statuses=[], events=[], stopped=False)
    checkbox = SimpleNamespace(
        setChecked=lambda value: setattr(calls, "checked", value)
    )
    window = SimpleNamespace(
        core=SimpleNamespace(
            config=config,
            ctx=SimpleNamespace(all=lambda **kwargs: [("history", kwargs)]),
        ),
        ui=SimpleNamespace(
            add_hook=lambda *args: calls.hooks.append(args),
            config={"global": {"agent.llama.loop.enabled": checkbox}},
            tray=SimpleNamespace(
                show_msg=lambda *args: setattr(calls, "message", args)
            ),
            nodes={
                "status.agent": SimpleNamespace(
                    setText=lambda value: setattr(calls, "node", value)
                )
            },
        ),
        controller=SimpleNamespace(
            config=SimpleNamespace(
                apply_value=lambda **kwargs: calls.applied.append(kwargs)
            ),
            kernel=SimpleNamespace(
                stopped=lambda: calls.stopped,
                stop=lambda: setattr(calls, "stopped", True),
            ),
            agent=SimpleNamespace(
                common=SimpleNamespace(
                    toggle_status=lambda: setattr(calls, "toggled", True)
                )
            ),
        ),
        update_status=calls.statuses.append,
        dispatch=calls.events.append,
    )
    return window, calls


def test_llama_setup_reload_loop_and_notification(agent_modules):
    window, calls = _llama_window(
        {
            "agent.llama.loop.enabled": True,
            "agent.llama.loop.score": 66,
            "agent.goal.notify": True,
        }
    )
    controller = agent_modules.llama.Llama(window)
    controller.setup()
    assert calls.hooks[0][0] == "update.global.agent.llama.loop.score"
    assert calls.checked is True
    assert calls.applied[0]["value"] == 66
    controller.eval_step_next()
    assert controller.get_eval_step() == 1
    controller.update()
    assert calls.node == "1" and calls.toggled
    controller.on_end()
    assert calls.message == (
        "translated:notify.agent.goal.title",
        "translated:notify.agent.goal.content",
    )
    assert controller.get_eval_step() == 0

    window.core.config.values["agent.llama.loop.enabled"] = False
    controller.reload()
    assert calls.checked is False


def test_llama_finish_gates_dispatch_and_stop_resets_state(agent_modules):
    window, calls = _llama_window(
        {
            "agent.llama.loop.enabled": False,
            "agent.goal.notify": False,
            "agent.llama.max_eval": 2,
        }
    )
    controller = agent_modules.llama.Llama(window)
    ctx = SimpleNamespace(meta=SimpleNamespace(id="ctx-1"))
    controller.eval_step_next()
    controller.on_finish(ctx)
    assert calls.events == [] and controller.get_eval_step() == 0

    window.core.config.values["agent.llama.loop.enabled"] = True
    calls.stopped = True
    controller.on_finish(ctx)
    assert calls.events == []
    calls.stopped = False
    controller.eval_step = 2
    controller.on_finish(ctx)
    assert calls.events == []

    controller.eval_step = 0
    controller.on_finish(ctx)
    assert controller.get_eval_step() == 1
    assert calls.statuses == ["translated:status.evaluating"]
    event = calls.events[0]
    assert event.event_type == "request-next"
    assert event.data["context"].ctx is ctx
    assert event.data["context"].history[0][1] == {"meta_id": "ctx-1"}

    controller.on_stop()
    assert calls.stopped
    assert controller.get_eval_step() == 0
    assert calls.statuses[-1] == "translated:status.finished"


def test_llama_score_hook_saves_only_a_changed_score(agent_modules):
    window, calls = _llama_window({"agent.llama.loop.score": 50})
    controller = agent_modules.llama.Llama(window)
    controller.hook_update("agent.llama.loop.score", 50, "ui")
    assert window.core.config.saved == 0
    controller.hook_update("agent.llama.loop.score", "72", "ui", extra=True)
    assert window.core.config.get("agent.llama.loop.score") == 72
    assert window.core.config.saved == 1
    assert calls.node == "0" and calls.toggled


def test_common_controller_toggles_infinity_loop_and_status(agent_modules):
    config = _Config({"mode": "agent", "agent.iterations": 0})
    states = []
    calls = SimpleNamespace()
    window = SimpleNamespace(
        core=SimpleNamespace(
            config=config,
            plugins=SimpleNamespace(get_option=lambda *_args: 0),
            debug=SimpleNamespace(info=lambda _value: None),
        ),
        controller=SimpleNamespace(
            plugins=SimpleNamespace(is_enabled=lambda _plugin: False),
            agent=SimpleNamespace(legacy=SimpleNamespace(is_inline=lambda: False)),
        ),
        ui=SimpleNamespace(
            dialogs=SimpleNamespace(
                confirm=lambda **kwargs: setattr(calls, "confirm", kwargs)
            ),
            nodes={"status.agent": SimpleNamespace(setVisible=states.append)},
        ),
    )
    controller = agent_modules.common.Common(window)
    controller.disable_auto_stop()
    controller.toggle_auto_stop(True)
    controller.disable_continue()
    controller.toggle_continue(True)
    controller.disable_loop()
    controller.toggle_loop(True)
    assert config.values["agent.auto_stop"] is True
    assert config.values["agent.continue.always"] is True
    assert config.values["agent.llama.loop.enabled"] is True
    assert config.saved == 6

    assert controller.is_infinity_loop("agent")
    config.values["mode"] = "chat"
    window.controller.plugins.is_enabled = lambda _plugin: True
    assert controller.is_infinity_loop("chat")
    window.controller.plugins.is_enabled = lambda _plugin: False
    assert not controller.is_infinity_loop("chat")
    controller.display_infinity_loop_confirm()
    assert calls.confirm == {
        "type": "agent.infinity.run",
        "id": 0,
        "msg": "translated:agent.infinity.confirm.content",
    }

    controller.show_status()
    controller.hide_status()
    assert states == [True, False]
    window.controller.agent.legacy.is_inline = lambda: True
    controller.toggle_status()
    assert states[-1] is True
    config.values["mode"] = "agent"
    controller.toggle_status()
    assert states[-1] is True
    config.values["mode"] = "chat"
    window.controller.agent.legacy.is_inline = lambda: False
    controller.toggle_status()
    assert states[-1] is False
