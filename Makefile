# ---------------------------------------------------------------------------
# Monkey-Head-Project
# Component: HueyOS / Build Automation
# Author: Dylan L.R. Pollock
# Documentation: https://www.dlrp.ca
#
# Philosophy: Breathing new life into old tech.
# ---------------------------------------------------------------------------
#
# Target baseline: Python 3.13.x. Python 3.14 is testing-only and not a
# release target; do not add it to the interpreter candidates below.
#
# Conventions for this file:
#   * `make` with no arguments runs `help`, not a build. `.DEFAULT_GOAL`
#     is set explicitly so this does not depend on which target comes first.
#   * Every target is `.PHONY` unless it names a real file on disk.
#   * Variables are overridable from the environment or the command line,
#     e.g. `make run PORT=8080` or `make test PYTEST_ARGS="-k connectors"`.
#   * Shell commands run with `SHELL := /bin/sh` on POSIX and `cmd.exe` on
#     Windows unless overridden. Windows contributors should have GNU Make
#     available (via MSYS2, Git Bash, or WSL); the recipes below avoid
#     POSIX-only constructs so they work in all three.
#   * `make lint` is expected to pass on a clean checkout. If a guardrail
#     script is flaky or slow, gate it behind a separate target -- do not
#     remove it from `lint` silently.

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Interpreter. Windows ships `py -3.13`; everywhere else, `python3.13`.
# Both can be overridden: `make test PYTHON=python3.12` is fine for a
# one-off, but CI must use the default.
PYTHON ?= python3.13
ifeq ($(OS),Windows_NT)
PYTHON := py -3.13
endif

PIP         ?= $(PYTHON) -m pip
HOST        ?= 0.0.0.0
PORT        ?= 1995
APP         ?= huey.api:app
PKG_COV     ?= --cov=huey
PYTEST_ARGS ?=
LINT_PATHS  ?= src tests scripts conftest.py
CONSTRAINTS ?= constraints.txt

# Treat warnings during lint as errors so `make lint` and CI agree.
LINT_ENV := PYTHONWARNINGS=error

# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------

.DEFAULT_GOAL := help
.PHONY: help setup install install-dev precommit-install format format-check lint \
        check-drift check-legacy-hueyos check-command-center check-canon \
        check-deps-sync test coverage run run-reload health clean clean-pyc \
        clean-test clean-build

help: ## Show this help.
	@echo "HueyOS common targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Variables (override on the command line):"
	@echo "  PYTHON=$(PYTHON)"
	@echo "  HOST=$(HOST)  PORT=$(PORT)"
	@echo "  APP=$(APP)"
	@echo "  PYTEST_ARGS=$(PYTEST_ARGS)"
	@echo "  LINT_PATHS=$(LINT_PATHS)"

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup: ## Upgrade packaging tools (pip, setuptools, wheel).
	$(PIP) install --upgrade pip setuptools wheel

install: ## Install core editable package with constraints.
	$(PIP) install -c $(CONSTRAINTS) -e .

install-dev: ## Install developer extras with constraints.
	$(PIP) install -c $(CONSTRAINTS) -e ".[dev]"

precommit-install: ## Install git hooks via pre-commit.
	pre-commit install
	pre-commit install --hook-type pre-push

# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

format: ## Run black + isort in place (writes changes).
	black $(LINT_PATHS)
	isort --profile black $(LINT_PATHS)

format-check: ## Verify formatting without writing (same as CI).
	black --check --diff $(LINT_PATHS)
	isort --check-only --diff --profile black $(LINT_PATHS)

# ---------------------------------------------------------------------------
# Linting
# ---------------------------------------------------------------------------

lint: ## Run repo guardrails + black/isort/ruff/flake8 (check-only).
	$(PYTHON) scripts/repo/check_stale_platform_strings.py
	$(PYTHON) scripts/repo/check_repo_drift.py
	$(PYTHON) scripts/repo/check_legacy_hueyos_imports.py
	$(PYTHON) scripts/check_command_center_contract.py
	$(PYTHON) scripts/repo/check_dependency_sync.py
	$(PYTHON) scripts/repo/check_canon_terms.py
	$(MAKE) format-check
	ruff check $(LINT_PATHS)
	flake8 $(LINT_PATHS)

# ---------------------------------------------------------------------------
# Repository guardrails (run individually for faster feedback)
# ---------------------------------------------------------------------------

check-drift: ## Run repository drift checker.
	$(PYTHON) scripts/repo/check_repo_drift.py

check-legacy-hueyos: ## Block new legacy hueyos imports.
	$(PYTHON) scripts/repo/check_legacy_hueyos_imports.py

check-command-center: ## Verify Command Center backend contract.
	$(PYTHON) scripts/check_command_center_contract.py

check-canon: ## Check canonical naming / terminology.
	$(PYTHON) scripts/repo/check_canon_terms.py

check-deps-sync: ## Check pyproject / requirements / constraints sync.
	$(PYTHON) scripts/repo/check_dependency_sync.py

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: ## Run pytest (add PYTEST_ARGS="-k foo" to filter).
	$(PYTHON) -m pytest -q $(PYTEST_ARGS)

coverage: ## Run pytest with coverage reports (terminal + XML).
	$(PYTHON) -m pytest $(PKG_COV) --cov-report=term-missing --cov-report=xml $(PYTEST_ARGS)

# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------

run: ## Run the FastAPI app via uvicorn.
	$(PYTHON) -m uvicorn $(APP) --host $(HOST) --port $(PORT)

run-reload: ## Run the FastAPI app with hot reload for development.
	$(PYTHON) -m uvicorn $(APP) --host $(HOST) --port $(PORT) --reload

health: ## Hit /healthz on the configured HOST/PORT.
	$(PYTHON) -c "import sys,urllib.request; \
		sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:$(PORT)/healthz', timeout=5).status == 200 else 1)"

# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

clean-pyc: ## Remove Python bytecode and caches.
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +

clean-test: ## Remove pytest / coverage / mypy caches.
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml htmlcov

clean-build: ## Remove build artifacts and egg-info.
	rm -rf build dist *.egg-info src/*.egg-info

clean: clean-pyc clean-test clean-build ## Remove all generated artifacts.