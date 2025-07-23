from confluent_kafka import Producer
import json
import time
import random
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

producer_config = {
    'bootstrap.servers': config['bootstrap.servers'],
    'acks': '0',
}

producer = Producer(producer_config)

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

while True:
    event = {
        'event_type': 'page_view',
        'user_id': random.randint(1, 1000),
        'page_id': random.randint(1, 100),
        'timestamp': time.time()
    }
    producer.produce(
        'user-events',
        key=str(event['user_id']),
        value=json.dumps(event),
        callback=delivery_report
    )
    producer.poll(0)
    time.sleep(0.3 + random.random() / 2)