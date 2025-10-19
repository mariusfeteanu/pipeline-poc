#!/usr/bin/env bash
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

. .venv/bin/activate

pip-compile pyproject.toml --output-file=requirements.txt
pip install .[dev]

mypy ingest_documents
black ingest_documents
isort --profile=black ingest_documents

python -m build --wheel
