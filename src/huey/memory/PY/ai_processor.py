# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Ai Processor module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
from __future__ import annotations

import importlib
import importlib.util
import logging
import re
from typing import Any, Dict, List, Optional

import matplotlib
import networkx as nx
import numpy as np
import pandas as pd
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import requests
import seaborn as sns
from sklearn.linear_model import LinearRegression

from hueyos.utils.gpu import (
    AcceleratorInfo,
    detect_accelerators,
    recommend_models_for_vram,
    total_vram_bytes,
)
from hueyos.utils.persistence import TelemetryStore


class AIProcessor:
    """Utility class that exposes lightweight AI features for demos and tests.

    The processor attempts to use a locally available large language model
    (LLM) – currently ``ollama`` or ``pygpt_net`` – for semantic text
    processing. When neither backend is usable the implementation falls back
    to deterministic, dependency-free algorithms so unit tests remain stable.
    """

    _OLLAMA_DEFAULT_MODEL = "llama3"

    def __init__(
        self,
        model: str | None = None,
        default_instruction: str | None = None,
        *,
        telemetry_store: Optional[TelemetryStore] = None,
    ):
        self.model = model
        self.default_instruction = default_instruction or (
            "Rewrite the provided text to improve clarity while preserving meaning."
        )
        self._logger = logging.getLogger(__name__)
        self._llm_backend: str | None = None
        self._llm_client: object | None = None
        self.telemetry_store = telemetry_store or TelemetryStore()
        self._accelerators: List[AcceleratorInfo] = []
        self._recommended_models: List[str] = []
        self.refresh_hardware_state()
        self._initialize_llm_backend()

    # ------------------------------------------------------------------
    # LLM initialisation helpers
    # ------------------------------------------------------------------
    def _initialize_llm_backend(self) -> None:
        """Detect and instantiate an available local LLM backend."""

        for name, initializer in (
            ("ollama", self._init_ollama_backend),
            ("pygpt_net", self._init_pygpt_backend),
        ):
            client = initializer()
            if client is not None:
                self._llm_backend = name
                self._llm_client = client
                return

    def refresh_hardware_state(self) -> None:
        """Refresh accelerator metadata and recommended models."""

        self._accelerators = detect_accelerators()
        best_vram = max(
            (info.vram_total or 0 for info in self._accelerators), default=0
        )
        self._recommended_models = recommend_models_for_vram(best_vram)
        if self.model is None and self._recommended_models:
            self.model = self._recommended_models[0]

    def get_model_catalog(self, refresh: bool = False) -> Dict[str, Any]:
        """Return backend, model, and accelerator insights for callers."""

        if refresh or not self._accelerators:
            self.refresh_hardware_state()
        return {
            "backend": self._llm_backend,
            "active_model": self.model or self._OLLAMA_DEFAULT_MODEL,
            "recommended_models": list(self._recommended_models),
            "accelerators": [info.to_dict() for info in self._accelerators],
            "total_vram": total_vram_bytes(self._accelerators),
        }

    def _init_ollama_backend(self) -> object | None:
        """Return an ``ollama`` client if the library is available."""

        spec = importlib.util.find_spec("ollama")
        if spec is None:
            return None

        module = importlib.import_module("ollama")
        if not hasattr(module, "chat"):
            return None
        return module

    def _init_pygpt_backend(self) -> object | None:
        """Return a ``pygpt_net`` client instance when possible."""

        spec = importlib.util.find_spec("pygpt_net")
        if spec is None:
            return None

        module = importlib.import_module("pygpt_net")
        client_cls = getattr(module, "Client", None)
        if client_cls is None:
            return None

        try:
            client = client_cls()
        except Exception:  # pragma: no cover - best effort optional dependency
            return None

        chat_method = getattr(client, "chat", None)
        if callable(chat_method):
            return client
        return None

    # ------------------------------------------------------------------
    # Public text utilities
    # ------------------------------------------------------------------
    def process_text(self, text: str, instruction: str | None = None) -> str:
        """Apply a semantic transformation to ``text``.

        Parameters
        ----------
        text:
            The raw text to transform.
        instruction:
            Optional natural-language instruction describing the desired
            transformation. When omitted, :attr:`default_instruction` is used.

        Returns
        -------
        str
            The transformed text. If no LLM backend is available the method
            falls back to a deterministic whitespace normalisation routine.
        """

        if not text:
            return ""

        if not self._accelerators:
            self.refresh_hardware_state()

        directive = instruction or self.default_instruction
        model_name = self.model or self._OLLAMA_DEFAULT_MODEL
        backend_label = self._llm_backend or "offline"
        status = "offline"

        if self._llm_backend is not None and self._llm_client is not None:
            try:
                response, used_fallback = self._process_with_llm(text, directive)
            except Exception:  # pragma: no cover - optional dependency failure
                self._logger.debug(
                    "LLM backend '%s' failed, falling back",
                    self._llm_backend,
                    exc_info=True,
                )
                response = self._fallback_process(text)
                backend_label = f"{self._llm_backend}-error"
                status = "error"
            else:
                status = "fallback" if used_fallback else "success"
                backend_label = (
                    f"{self._llm_backend}-fallback"
                    if used_fallback
                    else self._llm_backend
                )
                self._log_interaction(
                    prompt=text,
                    response=response,
                    instruction=directive,
                    backend=backend_label,
                    model=model_name,
                    status=status,
                )
                return response
        else:
            response = self._fallback_process(text)
            backend_label = "offline"
            status = "offline"

        self._log_interaction(
            prompt=text,
            response=response,
            instruction=directive,
            backend=backend_label,
            model=model_name,
            status=status,
        )
        return response

    def _process_with_llm(self, text: str, instruction: str) -> tuple[str, bool]:
        """Delegate semantic processing to the configured LLM backend."""

        if self._llm_backend == "ollama":
            client = self._llm_client
            assert client is not None  # for type-checkers

            model = self.model or self._OLLAMA_DEFAULT_MODEL
            response = client.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You transform user text exactly as requested.",
                    },
                    {
                        "role": "user",
                        "content": f"Instruction: {instruction}\n\nText:\n{text}",
                    },
                ],
            )

            message = response.get("message") if isinstance(response, dict) else None
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip(), False

            if isinstance(response, dict) and "messages" in response:
                messages = response["messages"]
                if messages:
                    content = messages[-1]
                    if isinstance(content, dict):
                        candidate = content.get("content")
                        if isinstance(candidate, str) and candidate.strip():
                            return candidate.strip(), False

        elif self._llm_backend == "pygpt_net":
            client = self._llm_client
            chat_method = getattr(client, "chat", None)
            if callable(chat_method):
                output = chat_method(
                    instruction,
                    text,
                    model=self.model,
                )
                if isinstance(output, str) and output.strip():
                    return output.strip(), False

        return self._fallback_process(text), True

    def _log_interaction(
        self,
        *,
        prompt: str,
        response: str,
        instruction: str,
        backend: str,
        model: str,
        status: str,
    ) -> None:
        if self.telemetry_store is None:
            return

        metadata: Dict[str, Any] = {
            "total_vram": total_vram_bytes(self._accelerators),
            "recommended_models": list(self._recommended_models),
        }
        try:
            self.telemetry_store.log_ai_result(
                prompt=prompt,
                response=response,
                model=model,
                backend=backend,
                instruction=instruction,
                metadata=metadata,
                status=status,
            )
        except Exception:  # pragma: no cover - telemetry failures should not break flow
            self._logger.debug(
                "Failed to record AI interaction telemetry", exc_info=True
            )

    def _fallback_process(self, text: str) -> str:
        """Provide a deterministic transformation when no LLM is active."""

        collapsed = re.sub(r"\s+", " ", text.strip())
        if not collapsed:
            return ""
        return collapsed[0].upper() + collapsed[1:]

    def process_data(self, data: str) -> str:
        """Return an upper-case version of ``data``.

        This helper mirrors the legacy interface used by a number of examples
        and unit tests. Keeping the implementation deterministic avoids brittle
        assertions in test fixtures that rely on predictable casing.
        """

        return data.upper()

    def analyze_data(self, data: str) -> dict[str, int]:
        """Analyze ``data`` and return token-centric statistics."""

        tokens = self._tokenize(data)
        token_set = {token.lower() for token in tokens}
        line_count = data.count("\n") + (1 if data else 0)
        whitespace_count = len(re.findall(r"\s", data))

        return {
            "length": len(data),
            "token_count": len(tokens),
            "unique_token_count": len(token_set),
            "line_count": line_count,
            "whitespace_count": whitespace_count,
        }

    def _tokenize(self, text: str) -> list[str]:
        """Split ``text`` into coarse whitespace-delimited tokens."""

        if not text:
            return []
        return re.findall(r"\b\w+\b", text)

    def compute_mean(self, numbers: list[float]) -> float:
        """Return the arithmetic mean of ``numbers`` using NumPy."""

        array = np.array(numbers, dtype=float)
        return float(np.mean(array))

    def dataframe_summary(self, data: list[dict]) -> pd.DataFrame:
        """Convert ``data`` to a DataFrame and return ``describe()`` result."""

        df = pd.DataFrame(data)
        return df.describe()

    def train_linear_model(self, X: list[list[float]], y: list[float]) -> tuple:
        """Fit a simple linear regression model and return coefficients."""

        model = LinearRegression().fit(X, y)
        return (float(model.coef_[0]), float(model.intercept_))

    def plot_histogram(self, data: list[float], filename: str) -> str:
        """Plot ``data`` as a histogram using seaborn and save to ``filename``."""

        sns.histplot(data, kde=True)
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()
        return filename

    def fetch_todo_title(self, todo_id: int) -> str:
        """Fetch a sample TODO item and return its title."""

        url = f"https://jsonplaceholder.typicode.com/todos/{todo_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()["title"]

    def shortest_path(
        self, edges: list[tuple[str, str]], source: str, target: str
    ) -> list[str]:
        """Return the shortest path between two nodes using ``networkx``."""

        graph = nx.Graph()
        graph.add_edges_from(edges)
        return nx.shortest_path(graph, source, target)

    def image_size(self, path: str) -> tuple[int, int]:
        """Return the ``(width, height)`` of an image using Pillow."""

        with Image.open(path) as img:
            return img.size
