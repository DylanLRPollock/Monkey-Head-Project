SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.PHONY: setup dev test run fmt lint clean ml data cloud pytest coverage lint-black lint-isort lint-ruff lint-flake8 docker-build docker-up docker-down

PORT ?= 1995
HOST ?= 0.0.0.0
PYTHON ?= python3
PIP := $(PYTHON) -m pip
SETUP_EXTRAS ?=
DEV_EXTRAS ?= dev
DEV_OPTIONAL_PROFILES ?=
ML_EXTRAS ?= ml
DATA_EXTRAS ?= data
CLOUD_EXTRAS ?= cloud

setup:
	$(PIP) install --upgrade pip setuptools wheel
	if [ -n "$(strip $(SETUP_EXTRAS))" ]; then \
		$(PIP) install -e ".[$(strip $(SETUP_EXTRAS))]"; \
	else \
		$(PIP) install -e .; \
	fi

test: lint pytest

run:
	$(PYTHON) -m uvicorn huey.api:app --host $(HOST) --port $(PORT)

fmt:
	black . && isort .

lint: lint-black lint-isort lint-ruff lint-flake8

lint-black:
	black --check .

lint-isort:
	isort --check-only .

lint-ruff:
	ruff check .

lint-flake8:
	flake8 .

pytest:
	$(PYTHON) -m pytest -q

coverage:
	$(PYTHON) -m pytest --cov=huey --cov=hueyos --cov-report=term-missing

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
	if [ -n "$(strip $(ML_EXTRAS))" ]; then \
		$(PIP) install -e ".[$(strip $(ML_EXTRAS))]"; \
	else \
		$(PIP) install -e .; \
	fi
	$(PYTHON) - << 'PY'
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
	if [ -n "$(strip $(DATA_EXTRAS))" ]; then \
		$(PIP) install -e ".[$(strip $(DATA_EXTRAS))]"; \
	else \
		$(PIP) install -e .; \
	fi
	$(PYTHON) - << 'PY'
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
	if [ -n "$(strip $(CLOUD_EXTRAS))" ]; then \
		$(PIP) install -e ".[$(strip $(CLOUD_EXTRAS))]"; \
	else \
		$(PIP) install -e .; \
	fi
	$(PYTHON) - << 'PY'
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

dev:
	if [ -n "$(strip $(DEV_OPTIONAL_PROFILES))" ]; then \
		$(MAKE) setup SETUP_EXTRAS="$(strip $(DEV_EXTRAS)),$(strip $(DEV_OPTIONAL_PROFILES))"; \
	else \
		$(MAKE) setup SETUP_EXTRAS="$(strip $(DEV_EXTRAS))"; \
	fi
	pre-commit install --install-hooks
	$(MAKE) fmt
	$(MAKE) lint
	pre-commit run --all-files
	$(PYTHON) -m pytest -q

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down
