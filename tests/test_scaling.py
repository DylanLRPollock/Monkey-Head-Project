from monkey_head.gui_scaling import apply_scaling


class DummyTk:
    def __init__(self):
        self.args = None

    def call(self, *args):
        self.args = args


class DummyRoot:
    def __init__(self):
        self.tk = DummyTk()


class DummyFont:
    def __init__(self):
        self.size = None
        self.family = None

    def configure(self, size=None, family=None, **kwargs):
        self.size = size
        self.family = family


class DummyFontModule:
    def __init__(self):
        self.fonts = []

    def nametofont(self, name):
        font = DummyFont()
        self.fonts.append(font)
        return font


def test_apply_scaling_1080p(monkeypatch):
    module = DummyFontModule()
    monkeypatch.setattr("monkey_head.gui_scaling.tkfont", module)
    root = DummyRoot()
    apply_scaling(root, mode="1080p")
    assert root.tk.args == ("tk", "scaling", 1.0)
    assert all(f.size == 10 for f in module.fonts)


def test_apply_scaling_4k(monkeypatch):
    module = DummyFontModule()
    monkeypatch.setattr("monkey_head.gui_scaling.tkfont", module)
    root = DummyRoot()
    apply_scaling(root, mode="4k")
    assert root.tk.args == ("tk", "scaling", 2.0)
    assert all(f.size == 14 for f in module.fonts)


def test_apply_scaling_custom(monkeypatch):
    module = DummyFontModule()
    monkeypatch.setattr("monkey_head.gui_scaling.tkfont", module)
    monkeypatch.setenv("SCREEN_FACTOR", "1.5")
    monkeypatch.setenv("SCREEN_FONT_SIZE", "12")
    monkeypatch.setenv("SCREEN_FONT_FAMILY", "TestFont")
    root = DummyRoot()
    apply_scaling(root, mode="custom")
    assert root.tk.args == ("tk", "scaling", 1.5)
    assert all((f.size == 12 and f.family == "TestFont") for f in module.fonts)
