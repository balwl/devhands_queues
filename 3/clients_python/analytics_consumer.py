from confluent_kafka import Consumer, KafkaError, KafkaException
import yaml
import json
import time

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

consumer = Consumer({
    'bootstrap.servers': config['bootstrap.servers'],
    'group.id': 'analytics-group',
    'auto.offset.reset': 'earliest'
})
consumer.subscribe(['user-events'])

event_counts = {
    'page_view': 0,
    'click': 0,
    'purchase': 0
}
distinct_users = set()

def print_aggregates():
    print("Event Counts:")
    for event_type, count in event_counts.items():
        print(f"  {event_type}: {count}")
    print(f"Distinct Users: {len(distinct_users)}")

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
            user_id = event.get('user_id')
            if event_type in event_counts:
                event_counts[event_type] += 1
            if user_id is not None:
                distinct_users.add(user_id)

        # Print aggregates every 3 seconds
        if time.time() - start_time > 3:
            print_aggregates()
            start_time = time.time()
            # Reset aggregates for the next interval
            event_counts = {key: 0 for key in event_counts}
            distinct_users.clear()

except KeyboardInterrupt:
    pass
finally:
    # Close down consumer to commit final offsets
    consumer.close()
