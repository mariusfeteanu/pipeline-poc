import json
import logging
import os

import boto3
from confluent_kafka import Consumer, Producer  # type: ignore
from mypy_boto3_s3.client import S3Client

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


def process_message(object_storage_client: S3Client, msg_value: dict[str, str]) -> str:
    logging.info(f"Processing message: {msg_value}")
    path = msg_value["path"]
    key = path
    if key.startswith("/"):
        key = path[1:]
    if key.startswith(".data/"):
        key = key[len(".data/") :]
    file_type = msg_value.get("file_type", key.split(".")[-1] if "." in key else "n/a")
    file_source = msg_value.get("file_source", "n/a")
    with open(path, "rb") as f:
        content = f.read()
        object_storage_client.put_object(
            Bucket=OBJECT_STORAGE_BUCKET,
            Key=key,
            Body=content,
            Metadata={
                "file_type": file_type,
                "file_source": file_source,
                "original_path": path,
            },
        )
    logging.info(f"Uploaded {path} to bucket {OBJECT_STORAGE_BUCKET} with key {key}")
    return json.dumps(
        {
            "bucket": OBJECT_STORAGE_BUCKET,
            "key": key,
            "file_type": file_type,
            "file_source": file_source,
            "original_path": path,
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
            result = process_message(object_storage_client, value)
            producer.produce(OUTPUT_TOPIC, result.encode("utf-8"))
            producer.flush()
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
