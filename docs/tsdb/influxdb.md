# InfluxDB

## Links

* https://www.influxdata.com/products/open-source/
* https://github.com/influxdb/influxdb-java

## Information

* The open source InfluxDB has limited cluster capabilities

## Implementation Notes

* A cluster always has 3 RAFT Server
    * status can be seen with `/opt/influxdb/influx -execute "SHOW SERVERS"'`
* 0.9.4.2 has problems with MEAN() when running on clusters
    * see https://github.com/influxdb/influxdb/issues/4170
    * newer versions don't have this problem
* GROUP BY with more than 100000 buckets can't be used
    * see https://github.com/influxdb/influxdb/issues/2702
    * Fix: Using seconds instead of millisceonds, checking if the range does not exceed 100000 seconds

[back](../)
