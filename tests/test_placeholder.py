"""Tests for the lightweight placeholder helpers."""

from huey.pygpt_net.controller.config.placeholder import Placeholder


class DummyPreset:
    def __init__(self, filename: str, name: str | None = None) -> None:
        self.filename = filename
        self.name = name or filename


class DummyPresets:
    def __init__(self, payload):
        self.payload = payload

    def get_all(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class DummyCore:
    def __init__(self, payload):
        self.presets = payload


class DummyWindow:
    def __init__(self, payload=None, with_core: bool = True):
        if with_core:
            self.core = DummyCore(payload)


def test_get_presets_returns_names():
    preset = DummyPreset("example.json", name="Example")
    placeholder = Placeholder(DummyWindow(DummyPresets({preset.filename: preset})))

    result = placeholder.get_presets()

    assert {"_": "---"} in result
    assert {"example.json": "Example"} in result


def test_handles_missing_core_gracefully():
    placeholder = Placeholder(DummyWindow(with_core=False))

    assert placeholder.get_presets() == [{"_": "---"}]


def test_accepts_iterable_of_tuples():
    presets = [("first.json", DummyPreset("first.json", "First"))]
    placeholder = Placeholder(DummyWindow(DummyPresets(presets)))

    assert placeholder.get_presets()[1:] == [{"first.json": "First"}]


def test_accepts_iterable_of_objects():
    presets = [DummyPreset("alt.json", "Alternate")]
    placeholder = Placeholder(DummyWindow(DummyPresets(presets)))

    assert placeholder.get_presets()[1:] == [{"alt.json": "Alternate"}]


def test_ignores_unusable_iterables_and_errors():
    class NoFilename:
        pass

    placeholder_list = Placeholder(DummyWindow(DummyPresets([NoFilename()])))
    placeholder_error = Placeholder(DummyWindow(DummyPresets(ValueError("bad"))))
    placeholder_string = Placeholder(DummyWindow(DummyPresets("not iterable")))

    assert placeholder_list.get_presets() == [{"_": "---"}]
    assert placeholder_error.get_presets() == [{"_": "---"}]
    assert placeholder_string.get_presets() == [{"_": "---"}]
