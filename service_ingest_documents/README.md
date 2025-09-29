```bash
python3 -m venv .venv
. .venv/bin/activate

pip-compile pyproject.toml --output-file=requirements.txt  # to speed up dcker build
pip install .[dev]

mypy ingest_documents
black ingest_documents
isort --profile=black ingest_documents

python -m build --wheel
```


```bash
curl -X POST "http://localhost:8000/document/v1" \
  -H "Content-Type: application/json" \
  -d '{"path": ".data/papers/cs.CL/xml/2509.20321v1.xml", "file_type": "xml", "file_source": "arxiv"}'
```

```bash
docker exec -it kafka \
  kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic document-stored \
  --from-beginning
```
