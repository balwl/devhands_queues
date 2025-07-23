from confluent_kafka import Consumer, KafkaError, KafkaException
import yaml
import json
import time

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

consumer = Consumer({
    'bootstrap.servers': config['bootstrap.servers'],
    'group.id': 'monitoring-group',
    'auto.offset.reset': 'earliest'
})
consumer.subscribe(['user-events'])

purchase_count = 0
total_amount = 0.0

def print_aggregates():
    print(f"Purchases in last 15 seconds: {purchase_count}")
    print(f"Total amount in last 15 seconds: ${total_amount:.2f}")

try:
    start_time = time.time()
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                print(f'End of partition reached {msg.topic()} [{msg.partition()}]')
            elif msg.error():
                raise KafkaException(msg.error())
        else:
            event = json.loads(msg.value().decode('utf-8'))
            event_type = event.get('event_type')
            if event_type == 'purchase':
                purchase_count += 1
                total_amount += event.get('amount', 0.0)

        if time.time() - start_time > 15:
            print_aggregates()
            start_time = time.time()
            purchase_count = 0
            total_amount = 0.0
except KeyboardInterrupt:
    pass
finally:
    # Close down consumer to commit final offsets
    consumer.close()
