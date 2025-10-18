import io
import json
import logging
import os

import boto3
from confluent_kafka import Consumer, Producer  # type: ignore
from mypy_boto3_s3.client import S3Client
from openai import OpenAI
from opentelemetry import propagate, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from PyPDF2 import PdfReader
from weaviate import Collection, WeaviateClient
from weaviate.collections import Collection as WeaviateCollection
from weaviate.collections.classes.config import DataType as WeaviateDataType
from weaviate.collections.classes.config import Property as WeaviateProperty
from weaviate.connect import ConnectionParams, ProtocolParams


def setup_tracing(service_name: str, endpoint: str = "http://jaeger:4318/v1/traces"):
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    trace.set_tracer_provider(provider)
    exporter = OTLPSpanExporter(endpoint=endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    return trace.get_tracer(service_name)


tracer = setup_tracing("service_embed_documents")

BOOTSTRAP_SERVERS = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
INPUT_TOPIC = os.environ["KAFKA_INPUT_TOPIC"]
OUTPUT_TOPIC = os.environ["KAFKA_OUTPUT_TOPIC"]
GROUP_ID = os.environ["KAFKA_GROUP_ID"]
OBJECT_STORAGE_URL = os.environ["OBJECT_STORAGE_URL"]
OBJECT_STORAGE_BUCKET = os.environ["OBJECT_STORAGE_BUCKET"]


def create_consumer():
    logging.info(f"Creating consumer with {BOOTSTRAP_SERVERS=}, {GROUP_ID=}")
    return Consumer(
        {
            "bootstrap.servers": BOOTSTRAP_SERVERS,
            "group.id": GROUP_ID,
            "auto.offset.reset": "earliest",
        }
    )


def create_producer():
    logging.info(f"Creating producer with {BOOTSTRAP_SERVERS=}")
    return Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})


def process_message(
    weaviate_collection: WeaviateCollection,
    openai_client: OpenAI,
    object_storage_client: S3Client,
    msg_value: dict[str, str],
) -> str:
    logging.info(f"Processing message: {msg_value}")
    current_span = trace.get_current_span()

    object_storage_bucket = msg_value["bucket"]
    key = msg_value["key"]
    file_type = msg_value["file_type"]
    model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

    with tracer.start_as_current_span("get_object"):
        object = object_storage_client.get_object(Bucket=object_storage_bucket, Key=key)
        object_body = object["Body"].read()

    if file_type == "pdf":
        with tracer.start_as_current_span("read_pdf"):
            reader = PdfReader(io.BytesIO(object_body))
            metadata = reader.metadata
            title = metadata.title if metadata and metadata.title else None
            author = metadata.author if metadata and metadata.author else None
            subject = metadata.subject if metadata and metadata.subject else None
            text = " ".join(page.extract_text() or "" for page in reader.pages)
            text = text[:1000]  # TODO: chunking
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    with tracer.start_as_current_span("embed_text"):
        response = openai_client.embeddings.create(
            input=text,
            model=model,
        )

    for d in response.data:
        embedding = d.embedding
        dimension = len(embedding)
        with tracer.start_as_current_span("store_embedding") as span:
            id = weaviate_collection.data.insert(
                properties={
                    "text": text,
                    "embedding_model": model,
                    "embedding_dim": dimension,
                    "bucket": object_storage_bucket,
                    "key": key,
                    "file_type": file_type,
                    "metadata_title": title,
                    "metadata_author": author,
                    "metadata_subject": subject,
                },
                vector=embedding,
            )
            span.set_attribute("embedding.model", model)
            span.set_attribute("embedding.id", str(id))

    current_span.set_attribute("object_storage.bucket", object_storage_bucket)
    current_span.set_attribute("object_storage.key", key)
    current_span.set_attribute("file.type", file_type)

    return json.dumps(
        {
            "bucket": object_storage_bucket,
            "key": key,
            "file_type": file_type,
        }
    )


def ensure_bucket(client: S3Client, bucket_name: str):
    if bucket_name in [b["Name"] for b in client.list_buckets()["Buckets"]]:
        logging.info(f"Bucket already exists: {bucket_name}")
        return
    logging.info(f"Creating bucket: {bucket_name}")
    client.create_bucket(Bucket=bucket_name)


def main() -> None:
    logging.info(f"{BOOTSTRAP_SERVERS=}")
    logging.info(f"{INPUT_TOPIC=}")
    logging.info(f"{OUTPUT_TOPIC=}")
    logging.info(f"{GROUP_ID=}")
    logging.info(f"{OBJECT_STORAGE_URL=}")
    logging.info(f"{OBJECT_STORAGE_BUCKET=}")

    consumer = create_consumer()
    producer = create_producer()
    object_storage_client: S3Client = boto3.client(
        "s3",
        endpoint_url=OBJECT_STORAGE_URL,
        aws_access_key_id=os.environ["OBJECT_STORAGE_USER"],
        aws_secret_access_key=os.environ["OBJECT_STORAGE_PASSWORD"],
    )
    ensure_bucket(object_storage_client, OBJECT_STORAGE_BUCKET)

    openai_client = OpenAI()

    with WeaviateClient(
        connection_params=ConnectionParams(
            http=ProtocolParams(host="weaviate", port=8080, secure=False),
            grpc=ProtocolParams(host="weaviate", port=50051, secure=False),
        )
    ) as weaviate_client:
        class_name = "DocumentChunk"
        if not weaviate_client.collections.exists(class_name):
            weaviate_client.collections.create(
                name=class_name,
                properties=[
                    WeaviateProperty(name="text", data_type=WeaviateDataType.TEXT),
                    WeaviateProperty(
                        name="embedding_model", data_type=WeaviateDataType.TEXT
                    ),
                    WeaviateProperty(
                        name="embedding_dim", data_type=WeaviateDataType.INT
                    ),
                    WeaviateProperty(name="bucket", data_type=WeaviateDataType.TEXT),
                    WeaviateProperty(name="key", data_type=WeaviateDataType.TEXT),
                    WeaviateProperty(name="file_type", data_type=WeaviateDataType.TEXT),
                    WeaviateProperty(
                        name="metadata_title", data_type=WeaviateDataType.TEXT
                    ),
                    WeaviateProperty(
                        name="metadata_author", data_type=WeaviateDataType.TEXT
                    ),
                    WeaviateProperty(
                        name="metadata_subject", data_type=WeaviateDataType.TEXT
                    ),
                ],
            )
        collection = weaviate_client.collections.get(class_name)

        consumer.subscribe([INPUT_TOPIC])

        try:
            while True:
                msg = consumer.poll(1.0)
                if msg is None or msg.error():
                    if msg is None:
                        logging.info("No message received")
                    elif msg.error():
                        logging.error(f"Consumer error: {msg.error()}")
                    continue
                value: dict[str, str] = json.loads(msg.value().decode("utf-8"))
                raw_headers = msg.headers() or []
                headers = {
                    k: v.decode("utf-8") for k, v in raw_headers if v is not None
                }
                ctx = propagate.extract(headers)

                with tracer.start_as_current_span("process_message", context=ctx):
                    result = process_message(
                        collection, openai_client, object_storage_client, value
                    )
                    carrier: dict[str, str] = {}
                    propagate.inject(carrier)
                    out_headers = [(k, v.encode("utf-8")) for k, v in carrier.items()]
                    producer.produce(
                        OUTPUT_TOPIC, result.encode("utf-8"), headers=out_headers
                    )
                    producer.flush()
        except KeyboardInterrupt:
            pass
        finally:
            consumer.close()


if __name__ == "__main__":
    main()
