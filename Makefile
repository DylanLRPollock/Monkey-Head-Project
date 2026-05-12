# Monkey-Head-Project / HueyOS Makefile
# Target baseline: Python 3.13.x

PYTHON ?= python3.13
ifeq ($(OS),Windows_NT)
PYTHON ?= python
endif
PIP ?= $(PYTHON) -m pip
HOST ?= 0.0.0.0
PORT ?= 1995
APP ?= huey.api:app
PKG_COV ?= --cov=huey --cov=hueyos

.PHONY: help setup install install-dev precommit-install format lint check-drift check-deps-sync test coverage run run-reload health

help:
	@echo "Common targets:"
	@echo "  make setup            - upgrade packaging tools"
	@echo "  make install          - install core editable package with constraints"
	@echo "  make install-dev      - install developer extras with constraints"
	@echo "  make precommit-install- install git hooks"
	@echo "  make format           - run black + isort"
	@echo "  make lint             - run drift checks + black/isort/ruff/flake8"
	@echo "  make check-drift      - run repository drift checker"
	@echo "  make check-deps-sync  - check pyproject/requirements/constraints sync"
	@echo "  make test             - run pytest"
	@echo "  make coverage         - run pytest with coverage for huey + hueyos"
	@echo "  make run              - run FastAPI app via uvicorn"
	@echo "  make run-reload       - run FastAPI app with reload for development"
	@echo "  make health           - hit /healthz on the configured HOST/PORT"

setup:
	$(PIP) install --upgrade pip setuptools wheel

install:
	$(PIP) install -c constraints.txt -e .

install-dev:
	$(PIP) install -c constraints.txt -e ".[dev]"

precommit-install:
	pre-commit install

format:
	black src tests conftest.py
	isort src tests conftest.py

lint:
	$(PYTHON) scripts/check_stale_platform_strings.py
	$(PYTHON) scripts/check_repo_drift.py
	black --check src tests conftest.py
	isort --check-only src tests conftest.py
	ruff check src tests conftest.py
	flake8 src tests conftest.py

check-drift:
	$(PYTHON) scripts/check_repo_drift.py

check-deps-sync:
	$(PYTHON) scripts/check_dependency_sync.py

test:
	$(PYTHON) -m pytest -q

coverage:
	$(PYTHON) -m pytest $(PKG_COV) --cov-report=term-missing --cov-report=xml

run:
	$(PYTHON) -m uvicorn $(APP) --host $(HOST) --port $(PORT)

run-reload:
	$(PYTHON) -m uvicorn $(APP) --host $(HOST) --port $(PORT) --reload

health:
	curl -fsS http://127.0.0.1:$(PORT)/healthz
