from __future__ import annotations

from huey.pyhuey_integration import prepare_pygpt, reset_pygpt_state


def test_monkey_manager_imports_without_full_pyside_stack():
    reset_pygpt_state()
    assert prepare_pygpt(source="package")

    from huey.pygpt_net.tools.manager import MonkeyManager

    manager = MonkeyManager()
    actions = manager.setup_menu()

    assert "monkey.pyhuey.status" in actions
    assert "monkey.system.check" in actions
    assert manager.integration_status()["prepared"] is True
