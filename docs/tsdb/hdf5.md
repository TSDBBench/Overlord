# HDF5 (h5serv)

## Links

* https://www.hdfgroup.org/HDF5/
* https://docs.dalmatiner.io/

## Information

* HDF5 is a file system
    * no distribution
    * strong consistency
    * often used in research
* No TSDB, just  a filesystem
* Disadvantages when using as TSDB:
    * No append() function
    * Only put() that eneds a specific index, requirement for a counter that counts along
    * COUNT, AVG, SUM not available
    * No indexing functions
    * time series as compound data type possible
    * h5table also possible for time series, but not yet available in h5serv
        * basically the same as compound, but easier to use
* h5serv is a server with REST interface and hdf5 filesystem
    * uses hdf5-json

## Implementation Notes

* Problems with string with variable length
    * see https://github.com/HDFGroup/h5serv/issues/77
    * Fix: using constant length strings
* H5T_STD_U64BE does not work with queries
    * see https://github.com/HDFGroup/h5serv/issues/80
    * *_I64BE variants work
    * *_*_LE is faster than *_*_BE


## How to install/build

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
  
## Other related links

* https://www.hdfgroup.org/HDF5/
* https://www.hdfgroup.org/projects/hdfserver/
* https://www.hdfgroup.org/HDF5/doc/
* http://h5serv.readthedocs.org/en/latest/
* http://h5serv.readthedocs.org/en/latest/Diagram.html
* https://github.com/HDFGroup/h5serv
* https://travis-ci.org/HDFGroup/h5serv/jobs/106399076
* https://travis-ci.org/HDFGroup/hdf5-json/jobs/99532396
* https://travis-ci.org/HDFGroup/h5serv/jobs/104515484
* http://h5serv.readthedocs.org/en/latest/FAQ/index.html
* https://github.com/HDFGroup/hdf5-json
* http://permalink.gmane.org/gmane.comp.programming.hdf/5946
* https://www.hdfgroup.org/pubs/papers/Big_HDF_FAQs.pdf
* http://stackoverflow.com/questions/15379399/writing-appending-arrays-of-float-to-the-only-dataset-in-hdf5-file-in-c
* http://www.pytables.org/index.html
* https://github.com/pydata/numexpr
* https://code.google.com/archive/p/numexpr/wikis/UsersGuide.wiki#Supported_operators
* http://www.pytables.org/usersguide/condition_syntax.html#condition-syntax
* http://www.pytables.org/usersguide/libref/structured_storage.html#tables.Table.where
* https://code.google.com/archive/p/numexpr/

[Back to README.md](../../README.md)
