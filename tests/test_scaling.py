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
    def configure(self, size=None):
        self.size = size

class DummyFontModule:
    def nametofont(self, name):
        return DummyFont()

def test_apply_scaling_1080p(monkeypatch):
    monkeypatch.setattr('monkey_head.gui_scaling.tkfont', DummyFontModule())
    root = DummyRoot()
    apply_scaling(root, mode='1080p')
    assert root.tk.args == ('tk', 'scaling', 1.0)

def test_apply_scaling_4k(monkeypatch):
    monkeypatch.setattr('monkey_head.gui_scaling.tkfont', DummyFontModule())
    root = DummyRoot()
    apply_scaling(root, mode='4k')
    assert root.tk.args == ('tk', 'scaling', 2.0)
