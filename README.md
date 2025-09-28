# pipeline-poc

## Running and Removing Containers with Docker Compose

To start all services defined in this project:

```bash
docker compose up -d
docker compose --profile minio up -d
```

To stop and remove all containers, networks, and volumes created by `docker compose up`:

```bash
docker compose --profile minio down -v
docker compose down -v

docker compose -p pipeline-poc down -v --remove-orphans
```
