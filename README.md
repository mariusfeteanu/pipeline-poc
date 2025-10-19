# pipeline-poc

## Running and Removing Containers with Docker Compose

To start all services defined in this project:

```bash
docker compose build api_document
docker compose build service_ingest_documents
docker compose build service_embed_documents
docker compose build ui_embeddings
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
- [Weaviate Objects](http://localhost:8081/v1/objects) [Schema](http://localhost:8081/v1/schema)
- [Embeddings UI](http://localhost:8082)
- [Prometheus](http://localhost:9091/query?g0.expr=sum%28increase%28calls_total%5B5m%5D%29%29+by+%28service_name%29&g0.show_tree=0&g0.tab=graph&g0.range_input=1h&g0.res_type=fixed&g0.res_step=60&g0.display_mode=lines&g0.show_exemplars=0)
