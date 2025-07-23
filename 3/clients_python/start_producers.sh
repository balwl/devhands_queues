#!/bin/bash

python ./click_producer.py &
python ./purchase_producer.py &
python ./page_view_producer.py &
tail -f /dev/null