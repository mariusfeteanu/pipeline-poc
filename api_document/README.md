```bash
python3 -m venv .venv
. .venv/bin/activate
pip-compile pyproject.toml --output-file=requirements.txt  # to speed up dcker build
pip install .[dev]
```


```bash
curl -X POST "http://localhost:8000/document/v1" \
  -H "Content-Type: application/json" \
  -d '{"path": ".data/papers/cs.CL/pdf/2509.20490v1.pdf", "file_type": "pdf", "file_source": "arxiv"}'
```

```bash
docker exec -it kafka \
  kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic document-landed \
  --from-beginning
```
