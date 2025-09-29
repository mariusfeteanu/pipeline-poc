import logging
import os

from confluent_kafka import Consumer, Producer  # type: ignore

BOOTSTRAP_SERVERS = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
INPUT_TOPIC = os.environ["KAFKA_INPUT_TOPIC"]
OUTPUT_TOPIC = os.environ["KAFKA_OUTPUT_TOPIC"]
GROUP_ID = os.environ["KAFKA_GROUP_ID"]
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


def process_message(msg_value: str) -> str:
    logging.info(f"Processing message: {msg_value}")
    return msg_value.upper()


def main():
    logging.info(f"{BOOTSTRAP_SERVERS=}")
    logging.info(f"{INPUT_TOPIC=}")
    logging.info(f"{OUTPUT_TOPIC=}")
    logging.info(f"{GROUP_ID=}")
    logging.info(f"{OBJECT_STORAGE_BUCKET=}")

    consumer = create_consumer()
    producer = create_producer()
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
            value = msg.value().decode("utf-8")
            result = process_message(value)
            producer.produce(OUTPUT_TOPIC, result.encode("utf-8"))
            producer.flush()
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
