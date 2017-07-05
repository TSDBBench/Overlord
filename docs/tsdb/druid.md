# Druid

## Links

* http://druid.io/docs/latest/
* http://druid.io/docs/0.8.0

## Information

* "high-performance, column-oriented, distributed data store"
* Real-time Analysis
* Has five node types:  Historical, Coordinator, Broker, Realtime, Indexing Service
* Supports multiple Ingestion methods
  * Two of them would be suitable for YCSB_TS:
    * [Realtime Data Ingestion](http://druid.io/docs/latest/ingestion/realtime-ingestion.html) via REST HTTP
      * Requires Realtime Node
      * Uses EventReceiverFirehose
      * Not very well documented
      * Should not be used ([source](https://groups.google.com/forum/#!topic/druid-development/DR89YlMzyKU))
    * Tranquility (Finagle Service)
        * Requires Coordinator, Historical, Overlord, Broker, and Middlemanager Node or Indexing Service
        * See "Batch Ingestionn Using the Indexing Service" [here](http://druid.io/docs/latest/ingestion/batch-ingestion.html)
        * All can be installed on the same node
        * [Tranquility](https://github.com/druid-io/tranquility) is the Java library for the client
* Multiple Deep Storages supported: local FS, HDFS, and S3
* Kafka is not recommended:
    * Does not scale very well compared to Tranquility/Finagle ([souce](https://groups.google.com/forum/#!searchin/druid-development/fangjin$20yang$20%22thoughts%22/druid-development/aRMmNHQGdhI/muBGl0Xi_wgJ))
* Supported query granularities:  none (ms when ms was ingested), minute, fifteen_minute, thirty_minute, hour, day, or all (one bucket) 
    
## Implementation Notes

* Using tranquility 0.4.2
    * 0.5.0 does not work from Maven
* No inserts into past possible, even with 1 year windowperiod and a fitting SegmentGranularity
* Tagnames have to be deinfed as dimensions before using
* SUM as aggregating function is available in two flavours: LongSum (for 64bit integer) and DoubleSum (for 64bit floating point)
    * Using DoubleSum in TSDBBench, changable via flag
* AVG is only available as post-aggregation function
    * Uses SUM + Count as preceding functions
* Replication of five is not possible in a five not cluster setup, since 5 historical nodes would be required.
    * The idea of replication if to achieve a higher availabily (see https://groups.google.com/forum/#!topic/druid-development/0TBL5-3Z2PI)

## Steps to setup Druids Cluster Wikipedia Example with Overload (for Tranquility)
* Old:
    * `wget http://static.druid.io/artifacts/releases/druid-0.8.0-bin.tar.gz`
    * `tar -xvzf druid-0.8.0-bin.tar.gz`
    * `sudo apt-get install zookeeperd mysql-server`
    * `sudo systemctl start zookeeper.service`
    * `cd druid-0.8.0`
    * `mysql -uroot -e 'CREATE DATABASE druid DEFAULT CHARACTER SET utf8; GRANT ALL PRIVILEGES ON druid.* TO druid IDENTIFIED BY "diurd";'`
    * `nano examples/wikipedia/wikipedia_realtime.spec`:
        * "segmentGranularity": "HOUR", -> "segmentGranularity": "FIVE_MINUTE",
        * "intermediatePersistPeriod": "PT10m", -> "intermediatePersistPeriod": "PT3m",
        * "windowPeriod": "PT10m", -> "windowPeriod": "PT1m",
* execute in parallel (can take some time when running the first time due to extension loading):
    * `java -Xmx256m -Duser.timezone=UTC -Dfile.encoding=UTF-8 -classpath config/_common:config/coordinator:lib/* io.druid.cli.Main server coordinator`
    * `java -Xmx256m -Duser.timezone=UTC -Dfile.encoding=UTF-8 -classpath config/_common:config/historical:lib/* io.druid.cli.Main server historical`
    * `java -Xmx256m -Duser.timezone=UTC -Dfile.encoding=UTF-8 -classpath config/_common:config/broker:lib/* io.druid.cli.Main server broker`
    * `java -Xmx256m -Duser.timezone=UTC -Dfile.encoding=UTF-8 -classpath config/_common:config/overlord:lib/* io.druid.cli.Main server overlord`
* If a "real" Index Service is required:
    * `java -Xms64m -Xmx64m -Duser.timezone=UTC -Dfile.encoding=UTF-8 -classpath config/_common:config/middlemanager:lib/* io.druid.cli.Main server middleManager`
* New with script (2015-10-13):
    * `sudo systemctl start zookeeper.service` (if not running)
    * `./run.bash` 

## Other Related Links

* https://github.com/gianm/druid-monitorama-2015
* https://github.com/jwang93/test-druid/wiki/MySQL-Setup
* http://curator.apache.org/index.html
* https://github.com/druid-io/tranquility
* https://github.com/mark1900/druid-sandbox/tree/master/kafka-storm-tranquility-druid-topology-test
* https://groups.google.com/forum/#!forum/druid-development
* https://groups.google.com/forum/#!forum/druid-user
* Important on Google Groups:
  * https://groups.google.com/forum/#!topic/druid-user/qgfKipXPzeE
  * https://groups.google.com/forum/#!topic/druid-development/eIiuSS-fM8I
  * https://groups.google.com/forum/#!topic/druid-development/Siwd4gA7Yjg
* Important on Google Groups on Problems with Tranquility:
  * https://groups.google.com/forum/#!topic/druid-development/PU6njY0gE5U
  * https://groups.google.com/forum/#!topic/druid-user/UT5JNSZqAuk
  * https://github.com/druid-io/druid/issues/1448
  * https://groups.google.com/forum/#!topic/druid-user/LKqvur7wWmo
  * https://groups.google.com/forum/#!topic/druid-user/1YsRnLPMkhw
  * https://groups.google.com/forum/#!topic/druid-user/IKJXd1d51TM
* http://brianoneill.blogspot.de/2015/09/druid-vagrant-up-and-tranquility.html
* https://github.com/Quantiply/druid-vagrant
* https://github.com/boneill42/druid-vagrant
* http://www.datascienceassn.org/sites/default/files/users/user1/DruidDataIngest_0.6.62.pdf

[back](../../)
