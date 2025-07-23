start: docker-compose up

make transaction: python3 tx.py -u 1 -a 10
retry transaction: python3 tx.py -u 1 -a 10 -i <transaction_id>

watch FROM db: watch -n 1 'docker-compose exec db_transactions psql -U postgres transactions_db -c "select * from balance"'
watch TO db: watch -n 1 'docker-compose exec db_balance psql -U postgres balance_db -c "select * from balance"'
