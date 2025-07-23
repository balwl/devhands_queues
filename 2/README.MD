Start kafka: docker-compose up<br />
<br />
Start producers (from clients_python dir):<br />
docker-compose exec kafka-client python ./click_producer.py<br />
docker-compose exec kafka-client python ./purchase_producer.py<br />
docker-compose exec kafka-client python ./page_view_producer.py<br />
<br />
Start consumers (from clients_python dir):<br />
docker-compose exec kafka-client python ./monitoring_consumer.py<br />
docker-compose exec kafka-client python ./analytics_consumer.py
