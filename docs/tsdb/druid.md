# Druid

## Links

* http://druid.io/docs/latest/
* http://druid.io/docs/0.8.0
  * sometime things are missing in latest

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







## Running the Wikipedia Cluster Example with Tranquility

## Other important Links

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
