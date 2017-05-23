# DalmatinerDB

## Links

* https://github.com/dalmatinerdb/dalmatinerdb
* https://docs.dalmatiner.io/

## Information

* Has no requirement on any DBMS
* Uses ZFS as filesystem
  * Can use other filesystems, but may be slower then
* DEB/RPM packages are not available, but can be build
* Not (yet) integrated into TSDBBench/YCSB-TS
  * Since the bug seems to be fixed ([issue](https://github.com/dalmatinerdb/dalmatinerdb/issues/4)), it may work know

## How to install/build:

* https://dalmatiner.io/docs/installation.html#from-sorce
* Datastore:
  * sudo apt-get install git rebar erlang
  * git clone https://github.com/dalmatinerdb/dalmatinerdb.git
  * cd dalmatinerdb
  * make deps all rel
  * cp -r rel/dalmatinerdb $TARGET_DIRECTORY
  * cd $TARGET_DIRECTORY
  * cp etc/dalmatinerdb.conf.example etc/dalmatinerdb.conf
  * vi etc/dalmatinerdb.conf # check the settings and adjust if needed
  * ./bin/ddb start

[Back to README.md](../../README.md)
