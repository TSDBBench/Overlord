# OpenTSDB

## Links

* http://opentsdb.net

## Information

* Requires three components:
    * Zookeeper
    * HBase
    * Java
* Gnuplot is required for graphs
* Metrics must be created explicitly
* Filtering for tags required version >= 2.2
* Every query requires an aggregating function
    * pure SCAN()/READ() is not possible
* COUNT() requires version >= 2.2
* Milliseconds are accepted but not guaranteed
    * see http://opentsdb.net/docs/build/html/user_guide/writing.html#timestamps
* Not sure how tu use more than one OpenTSDB node
    * see http://wiki.cvrgrid.org/index.php/OpenTSDB_Cluster_Setup#Installing_OpenTSDB
    * Vanish or DNS Round Robin would be a possibility but only for READ()

## Implementation Notes

* No direct java API, requires REST/JSON via HTTP
* Zookeeper is started by start-hbase.sh, do not start by manually
* JAVA_HOME must be set correctly
* Gnuplot is required for graphs
* MIN() is used for SCAN()/READ()
* HBase stores by deault in /tmp/hbase-root which is a tmpfs (faster than HDD/SSD)
    * changed to use HDD
* /etc/opentsdb/opentsdb.conf says that tsd.storage.hbase.zk_quorum must be a space seperated list, but it must be a comma seperated list
* LZO should be used for better performance
    * see http://opentsdb.net/setup-hbase.html
    * installation: http://opentsdb.net/setup-hbase.html
        * FIX1: https://github.com/twitter/hadoop-lzo/issues/35
        * FIX2: ignore CLASSPATH -> `JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64 CFLAGS=-m64 CXXFLAGS=-m64 ant compile-native tar`
* OpenTSDB's webinterface is accessible on http://<IP>:4242/
* Haddop is accessible on http://<IP>:50070
* HBase ist accessible on http://<IP>:16010 (16020/16030 on regionservers!)
## Other Related Links

* http://arcticfoxontheweb.blogspot.de/2015/03/querying-opentsdb-with-java-yes-it-can.html
* http://opentsdb.net/docs/build/html/api_http/query/index.html
* http://opentsdb.net/docs/build/html/api_http/put.html
* https://hbase.apache.org/book.html#quickstart
* http://www.dreamsyssoft.com/blog/blog.php?/archives/5-How-to-use-HBase-Hadoop-Clustered.html
* https://alijehangiri.wordpress.com/2013/05/17/cloud/
* http://hbase.apache.org/book.html#standalone_dist
* http://hbase.apache.org/book.html#quickstart_fully_distributed
* http://chaalpritam.blogspot.de/2015/01/hadoop-260-multi-node-cluster-setup-on.html
* http://www.michael-noll.com/tutorials/running-hadoop-on-ubuntu-linux-multi-node-cluster/
* http://www.bigdata-insider.de/infrastruktur/articles/469385/
* http://wiki.cvrgrid.org/index.php/OpenTSDB_Cluster_Setup#Installing_OpenTSDB
* Performance/Benchmarking:
    * http://www.moredevs.com/opentsdb-and-hbase-rough-performance-test/
    * https://peritusconsulting.github.io/articles/2014-06-02-next-generation-monitoring-using-opentsdb.html
    * https://www.mapr.com/blog/loading-time-series-database-100-million-points-second

[back](../)
