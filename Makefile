SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.PHONY: setup dev test run fmt lint clean ml data cloud

setup:
	python3 -m pip install --upgrade pip
	pip install -r requirements/requirements-core.txt

test: fmt lint
	pytest -q

run:
	python3 -m uvicorn huey.api:app --host 0.0.0.0 --port 0000

fmt:
	black . && isort .

lint:
	flake8 .

clean:
	rm -rf build dist .pytest_cache **/__pycache__ *.egg-info
	rm -rf .mypy_cache/ .ruff_cache/ .coverage htmlcov/

