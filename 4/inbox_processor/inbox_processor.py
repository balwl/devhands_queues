import os
import json
import time
import decimal
import random
import psycopg2
from confluent_kafka import Consumer, KafkaException, KafkaError

DATABASE_URL = os.getenv("DATABASE_URL")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transactions")
FAULTY = float(os.getenv("FAULTY", 0))
def random_fail():
    if FAULTY:
        if random.random() < FAULTY:
            raise Exception("Something went wrong... Status unknown.")

def init_db(conn):
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inbox (
        transaction_id BIGINT PRIMARY KEY,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS balance (
        account_id INT PRIMARY KEY,
        current_balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    conn.commit()
    cursor.close()

def get_db_connection():
    while True:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except Exception as e:
            print("Failed to connect to database: ", e)
            time.sleep(1)

def main():
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'inbox_processor',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,
        'group.instance.id': 'the_only_client',
    })

    notice = False

    while True:
        try:
            meta = consumer.list_topics(topic = KAFKA_TOPIC, timeout=5).topics[KAFKA_TOPIC]
            if not meta.partitions or meta.error and meta.error.code == KafkaError.UNKNOWN_TOPIC_OR_PART:
                if not notice:
                    print("Waiting for topic to be available...")
                    notice = True
                time.sleep(1)
            else:
                consumer.subscribe([KAFKA_TOPIC])
                break
        except Exception as e:
            print(f"Error getting meta for topic: {e}")
            time.sleep(1)

    conn = get_db_connection()
    init_db(conn)
    cursor = conn.cursor()

    notice = False
    msg = None

    while True:
        if msg is None:
            msg = consumer.poll(1.0)

        if msg is None:
            if not notice:
                print("Wait for messages")
            notice = True
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()} at offset {msg.offset()}")

            if msg.error().code() == KafkaError._PARTITION_EOF:
                print(f"End of partition reached {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
                continue
            elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                if not notice:
                    print("Waiting for topic to appear...")
                    notice = True
                time.sleep(1)
                continue
            elif msg.error():
                print(f"Consumer error: {msg.error()} at offset {msg.offset()}")
                raise KafkaException(msg.error())

        notice = False

        if not conn:
            conn = get_db_connection()
            cursor = conn.cursor()

        transaction_id = None
        try:
            payload = json.loads(msg.value().decode('utf-8'))
            transaction_id = payload['transaction_id']
            print(f"Processing {transaction_id} at {msg.offset()}...")
            account_id = payload['account_id']
            amount = decimal.Decimal(payload['amount'])
            transaction_type = payload['transaction_type']

            random_fail()

            cursor.execute('SELECT 1 FROM inbox WHERE transaction_id = %s;', (transaction_id,))
            if cursor.fetchone():
                print(f"Transaction {transaction_id} already processed. Commit offset {msg.offset()}")
                consumer.commit(message=msg)
                msg = None
                continue

            if transaction_type == "WITHDRAWAL" and amount > 0:
                amount = -amount

            cursor.execute('''
                INSERT INTO balance (account_id, current_balance, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (account_id) DO UPDATE SET current_balance = balance.current_balance + EXCLUDED.current_balance, updated_at = NOW();
            ''', (account_id, amount))

            random_fail()

            cursor.execute('INSERT INTO inbox (transaction_id) VALUES (%s);', (transaction_id,))

            conn.commit()

            random_fail()

            consumer.commit(message=msg)
            print(f"Processed transaction {transaction_id} for account {account_id}. Commit offset {msg.offset()}")
            msg = None

        except Exception as e:
            print(f"Failed to process message {transaction_id}: {e} at offset {msg.offset()}")
            conn.rollback()
            cursor.close()
            conn.close()
            conn = None

if __name__ == "__main__":
    main()
