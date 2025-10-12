# pipeline-poc

## Running and Removing Containers with Docker Compose

To start all services defined in this project:

```bash
docker compose build api_document
docker compose build service_ingest_documents
docker compose build service_embed_documents
docker compose --profile all up -d
```

To stop and remove all containers, and networks created by `docker compose up`:
```bash
docker compose --profile all down
```

To stop and remove all containers, networks, and volumes created by `docker compose up`:
```bash
docker compose --profile all down -v
```

```
. ./scripts/trigger-ingest.sh
```


- [Minio](http://localhost:9090)    
- [Jaeger](http://localhost:16686)
- [Weaviate](http://localhost:8081/v1/objects)
