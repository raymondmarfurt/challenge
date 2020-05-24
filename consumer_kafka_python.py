from kafka import KafkaConsumer
from json import loads
import logging
import time
#logging.basicConfig(level=logging.DEBUG)

print('init consumer')
consumer = KafkaConsumer(
        'doodle',
        group_id=None,
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='earliest',
        request_timeout_ms=8000,
        session_timeout_ms=5000,
        consumer_timeout_ms=6000,
        value_deserializer=lambda x: loads(x.decode('utf-8')))

print('start reading')
start_time = time.time()
i_cnt = 0
from collections import Counter
uid_cnt = Counter()
for message in consumer:
    i_cnt = i_cnt + 1
    m_uid = message.value['uid'] 
    uid_cnt[m_uid] = uid_cnt[m_uid] + 1
end_time = time.time()
print("processing time: " + str(end_time - start_time))
print("total processed: " + str(i_cnt))
print("messages per second: " + str(i_cnt / (end_time - start_time)))
