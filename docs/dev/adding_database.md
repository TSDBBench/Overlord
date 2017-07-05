# Adding a New Database
* for this example consider your new tsdb would be opentsdb:
  1. Add Vagrantfiles:
    1. Create at least one folder in TSDBBench/vagrant_files
      * E.g. opentsdb_cl1_rf1 (cl = cluster size, rf = replication factor)
    2. Create at least one Vagrantfile in this new folder
      * Named same as the folder but with _ + number + .vagrant as suffix
      * Each file is one VM that is created and provisioned
      * E.g. TSDBBench/vagrant_files/opentsdb_cl1_rf1/opentsdb_cl1_rf1_0.vagrant
    3. In this Vagrantfile put deployment tasks like installing and configuring
      * But nothing where you need to know IPs from other nodes of the cluster (that comes in a later step)
        * Can't be done with Vagrant
      * Consider files in basic folder that can be reused
        * Eee TSDBBench/vagrant_files/basic/opentsdb.rb for example
  2. Add the python part
    1. Add a python file to TSDBBench/vagrant_files/generator/files/databases/
      * Named like the folder + .py (.e.g. opentsdb_cl1_rf1.py)
    2. In this file add:
      1. Deployment tasks that requires IPs from all nodes of the cluster
      2. Checks that the database is running
      3. Some basic db configs (everything that starts with db_)
    3. Look at other database python files, there are comments that explain every field in every file
      * E.g., TSDBBench/vagrant_files/generator/files/databases/opentsdb_cl1_rf1.py
  3. Add a Client (if not existing) to YCSB-TS
    * See https://github.com/TSDBBench/YCSB-TS

[back](../)
