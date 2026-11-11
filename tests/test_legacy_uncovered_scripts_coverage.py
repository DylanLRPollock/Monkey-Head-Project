"""Exercise dependency-light legacy scripts without requiring their runtimes."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

LEGACY = Path(__file__).resolve().parents[1] / "src" / "huey" / "memory" / "PY"


def _load_script(path: Path, name: str):
    module_name = f"huey.memory.PY._coverage_{name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_transcribe_lecture_writes_text_and_srt_with_and_without_segments(
    monkeypatch, tmp_path, capsys
):
    class Segment:
        def __init__(self, start, end, text):
            self.start, self.end, self.text = start, end, text

    class WhisperModel:
        batches = iter(
            [
                (
                    [Segment(0, 61.9996, " first ")],
                    SimpleNamespace(language="en", language_probability=0.75),
                ),
                ([], SimpleNamespace(language="fr", language_probability=0.5)),
            ]
        )

        def __init__(self, *_args, **_kwargs):
            pass

        def transcribe(self, *_args, **_kwargs):
            return next(self.batches)

    monkeypatch.setattr(Path, "home", classmethod(lambda _cls: tmp_path))
    monkeypatch.setitem(
        sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=WhisperModel)
    )

    script = LEGACY / "transcribe-lecture.py"
    module = _load_script(script, "legacy_transcribe_lecture")
    text_path = tmp_path / "alan_watts_medium.en.txt"
    srt_path = tmp_path / "alan_watts_medium.en.srt"
    assert "[0.00 -> 62.00] first" in text_path.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:01:02,000" in srt_path.read_text(encoding="utf-8")

    module.__loader__.exec_module(module)
    assert "Segments: 0" in capsys.readouterr().out


def test_mini_chat_gui_answers_and_updates_widgets(monkeypatch):
    calls = []

    class Widget:
        def __init__(self, *_args, **kwargs):
            self.kwargs = kwargs
            self.value = "two plus two"

        def title(self, value):
            calls.append(("title", value))

        def pack(self, **kwargs):
            calls.append(("pack", kwargs))

        def get(self):
            return self.value

        def config(self, **kwargs):
            calls.append(("config", kwargs))

        def insert(self, index, value):
            calls.append(("insert", index, value))

        def delete(self, *_args):
            self.value = ""

        def mainloop(self):
            calls.append(("mainloop",))

    fake_tk = ModuleType("tkinter")
    fake_tk.Tk = Widget
    fake_tk.Entry = Widget
    fake_tk.Button = Widget
    fake_tk.END = "end"
    fake_tk.NORMAL = "normal"
    fake_tk.DISABLED = "disabled"
    fake_scrolled = ModuleType("tkinter.scrolledtext")
    fake_scrolled.ScrolledText = Widget
    monkeypatch.setitem(sys.modules, "tkinter", fake_tk)
    monkeypatch.setitem(sys.modules, "tkinter.scrolledtext", fake_scrolled)

    result = _load_script(LEGACY / "mini-chat-gui.py", "legacy_mini_chat_gui")
    assert (
        result.get_answer("  CAPITAL OF FRANCE ") == "The capital of France is Paris."
    )
    assert result.get_answer("2+2") == "2 + 2 equals 4."
    assert result.get_answer("unknown") == "Sorry, I do not know the answer."
    result.on_ask()
    assert any("2 + 2 equals 4." in item[-1] for item in calls if item[0] == "insert")
    assert ("mainloop",) in calls


def test_train_image_model_cli_selects_device_and_prints_artifacts(monkeypatch, capsys):
    configs = []
    training = ModuleType("monkey_head.training")
    training.TrainingConfig = lambda **kwargs: configs.append(kwargs) or kwargs
    training.run_training = lambda config: (
        {"weights": "/tmp/model.bin"},
        SimpleNamespace(best_val_accuracy=0.875),
    )
    package = ModuleType("monkey_head")
    package.__path__ = []
    package.training = training
    torch = ModuleType("torch")
    torch.cuda = SimpleNamespace(is_available=lambda: True)
    monkeypatch.setitem(sys.modules, "monkey_head", package)
    monkeypatch.setitem(sys.modules, "monkey_head.training", training)
    monkeypatch.setitem(sys.modules, "torch", torch)

    script = LEGACY / "train_image_model.py"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(script),
            "--data-dir",
            "images",
            "--output-dir",
            "artifacts",
            "--device",
            "cpu",
        ],
    )
    module = _load_script(script, "legacy_train_image_model")
    module.main()
    assert configs[-1]["device"] == "cpu"
    output = capsys.readouterr().out
    assert "Best validation accuracy: 0.8750" in output
    assert "Saved weights: /tmp/model.bin" in output

    monkeypatch.setattr(
        sys,
        "argv",
        [str(script), "--data-dir", "images", "--output-dir", "artifacts"],
    )
    module.main()
    assert configs[-1]["device"] == "cuda"


def test_chat_learning_works_with_stubbed_optional_dependencies(monkeypatch):
    class Document:
        def __iter__(self):
            return iter([SimpleNamespace(get_text=lambda: "PDF words")])

        def close(self):
            self.closed = True

    fitz = ModuleType("fitz")
    fitz.open = lambda _path: Document()

    class Tokenizer:
        def fit_on_texts(self, texts):
            words = list(dict.fromkeys(texts[0].split()))
            self.word_index = {word: index + 1 for index, word in enumerate(words)}

        def texts_to_sequences(self, texts):
            return [[self.word_index[word] for word in texts[0].split()]]

    class Model:
        def __init__(self, layers):
            self.layers = layers
            self.fit_args = None

        def compile(self, **kwargs):
            self.compile_args = kwargs

        def fit(self, *args, **kwargs):
            self.fit_args = (args, kwargs)

    tf = ModuleType("tensorflow")
    tf.keras = SimpleNamespace(
        Model=Model,
        preprocessing=SimpleNamespace(text=SimpleNamespace(Tokenizer=Tokenizer)),
        Sequential=Model,
        layers=SimpleNamespace(
            Embedding=lambda *a, **k: ("Embedding", a, k),
            Flatten=lambda: "Flatten",
            Dense=lambda *a, **k: ("Dense", a, k),
        ),
    )
    tf.constant = lambda values: tuple(values)
    tf.expand_dims = lambda values, axis: (values, axis)
    monkeypatch.setitem(sys.modules, "fitz", fitz)
    monkeypatch.setitem(sys.modules, "tensorflow", tf)
    module = importlib.reload(importlib.import_module("huey.memory.PY.chat_learning"))

    assert module._read_pdf_text("book.pdf") == "PDF words"
    try:
        module._prepare_dataset(["one"])
    except ValueError as exc:
        assert "Not enough text" in str(exc)
    else:
        raise AssertionError("single-token training data must be rejected")
    xs, ys, tokenizer = module._prepare_dataset(["one two"])
    assert xs == ((1,), -1)
    assert ys == (2,)
    assert tokenizer.word_index == {"one": 1, "two": 2}

    model = module.train_from_chat_and_pdfs(["chat words"], ["book.pdf"], epochs=3)
    assert model.compile_args["optimizer"] == "adam"
    assert model.fit_args[1]["epochs"] == 3
