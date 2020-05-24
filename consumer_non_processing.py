import time
import datetime


## fast kafka client
from confluent_kafka import Consumer

print('init consumer/producer')
conf = {'bootstrap.servers': "localhost:9092",
        'group.id': "auto_reset",
        'enable.auto.commit': False,
        'auto.offset.reset': 'smallest'}

consumer = Consumer(conf)

print('start reading')
start_time = time.time()
i_cnt = 0

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

except KeyboardInterrupt:
        pass
finally:
    ## Close down consumer to commit final offsets.
    consumer.close()


took = time.time() - start_time
print("processing time: " + str(took))
print("total processed: " + str(i_cnt) + "/" + str(1000000))
print("message rate: " + str(i_cnt/took) + " frames per second")
