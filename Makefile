SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.PHONY: setup dev test run fmt lint clean ml data cloud

PORT ?= 5151
REQ_DIR := requirements
REQ_ML_FILE := $(REQ_DIR)/requirements-ml.txt
REQ_DATA_FILE := $(REQ_DIR)/requirements-data.txt
REQ_CLOUD_FILE := $(REQ_DIR)/requirements-cloud.txt
REQ_DEV_FILE := $(REQ_DIR)/requirements-dev.txt

define install_section
        @if [ -f $(1) ]; then \
                echo "Installing dependencies from $(1)"; \
                python3 -m pip install -r $(1); \
        elif [ -f requirements.txt ]; then \
                tmp_file="$$(mktemp)"; \
                echo "Extracting $(2) requirements from requirements.txt"; \
                SECTION="$(2)" TMP_FILE="$$tmp_file" python3 - <<'PY'; \
import os
from pathlib import Path

section = os.environ["SECTION"]
tmp_path = Path(os.environ["TMP_FILE"])
source = Path("requirements.txt")
start_token = f"# ===== {section}.txt ====="
capture = False
lines = []

with source.open(encoding="utf-8") as handle:
    for raw_line in handle:
        stripped = raw_line.strip()
        if stripped == start_token:
            capture = True
            continue
        if capture and stripped.startswith("# =====") and stripped != start_token:
            break
        if capture and stripped and not stripped.startswith("#"):
            lines.append(raw_line)

if not lines:
    raise SystemExit(f"No requirements found for section '{section}'")

tmp_path.write_text("".join(lines), encoding="utf-8")
PY
                python3 -m pip install -r "$$tmp_file"; \
                rm -f "$$tmp_file"; \
        else \
                echo "Unable to locate requirements for $(2)" >&2; \
                exit 1; \
        fi
endef

setup:
        python3 -m pip install --upgrade pip
        python3 -m pip install -r $(REQ_DIR)/requirements-core.txt

test: fmt lint
        pytest -q

run:
        python3 -m uvicorn huey.api:app --host 0.0.0.0 --port $(PORT)

fmt:
        black . && isort .

lint:
        flake8 .

clean:
        rm -rf build dist .pytest_cache **/__pycache__ *.egg-info
        rm -rf .mypy_cache/ .ruff_cache/ .coverage htmlcov/
        if command -v docker >/dev/null 2>&1; then \
                docker container prune -f; \
                docker image prune -f; \
                docker system prune -f --volumes; \
        else \
                echo "Docker not available, skipping Docker cleanup"; \
        fi

ml:
        $(call install_section,$(REQ_ML_FILE),requirements-ml)
        python3 - <<'PY'
from llama_index.core import Document, VectorStoreIndex

documents = [
    Document(text="Huey is a friendly robotics research assistant."),
    Document(text="Huey loves banana milkshakes."),
]
index = VectorStoreIndex.from_documents(documents)
response = index.as_query_engine().query("What does Huey enjoy?")
print("Sample inference response:", response)
PY

data:
        $(call install_section,$(REQ_DATA_FILE),requirements-data)
        python3 - <<'PY'
import chromadb

client = chromadb.Client()
collection = client.get_or_create_collection("makefile_demo")
collection.add(
    ids=["1"],
    documents=["Huey keeps its research notes in a vector store."],
    metadatas=[{"source": "demo"}],
)
result = collection.query(query_texts=["research notes"], n_results=1)
print("Chroma query result:", result)
PY

cloud:
        $(call install_section,$(REQ_CLOUD_FILE),requirements-cloud)
        python3 - <<'PY'
import urllib.request

import boto3  # noqa: F401 - ensure AWS SDK is installed
from azure.identity import AzureAuthorityHosts  # noqa: F401 - ensure Azure SDK is installed

providers = {
    "Azure": "https://management.azure.com/",
    "GCP": "https://www.googleapis.com/",
    "AWS": "https://sts.amazonaws.com/",
}

for name, url in providers.items():
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            status = response.status
    except Exception as exc:  # pragma: no cover - depends on network availability
        print(f"{name} connectivity check failed: {exc}")
    else:
        print(f"{name} connectivity check succeeded (status {status})")
PY

dev: setup
        $(call install_section,$(REQ_DEV_FILE),requirements-dev)
        python3 -m pip install black isort flake8
        pre-commit install --install-hooks
        $(MAKE) fmt
        $(MAKE) lint
        pre-commit run --all-files
        pytest -q

