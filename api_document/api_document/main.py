import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from kafka import KafkaProducer  # type: ignore
from pydantic import BaseModel

producer: KafkaProducer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer
    for i in range(5):
        try:
            producer = KafkaProducer(
                bootstrap_servers="kafka:9092",
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            producer.bootstrap_connected()
            logging.info("Connected to Kafka")
            break
        except Exception as e:
            logging.warning(f"Kafka not available yet, retrying... ({i+1})")
            time.sleep(5)

    yield  # yield to application

    if producer:
        producer.close()


app = FastAPI(lifespan=lifespan)


class DocumentLandedEvent(BaseModel):
    path: str
    file_type: str
    file_source: str


@app.post("/document/v1")
def create_item_event(doc: DocumentLandedEvent):
    global producer
    assert producer is not None, "Producer not initialized"
    event = doc.model_dump(mode="json")
    logging.info(f"Sending event to Kafka: {event}")
    producer.send("document-landed", event)
