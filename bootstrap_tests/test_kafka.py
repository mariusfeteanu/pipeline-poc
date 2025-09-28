from kafka import KafkaProducer, KafkaConsumer
import time

def test_kafka():
    TOPIC = "test-topic"
    BOOTSTRAP_SERVERS = ["localhost:9092"]

    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    producer.send(TOPIC, b"derp!")
    producer.flush()
    print("Message produced")

    for i in range(1):
        time.sleep(1)
        print(f"{i} ", end="", flush=True)
    print("\nStarting consumer...")

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="test-group",
    )

    for msg in consumer:
        print(f"Received: {msg.value.decode()}")
        break
