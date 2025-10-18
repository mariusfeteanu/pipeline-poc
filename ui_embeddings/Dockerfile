FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends bash && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# streamlit does not support modules so we copy the scripts as is
COPY ui_embeddings/ ./ui_embeddings/

EXPOSE 8000
CMD ["streamlit", "run", "ui_embeddings/main.py", "--server.port", "8082"]
