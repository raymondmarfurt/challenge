#from kafka import KafkaConsumer
import time
from json import loads
import logging
#logging.basicConfig(level=logging.DEBUG)
from collections import Counter
from pykafka import KafkaClient
from pykafka.common import OffsetType
client = KafkaClient(hosts="127.0.0.1:9092")
topic = client.topics['doodle']

print('init consumer')
consumer = topic.get_simple_consumer(
        use_rdkafka=False,
        #deserializer=lambda x: loads(x.decode('utf-8')),
        auto_offset_reset=OffsetType.EARLIEST)

print('start reading')
start_time = time.time()
i_cnt = 0
uid_cnt = Counter()
for message in consumer:
    i_cnt = i_cnt + 1
    #m_uid = message.value['uid'] 
    #uid_cnt[m_uid] = uid_cnt[m_uid] + 1
end_time = time.time()
print("processing time: " + str(end_time - start_time))
print("total processed: " + str(i_cnt))
print("messages per second " + str(i_cnt / (end_time - start_time)))
#print("number of unique uids: " + str(len(uid_cnt)))
