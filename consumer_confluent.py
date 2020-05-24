import time
import datetime

## fast json parser
from orjson import loads
from orjson import dumps

## fast kafka client
from confluent_kafka import Consumer
from confluent_kafka import Producer

print('init consumer/producer')
conf = {'bootstrap.servers': "localhost:9092",
        'group.id': "auto_reset",
        'enable.auto.commit': False,
        'auto.offset.reset': 'smallest'}

consumer = Consumer(conf)
producer = Producer(conf)

print('start reading')
start_time = time.time()
i_cnt = 0
last_ts_min = -1

try:
    consumer.subscribe(['doodle'])

    while True:
        msg = consumer.poll(timeout=1.0)
        ## in batch-mode for historical data: during ramp-up, there
        ## are no messages. Once we have seen messages, the program
        ## must exit with the next timeout.
        if msg is None: 
            if i_cnt > 0:
                break
            else:
                continue

        ## copy/paste error handling. Never seen one of these errors.
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition event
                sys.stderr.write('%% %s [%d] reached end at offset %d\n' %
                                 (msg.topic(), msg.partition(), msg.offset()))
            elif msg.error():
                raise KafkaException(msg.error())
        else:
            ## total count of processed messages
            i_cnt = i_cnt + 1

            ## json deserialization
            json_data = loads(msg.value().decode('utf8'))

            ## extract elements
            ts = json_data['ts']
            uid = json_data['uid']

            ## current minute interval
            current_ts_min = ts//60*60 

            ## discard late arrivals
            if current_ts_min < last_ts_min:
                print("late arrival. Dropping.")
                continue

            ## if a new minute interval starts, write the result
            ## of the current one to kafka topic minuteStats
            if current_ts_min != last_ts_min:
                if last_ts_min > 0: ## skip first iteration
                    ts_min_str = datetime.datetime.utcfromtimestamp(last_ts_min)
                    print("Found " + str(len(minute_set)) + " unique users for minute " + str(ts_min_str))
                    producer.produce("minuteStats", value=dumps({"ts":last_ts_min, "ts_str":ts_min_str, "count":len(minute_set)}))

                last_ts_min = current_ts_min
                minute_set = set()

            ## add each uid to set. Length of set gives us number of unique
            ## uid elements
            minute_set.add(uid)

except KeyboardInterrupt:
        pass
finally:
    ## Close down consumer to commit final offsets.
    consumer.close()


took = time.time() - start_time
print("processing time: " + str(took))
print("total processed: " + str(i_cnt) + "/" + str(1000000))
print("message rate: " + str(i_cnt/took) + " frames per second")
