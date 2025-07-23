Start kafka: docker-compose up

Start producers (from clients_python dir):
docker-compose exec kafka-client python ./click_producer.py
docker-compose exec kafka-client python ./purchase_producer.py
docker-compose exec kafka-client python ./page_view_producer.py

Start consumers (from clients_python dir):
docker-compose exec kafka-client python ./monitoring_consumer.py
docker-compose exec kafka-client python ./analytics_consumer.py
