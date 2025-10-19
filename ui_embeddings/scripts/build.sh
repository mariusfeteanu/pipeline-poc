#!/usr/bin/env bash
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

. .venv/bin/activate

pip-compile pyproject.toml --output-file=requirements.txt
pip install .[dev]

mypy ui_embeddings
black ui_embeddings
isort --profile=black ui_embeddings
