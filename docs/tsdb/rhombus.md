# Rhombus

## Links

* https://github.com/Pardot/Rhombus

## Information

* Rhombus is a library that uses Cassandra, no seperate running daemon
* Creates a Cassandra Keyspace at init()
* The cassandra layout must be given in a json file
    * Amount of TAGs is not dynamic!
* No AVG() or SUM() and therefore no granularity choosable
    
## Implementation Notes

* 3 TAGs are supported by default (same as SQL)
* "ShardingStrategyNone" is used as strategy since it is not expected that tag wide rows overflow
* Nothing must be installed on the server besides Cassandra
* COUNT() instead of AVG()/SUM()

[back](../../)
