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
    for i in range(5):
        try:
            producer = KafkaProducer(
                bootstrap_servers="kafka:9092",
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            # Test the connection
            producer.bootstrap_connected()
            logging.info("Connected to Kafka")
            break
        except Exception as e:
            logging.warning(f"Kafka not available yet, retrying... ({i+1}/5)")
            time.sleep(5)
    logging.error("Failed to connect to Kafka after several attempts")

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
    logging.info(f"Sending event to Kafka: {event}")
    producer.send("document-landed", event)
