FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends bash && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dist/api_document-0.1.0-py3-none-any.whl  .
RUN pip install --no-cache-dir api_document-0.1.0-py3-none-any.whl

EXPOSE 8000
CMD ["uvicorn", "api_document.main:app", "--host", "0.0.0.0", "--port", "8000"]
