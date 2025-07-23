from confluent_kafka import Producer
import json
import time
import random
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

producer_config = {
    'bootstrap.servers': config['bootstrap.servers'],
    'acks': 'all',
}
producer = Producer(producer_config)

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

while True:
    user_id = random.randint(1, 1000)
    event = {
        'event_type': 'purchase',
        'user_id': user_id,
        'product_id': random.randint(1, 1000),
        'amount': random.uniform(10.0, 500.0),
        'timestamp': time.time()
    }
    producer.produce(
        'user-events',
        key=str(user_id),
        value=json.dumps(event),
        callback=delivery_report
    )
    producer.poll(0)
    time.sleep(3+random.random()*2)
