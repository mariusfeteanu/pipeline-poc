# pipeline-poc

## Running and Removing Containers with Docker Compose

To start all services defined in this project:

```bash
docker compose up -d
```

To stop and remove all containers, networks, and volumes created by `docker compose up`:

```bash
docker compose down -v
```