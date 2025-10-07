```bash
python3 -m venv .venv
. .venv/bin/activate

pip install .[dev]
pip-compile pyproject.toml --output-file=requirements.txt  # to speed up dcker build

mypy embed_documents
black embed_documents
isort --profile=black embed_documents

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
