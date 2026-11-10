"""Cover AIProcessor behavior with isolated fakes for optional data libraries."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest


def _install_optional_fakes(monkeypatch):
    calls = {"plots": [], "http": [], "frames": []}
    matplotlib = types.ModuleType("matplotlib")
    matplotlib.use = lambda _backend: None
    pyplot = types.ModuleType("matplotlib.pyplot")
    pyplot.tight_layout = lambda: calls["plots"].append("tight")
    pyplot.savefig = lambda filename: calls["plots"].append(("save", filename))
    pyplot.close = lambda: calls["plots"].append("close")
    matplotlib.pyplot = pyplot

    networkx = types.ModuleType("networkx")

    class Graph:
        def add_edges_from(self, edges):
            self.edges = list(edges)

    networkx.Graph = Graph
    networkx.shortest_path = lambda graph, source, target: [source, target]

    numpy = types.ModuleType("numpy")
    numpy.array = lambda values, dtype=None: list(values)
    numpy.mean = lambda values: sum(values) / len(values)

    pandas = types.ModuleType("pandas")

    class Frame:
        def __init__(self, data):
            calls["frames"].append(data)

        def describe(self):
            return {"rows": len(calls["frames"][-1])}

    pandas.DataFrame = Frame

    image_module = types.ModuleType("PIL.Image")

    class ImageObject:
        size = (640, 480)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    image_module.open = lambda _path: ImageObject()
    pil = types.ModuleType("PIL")
    pil.__path__ = []
    pil.Image = image_module

    requests = types.ModuleType("requests")
    requests.get = lambda url, **kwargs: calls["http"].append((url, kwargs))

    seaborn = types.ModuleType("seaborn")
    seaborn.histplot = lambda data, **kwargs: calls["plots"].append((data, kwargs))

    sklearn = types.ModuleType("sklearn")
    sklearn.__path__ = []
    linear_model = types.ModuleType("sklearn.linear_model")

    class LinearRegression:
        def fit(self, x_values, y_values):
            self.coef_ = [2.5]
            self.intercept_ = 1.0
            self.fit_args = (x_values, y_values)
            return self

    linear_model.LinearRegression = LinearRegression
    sklearn.linear_model = linear_model

    modules = {
        "matplotlib": matplotlib,
        "matplotlib.pyplot": pyplot,
        "networkx": networkx,
        "numpy": numpy,
        "pandas": pandas,
        "PIL": pil,
        "PIL.Image": image_module,
        "requests": requests,
        "seaborn": seaborn,
        "sklearn": sklearn,
        "sklearn.linear_model": linear_model,
    }
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    return calls


@pytest.fixture
def processor_module(monkeypatch):
    calls = _install_optional_fakes(monkeypatch)
    source = (
        Path(__file__).parents[1] / "src" / "huey" / "memory" / "PY" / "ai_processor.py"
    )
    spec = importlib.util.spec_from_file_location("huey.memory.PY.ai_processor", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)

    class Telemetry:
        def __init__(self, *, fail=False):
            self.entries = []
            self.fail = fail

        def log_ai_result(self, **kwargs):
            if self.fail:
                raise OSError("telemetry offline")
            self.entries.append(kwargs)

    accelerators = [
        SimpleNamespace(vram_total=1024, to_dict=lambda: {"name": "test-gpu"})
    ]
    monkeypatch.setattr(module, "detect_accelerators", lambda: list(accelerators))
    monkeypatch.setattr(
        module, "recommend_models_for_vram", lambda _vram: ["small-model"]
    )
    monkeypatch.setattr(module, "total_vram_bytes", lambda _accelerators: 1024)
    return module, calls, Telemetry


def test_offline_processing_catalog_and_text_helpers(processor_module, monkeypatch):
    module, _calls, Telemetry = processor_module
    monkeypatch.setattr(module.importlib.util, "find_spec", lambda _name: None)
    telemetry = Telemetry()
    processor = module.AIProcessor(telemetry_store=telemetry)

    assert processor.model == "small-model"
    assert processor.process_text("") == ""
    assert processor.process_text("  hello\n   world  ") == "Hello world"
    assert (
        processor.process_text("  second  line ", instruction="shorten")
        == "Second line"
    )
    assert processor.process_data("huey") == "HUEY"
    assert processor._tokenize("") == []
    assert processor._fallback_process(" \t\n ") == ""
    assert processor._tokenize("One, two!") == ["One", "two"]
    assert processor.analyze_data("One one\nTWO") == {
        "length": 11,
        "token_count": 3,
        "unique_token_count": 2,
        "line_count": 2,
        "whitespace_count": 2,
    }
    assert processor.get_model_catalog()["active_model"] == "small-model"
    assert processor.get_model_catalog(refresh=True)["total_vram"] == 1024
    assert len(telemetry.entries) == 2
    assert telemetry.entries[0]["backend"] == "offline"
    assert telemetry.entries[0]["status"] == "offline"


def test_backend_initialization_and_ollama_response_variants(
    processor_module, monkeypatch
):
    module, _calls, Telemetry = processor_module
    telemetry = Telemetry()
    client = SimpleNamespace(
        chat=lambda **_kwargs: {"message": {"content": "  transformed  "}}
    )
    monkeypatch.setattr(
        module.importlib.util,
        "find_spec",
        lambda name: object() if name == "ollama" else None,
    )
    monkeypatch.setattr(module.importlib, "import_module", lambda _name: client)
    processor = module.AIProcessor(model="custom", telemetry_store=telemetry)

    assert processor._llm_backend == "ollama"
    assert processor.process_text("input", "rewrite") == "transformed"
    assert telemetry.entries[-1]["backend"] == "ollama"
    assert telemetry.entries[-1]["status"] == "success"

    client.chat = lambda **_kwargs: {"messages": [{"content": " from list "}]}
    assert processor.process_text("input") == "from list"
    client.chat = lambda **_kwargs: {"messages": []}
    assert processor.process_text("input") == "Input"
    client.chat = lambda **_kwargs: {"messages": ["not a mapping"]}
    assert processor.process_text("input") == "Input"
    client.chat = lambda **_kwargs: {"messages": [{"content": 3}]}
    assert processor.process_text("input") == "Input"
    client.chat = lambda **_kwargs: {"message": {"content": "  "}}
    assert processor.process_text("input") == "Input"
    assert telemetry.entries[-1]["status"] == "fallback"


def test_backend_fallback_errors_and_telemetry_failure(processor_module, monkeypatch):
    module, _calls, Telemetry = processor_module
    client = SimpleNamespace(chat=lambda *_args, **_kwargs: " useful ")
    monkeypatch.setattr(
        module.importlib.util,
        "find_spec",
        lambda name: object() if name == "pygpt_net" else None,
    )
    monkeypatch.setattr(
        module.importlib,
        "import_module",
        lambda _name: SimpleNamespace(Client=lambda: client),
    )
    telemetry = Telemetry()
    processor = module.AIProcessor(telemetry_store=telemetry)
    assert processor._llm_backend == "pygpt_net"
    assert processor.process_text("raw") == "useful"
    assert telemetry.entries[-1]["backend"] == "pygpt_net"

    processor._accelerators = []
    client.chat = None
    assert processor.process_text("refreshes hardware") == "Refreshes hardware"
    assert processor._process_with_llm("input", "instruction") == ("Input", True)
    client.chat = lambda *_args, **_kwargs: 3
    assert processor._process_with_llm("input", "instruction") == ("Input", True)
    processor._llm_backend = "unsupported"
    assert processor._process_with_llm("input", "instruction") == ("Input", True)

    processor._llm_backend = "pygpt_net"
    client.chat = lambda *_args, **_kwargs: None
    assert processor.process_text("   ") == ""
    assert telemetry.entries[-1]["backend"] == "pygpt_net-fallback"

    client.chat = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        RuntimeError("offline")
    )
    assert processor.process_text("raw text") == "Raw text"
    assert telemetry.entries[-1]["backend"] == "pygpt_net-error"
    assert telemetry.entries[-1]["status"] == "error"

    broken_telemetry = Telemetry(fail=True)
    processor.telemetry_store = broken_telemetry
    assert processor.process_text("still works") == "Still works"


def test_optional_backend_rejection_and_silent_logger(processor_module, monkeypatch):
    module, _calls, Telemetry = processor_module
    monkeypatch.setattr(
        module.importlib.util,
        "find_spec",
        lambda name: object() if name in {"ollama", "pygpt_net"} else None,
    )
    modules = {
        "ollama": SimpleNamespace(),
        "pygpt_net": SimpleNamespace(Client=lambda: object()),
    }
    monkeypatch.setattr(module.importlib, "import_module", lambda name: modules[name])
    processor = module.AIProcessor(telemetry_store=Telemetry())
    assert processor._llm_backend is None
    assert processor._init_ollama_backend() is None
    assert processor._init_pygpt_backend() is None

    modules["pygpt_net"] = SimpleNamespace(
        Client=lambda: (_ for _ in ()).throw(RuntimeError("unavailable"))
    )
    assert processor._init_pygpt_backend() is None

    processor.telemetry_store = None
    processor._log_interaction(
        prompt="p",
        response="r",
        instruction="i",
        backend="offline",
        model="m",
        status="ok",
    )

    monkeypatch.setattr(module.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(
        module.importlib, "import_module", lambda _name: SimpleNamespace()
    )
    assert processor._init_pygpt_backend() is None


def test_data_analysis_visualization_http_graph_and_image_helpers(
    processor_module, monkeypatch
):
    module, calls, Telemetry = processor_module
    monkeypatch.setattr(module.importlib.util, "find_spec", lambda _name: None)
    processor = module.AIProcessor(telemetry_store=Telemetry())

    assert processor.compute_mean([1, 2, 6]) == 3.0
    assert processor.dataframe_summary([{"a": 1}, {"a": 2}]) == {"rows": 2}
    assert processor.train_linear_model([[1], [2]], [3, 5]) == (2.5, 1.0)
    assert processor.plot_histogram([1, 2], "chart.png") == "chart.png"
    assert calls["plots"] == [
        ([1, 2], {"kde": True}),
        "tight",
        ("save", "chart.png"),
        "close",
    ]
    assert processor.shortest_path([("a", "b")], "a", "b") == ["a", "b"]
    assert processor.image_size("image.png") == (640, 480)

    response = SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"title": "test title"},
    )
    monkeypatch.setattr(
        module.requests,
        "get",
        lambda url, **kwargs: calls["http"].append((url, kwargs)) or response,
    )
    assert processor.fetch_todo_title(7) == "test title"
    assert calls["http"][0] == (
        "https://jsonplaceholder.typicode.com/todos/7",
        {"timeout": 10},
    )
    monkeypatch.setattr(
        module.requests,
        "get",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("network")),
    )
    with pytest.raises(OSError, match="network"):
        processor.fetch_todo_title(8)
