# NewTS

## Links

* http://opennms.github.io/newts/
* https://github.com/OpenNMS/newts

## Information

* Filtering can only done by time or by TAGs when using the API
* When filtering for TAGs, you have the choice between x,y,z exist or one of x,y,z
    * but you can't say: a=x and b=y and c=z
    * see https://github.com/OpenNMS/newts/blob/master/api/src/main/java/org/opennms/newts/api/search/QueryBuilder.java
    * see https://github.com/OpenNMS/newts/blob/master/cassandra/search/src/main/java/org/opennms/newts/cassandra/search/CassandraSearcher.java
* REST API does not support searching/filtering for time -> https://github.com/OpenNMS/newts/wiki/Search
* No COUNT(), SUM() -> https://github.com/OpenNMS/newts/wiki/ReportDefinitions
* Bucket size must be at least 2 ms when using AVG(), MAX(), MIN()
* Unlimited bucket size impossible
    * If bucket is too big, "java.lang.IllegalArgumentException: resolution must be a multiple of interval" is thrown

## Implementation Notes

* Instead of COUNT() MIN() is used
* Instead of SUM() MAX() is used
* 1 year bucket size is used for "unlimited"
* NewTS daemonizes itself in a ugly way. Only way to control it headlessly is with a systemd service file.
* Changing the replication factor must be done by hand in Cassandra keypsace
    * https://cassandra.apache.org/doc/cql3/CQL.html#createKeyspaceStmt
    * http://www.opennms.org/wiki/Featurebranch/Newts#Updating_the_replication_factor
* Filtering for Tags does also not work with CassandraSearcher
    * disabled

## Other Related Links

* https://github.com/OpenNMS/newts/wiki/JavaAPI
* https://github.com/OpenNMS/newts/wiki/UsingJava

[back](../../)
