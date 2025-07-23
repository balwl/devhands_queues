import os
import json
import time
import random
import psycopg2
from confluent_kafka import Producer, KafkaException

DATABASE_URL = os.getenv("DATABASE_URL")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transactions")
FAULTY = float(os.getenv("FAULTY", 0))
def random_fail():
    if FAULTY:
        r = random.random()
        if r < FAULTY:
            raise Exception(f"Something went wrong... Status unknown {r}.")

def delivery_report(err, msg, cursor, message_id):
    if err is not None:
        print(f"Message {message_id} delivery failed: {err}")
    else:
        print(f"Message {message_id} delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")
        random_fail()
        cursor.execute("UPDATE outbox SET processed = TRUE WHERE id = %s;", (message_id,))
        # cursor.execute("DELETE FROM outbox WHERE id = %s;", (message_id,))

def get_db_connection():
    while True:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except Exception as e:
            print("Failed to connect to database: ", e)
            time.sleep(1)

def main():
    producer = Producer({
        'bootstrap.servers': KAFKA_BROKER,
        'enable.idempotence': True,
        'acks': 'all',
        'retries': 5,
        'linger.ms': 100,
        'batch.size': 16384
    })

    conn = None
    cursor = None
    while True:
        try:
            if conn is None:
                conn = get_db_connection()
                conn.autocommit = True
                cursor = conn.cursor()

            cursor.execute("SELECT id, account_id, transaction_id, payload FROM outbox WHERE processed = FALSE order by id limit 1 FOR UPDATE")
            unprocessed_messages = cursor.fetchall()

            for message_id, account_id, transaction_id, payload in unprocessed_messages:
                print(message_id, account_id, transaction_id, payload)

                r = producer.produce(
                    KAFKA_TOPIC,
                    key=str(account_id),
                    value=json.dumps(payload),
                    callback=lambda err, msg: delivery_report(err, msg, cursor, message_id)
                )

                random_fail()

            if unprocessed_messages:
                producer.flush()

        except KafkaException as e:
            print(f"Failed to send message to Kafka: {e}")

        except Exception as e:
            print(f"Error processing outbox: {e}")
            conn.close()
            conn = None
            if cursor:
                cursor.close()

        time.sleep(0.1)

if __name__ == "__main__":
    main()
