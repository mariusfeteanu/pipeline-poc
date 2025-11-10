FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends bash && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dist/embed_documents-0.1.0-py3-none-any.whl  .
RUN pip install --no-cache-dir embed_documents-0.1.0-py3-none-any.whl

EXPOSE 8000
CMD ["python", "-m", "embed_documents.main"]
