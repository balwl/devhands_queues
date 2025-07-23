start: docker-compose up

subscribe to all topics: nats sub '>'

publish:
nats pub topic test-message

nats pub topic.a test-a
nats pub topic.b test-b
nats pub topic.c.d test-c-d

nats pub topic.a test-a
nats pub topic.b test-b
nats pub topic.c.d test-c-d


Create consumer group with 2 workers: 
nats sub topic --queue grp1
nats sub topic --queue grp1
publish to consumer group: nats pub topic --count 10 '{{ID}} : {{Count}} : {{Random 5 5}}'


Create responder: nats reply topic 'RE: {{ Request }}'
Send request to responder: nats request topic test-request