# blueflood

## Links

* http://blueflood.io/
* https://github.com/rackerlabs/blueflood

## Information

* Uses Cassandra
* Does not support TAGs ([source](https://github.com/rackerlabs/blueflood/wiki/FAQ))
* Does not support SUM ([source](https://github.com/rackerlabs/blueflood/wiki/10minuteguide#send-numeric-metrics))
  * Using MIN instead of SUM in YCSB-TS
* Elastic Search (ES) is optional for searching metrics (not needed for YCSB-TS, only using one known metric)
* Unclear how to combine multiple instances of blueflood
    * Zookeeper can be used to coordinate Rollups and shard locking ([Source1](https://github.com/rackerlabs/blueflood/wiki/Deployment-Dependencies), [Source2](https://github.com/rackerlabs/blueflood/blob/master/blueflood-core/src/main/java/com/rackspacecloud/blueflood/service/CoreConfig.java))
    * Unclear if and how load can be distributed
    * Multiple cassandra nodes can be used for one shard. If one node fails, a non-failing one takes over.
* Only support for the following granularities: 5, 60, 240, 1440
* Due to the size of the .jar file (72 MB) and a long buildprocess, the jar file is downloaded in TSDBBench instead of built everytime

## How to install/build:

* sudo apt-get install maven openjdk-7-jdk
* git clone https://github.com/rackerlabs/blueflood.git
* cd blueflood
* mvn test integration-test
* mvn package -P all-modules
* The result (if the build process was successful) is in blueflood-all/target/blueflood-all-2.0.0-SNAPSHOT-jar-with-dependencies.jar
* Go on with the [10 Minuten Guide](https://github.com/rackerlabs/blueflood/wiki/10minuteguide)


[back](../../)
