# KairosDB

## Links

* https://kairosdb.github.io/
* https://github.com/kairosdb/kairosdb

## Information

* 3 possible variants:
    * KairosDB with H2 (slow, only for testing)
    * KairosDB with HBase (deprecated, does not support seconds(?))
    * KairosDB with Cassandra
* When using READ() only a timerange (not a timestamp) is supported
* Status can be seen with `nodetool status`
* Performance notes: https://code.google.com/p/kairosdb/wiki/GettingStarted#Configuring_Cassandra
* Hardware notes: https://wiki.apache.org/cassandra/CassandraHardware
* Cassandra Cluster setup hints:
    * http://docs.datastax.com/en/cassandra/1.2/cassandra/initialize/initializeSingleDS.html
    * https://www.digitalocean.com/community/tutorials/how-to-configure-a-multi-node-cluster-with-cassandra-on-a-ubuntu-vps

## Implementation Notes

* Cassandra 22X did not work, error: "all host pools marked down. Retry burden pushed out to client"
* Cassandra 21X works with the same config
* When using e.g. SCAN(), a message is thrown: "******************* Type=number"
    * See https://github.com/kairosdb/kairosdb-client/issues/43


## Other Related Links

* http://de.slideshare.net/codyaray/scalable-distributed-stats-infrastructure
* https://prezi.com/ajkjic0jdws3/kairosdb-cassandra-schema/

[back](../../)
