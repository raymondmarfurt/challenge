# Data Engineer Challenge

## Installation

### Kafka Infrastructure
| Step | Description | Command (arch Linux)  |
|--|--|--|
| 1 | install docker| `pacman -S docker` |
| 2 | install docker compose  | `pacman -S docker-compose` |
| 3 | start docker service | `systemctl start docker` |
| 4 | download bitname docker compose file with Kafka broker and zookeeper instance | `curl -sSL https://raw.githubusercontent.com/bitnami/bitnami-docker-kafka/master/docker-compose.yml > docker-compose.yml` |
| 6 | create persistent data store  | `mkdir kafka_data` | 
| 7 | edit yml file | see updated version. Adapt absolute path to `kafka_data` if necessary  | 
| 8 | start docker compose configuration | `docker-compose up -d` | 
| 9 | verify processes are running | `docker-compose ps` | 
| 10 | create Kafka topic | `docker exec -it bitnami_kafka_1 kafka-topics.sh --create --topic doodle --partitions 1 --replication-factor 1 --bootstrap-server :9092` | 
| 11 | unzip data (because gunzip not available in docker image) | `gunzip kafka_data/stream.jsonl.gz` | 
| 12a | load the data | <code>docker exec -ti bitname_kafka_1 bash</code>| 
| 12b | load the data | <code>cat stream.jsonl &#124; kafka-console-producer.sh --broker-list localhost:9092 --topic doodle </code>| 
| 13| create topic for result output | `docker exec -it bitnami_kafka_1 kafka-topics.sh --create --topic minuteStats --partitions 1 --replication-factor 1 --bootstrap-server :9092`|

### Python Environment
| Step |Description|Command (arch Linux)|
|--|--|--|
|1|install python|`pacman -S python`|
|2|install packages|`pip install orjson`<br>`pip install confluent_kafka`|
|3|install high performance kafka client library | `pacman -S librdkafka`|

## Run the Calculation
<code>
python consumer_confluent.py <br>
init consumer<br>
start reading<br>
Found 16193 unique users for minute 2016-07-11 13:39:00<br/>
Found 41130 unique users for minute 2016-07-11 13:40:00<br/>
Found 47369 unique users for minute 2016-07-11 13:41:00<br>
Found 49488 unique users for minute 2016-07-11 13:42:00<br>
Found 47863 unique users for minute 2016-07-11 13:43:00<br>
Found 40439 unique users for minute 2016-07-11 13:44:00<br>
Found 42859 unique users for minute 2016-07-11 13:45:00<br>
Found 47312 unique users for minute 2016-07-11 13:46:00<br>
Found 48180 unique users for minute 2016-07-11 13:47:00<br>
Found 47981 unique users for minute 2016-07-11 13:48:00<br>
Found 42194 unique users for minute 2016-07-11 13:49:00<br>
Found 45070 unique users for minute 2016-07-11 13:50:00<br>
Found 43659 unique users for minute 2016-07-11 13:51:00<br>
Found 48611 unique users for minute 2016-07-11 13:52:00<br>
Found 42742 unique users for minute 2016-07-11 13:53:00<br>
Found 51930 unique users for minute 2016-07-11 13:54:00<br>
Found 45471 unique users for minute 2016-07-11 13:55:00<br>
processing time: 21.095016717910767<br>
total processed: 1000000/1000000<br>
message rate: 47404.560677638525 frames per second<br>
</code>

## Report
### Kafka Setup
At home, I am running Arch Linux, which makes it somewhat more difficult to set up  Kafka and Zookeeper. I therefore decided to try a ready-made docker image. Additionally, I could finally get to know docker.

I first tried https://hub.docker.com/r/wurstmeister/kafka/, but did not manage to get Kafka and Zookeeper to talk to each other. Unfortunately, I lost quite some time here. Finally, I switched to https://github.com/bitnami/bitnami-docker-kafka, which worked like a breeze.

### Programming Language
I decided to go with python, because it sped up my code writing for this challenge.

### Initial throughput test
I did basic message reading from kafka topic (see consumer_non_processing.py; although I used a different client initially), to see pure performance on kafka message consuming, without deserializing and processing of message values.
<code>
python consumer_non_processing.py 
init consumer/producer
start reading
processing time: 6.327501535415649
total processed: 1000000/1000000
message rate: 158040.26192690773 frames per second
</code>

*Thoughts*
During this test, I see kafka's java process uses about 20% of a Core, the client's python process about 80%. This means that processing is limited by IO, not by CPU. 
Adding JSON parsing in the next step shows that the java process is at about 8% and python at 100%. I.e. the consumer is now CPU bound, caused by message processing and JSON parsing.
### Basic Kafka Client and JSON Parser
consumer_kafka_python.py is a test implementation to measure throughput with standard python libraries.
<code>
python consumer_kafka_python.py 
init consumer
start reading
processing time: 54.371084213256836
total processed: 1000000
messages per second: 18392.12909710891
</code>

### Optimizations
The optimizations below show are about 2.5 times more performant than the native python implementation.
#### Kafka Client
I first switch to pykafka for optimized kafka message processing. It uses librdkafka as a backend, but seems to be incompatible in its current version.
I then tried confluent kafka, which played well with librdkafka and showed good performance.
#### JSON Parser
The replacement of json with orjson gave significant performance improvements (measured, but not shown in this report).
## Result
consumer_confluent.py writes the result back to kafka topic minuteStats.
The data structure is a minimalist JSON structure, containing

 - `ts`: timestamp to the minute in epoch format
 - `ts_str`: human readable timestamp
 - `count`: unique uids during minute interval

## Limitations and Next Steps
  - Each minute interval's output value is calculated when the next minute interval is detected. This should be changed to comparing with current time, because there might be no next interval, or it comes some time later
  - The current solution allows only a kafka topic with one partition. Additional logic must be added for multiple consumer threads on multiple partitions
  - For the purpose of this exercise (with no live data stream), I do not commit at all, so that I can re-read the whole stream with each consumer start. To cope with application failures, this needs to be changed. In order to correctly handle late arrivals, I would not set auto commit, but do it explicitly when the client has calculated an interval
  - For day/month/year calculations, we need to enhance the result data structure to be able to further aggregate results from smaller timespans. I am not yet sure how; one possibility would be to store unique uid's per interval to a topic to later combine with other intervals, but this results in large messages, which might not be ideal
  - Late arrivals are dropped. There is currently no logic for random timestamps, but it would be easy to add an additional check and drop timestamps that are way off the current time
  - For scaling, the obvious choice would be to add kafka nodes and increase partitions. Both will require additional logic in the consumer. Besides the architectural changes, we can
    * migrate to Java client and compare performance
    * tune kafka and consumer/producer parameter, e.g. buffer sizes 
  - File format: JSON for sure is a good choice. From a pure performance perspective, CSV has advantages - but of course many disadvantages. An alternative would be Avro. For Avro, as for other optimized formats, a schema is necessary. This would be beneficial anyway to validate input data. But is not (or hardly?) possible with the suggested input data, which shows variations in its format.


