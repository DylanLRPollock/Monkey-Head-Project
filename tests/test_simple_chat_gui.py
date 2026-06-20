# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Simple Chat Gui module (tests)

from types import SimpleNamespace

from huey.os.simple_chat_gui import get_answer, run_simple_chat


def test_get_answer_known():
    assert (
        get_answer("What is the capital of France?")
        == "The capital of France is Paris."
    )


def test_get_answer_unknown():
    assert "Sorry" in get_answer("Who is John Galt?")


def test_run_simple_chat(monkeypatch):
    events = {}

    class DummyRoot:
        def configure(self, **kwargs):
            pass

        def title(self, t):
            events["title"] = t

        def mainloop(self):
            events["ran"] = True

    class DummyWidget:
        def __init__(self, *a, **k):
            pass

        def pack(self, *a, **k):
            pass

        def config(self, *a, **k):
            pass

        def insert(self, *a, **k):
            pass

        def delete(self, *a, **k):
            pass

        def get(self):
            return ""

    dummy_tk = SimpleNamespace(
        Tk=lambda: DummyRoot(),
        Entry=DummyWidget,
        Button=lambda *a, **k: DummyWidget(),
        NORMAL="normal",
        DISABLED="disabled",
        END="end",
    )
    dummy_scrolled = SimpleNamespace(ScrolledText=lambda *a, **k: DummyWidget())

    monkeypatch.setattr("huey.os.simple_chat_gui.tk", dummy_tk)
    monkeypatch.setattr("huey.os.simple_chat_gui.scrolledtext", dummy_scrolled)
    monkeypatch.setattr(
        "huey.os.simple_chat_gui.apply_scaling",
        lambda *a, **k: events.update({"scaled": True}),
    )

    run_simple_chat()
    assert events.get("ran") is True
    assert events.get("scaled") is True
