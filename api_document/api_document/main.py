import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from kafka import KafkaProducer  # type: ignore
from opentelemetry import propagate, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.propagators.textmap import default_setter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    for i in range(10):
        try:
            producer = KafkaProducer(
                bootstrap_servers="kafka:9092",
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            app.state.producer = producer
            producer.bootstrap_connected()
            logging.info("Connected to Kafka")
            break
        except Exception as e:
            logging.warning(f"Kafka not available yet, retrying... ({i+1})")
            time.sleep(i)
    else:
        app.state.producer = None

    yield

    if producer:
        producer.close()


app = FastAPI(lifespan=lifespan)


class DocumentLandedEvent(BaseModel):
    path: str
    file_type: str
    file_source: str

def setup_tracing():
    provider = TracerProvider(
        resource=Resource.create({"service.name": "api_document"})
    )
    trace.set_tracer_provider(provider)
    exporter = OTLPSpanExporter(endpoint="http://jaeger:4318/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    return trace.get_tracer(__name__)

tracer = setup_tracing()

@app.middleware("http")
async def tracing_middleware(request: Request, call_next):
    ctx = propagate.extract(request.headers)
    with tracer.start_as_current_span(
        f"{request.method} {request.url.path}",
        context=ctx,
        kind=trace.SpanKind.SERVER,
    ) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        if request.client:
            span.set_attribute("http.client_ip", request.client.host)
        response = await call_next(request)
        span.set_attribute("http.status_code", response.status_code)
        return response


@app.post("/document/v1")
def document(doc: DocumentLandedEvent):
    producer: KafkaProducer | None = app.state.producer
    if producer is None:
        raise HTTPException(status_code=503, detail="Kafka not ready")

    event = doc.model_dump(mode="json")
    logging.info(f"Sending event to Kafka: {event}")

    carrier: dict[str, str] = {}
    propagate.inject(carrier, setter=default_setter)
    kafka_headers = [(k, v.encode("utf-8")) for k, v in carrier.items()]

    producer.send("document-landed", value=event, headers=kafka_headers)

    current_span = trace.get_current_span()
    current_span.set_attribute("doc.file_type", doc.file_type)
    current_span.set_attribute("doc.file_source", doc.file_source)
    current_span.set_attribute("doc.path", doc.path)
    trace_id = current_span.get_span_context().trace_id
    logging.info(f"[Service1] Trace ID: {trace_id:032x}")
    return {"status": "ok", "trace_id": f"{trace_id:032x}"}
