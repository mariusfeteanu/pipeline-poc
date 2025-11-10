#!/usr/bin/env bash
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

. .venv/bin/activate

pip-compile pyproject.toml --output-file=requirements.txt
pip install .[dev]

mypy api_document
black api_document
isort --profile=black api_document

python -m build --wheel
