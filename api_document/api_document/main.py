from fastapi import FastAPI
from pydantic import BaseModel
from kafka import KafkaProducer
import json
import logging
import time

app = FastAPI()

producer = None

@app.on_event("startup")
def startup_event():
    global producer
    time.sleep(5)
    producer = KafkaProducer(
        bootstrap_servers="kafka:9092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

@app.on_event("shutdown")
def shutdown_event():
    if producer:
        producer.close()

class DocumentLandedEvent(BaseModel):
    path: str
    file_type: str
    file_source: str

@app.post("/document/v1")
def create_item_event(doc: DocumentLandedEvent):
    event = doc.model_dump(mode="json")
    logging.debug(f"Sending event to Kafka: {event}")
    producer.send("document-landed", event)
