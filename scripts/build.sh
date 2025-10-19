#!/usr/bin/env bash
service=$1

build_service() {
    (cd "$1";scripts/build.sh)
    docker compose build "$1"
}

if [ -n "$service" ]; then
    build_service "$service"
else
    build_service api_document
    build_service service_ingest_documents
    build_service service_embed_documents
    build_service ui_embeddings
    build_service ui_chat
fi
