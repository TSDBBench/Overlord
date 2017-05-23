# Overlord
[![Build Status](https://api.travis-ci.org/TSDBBench/TSDBBench.svg?branch=master)](https://travis-ci.org/TSDBBench/TSDBBench)

The Python and Vagrant part of TSDBBench that automatically setups and benchmarks tims series databases (TSDBs).

The benchmarking is done with VMs that are automatically setup by Vagrant and are running on one of the five supported elastic infrastructures (EIs).

Different cluster sizes and configurations as well as different workloads can be used to benchmark one or more TSDBs.

The benchmark is done with [YCSB-TS](https://github.com/TSDBBench/YCSB-TS).

## Supported databases
* Timeseries databases with a Requirement on NoSQL DBMS:
  * [Axibase](docs/tsdb/axibase.md)
  * [Blueflood](docs/tsdb/blueflood.md)
  * [Databus](docs/tsdb/databus.md)
  * [KairosDB](docs/tsdb/kairosdb.md)
  * [NewTS](docs/tsdb/newts.md)
  * [OpenTSDB](docs/tsdb/opentsdb.md)
  * [Rhombus](docs/tsdb/rhombus.md)
  * [Graphite](docs/tsdb/graphite.md)
* Timeseries databases with no Requirement on any DBMS:
  * [Akumuli](docs/tsdb/akumuli.md)
  * [Druid](docs/tsdb/druid.md)
  * [InfluxDB](docs/tsdb/influxdb.md)
  * [Gnocchi](docs/tsdb/gnocchi.md)
  * [Seriesly](docs/tsdb/seriesly.md)
  * [Prometheus](docs/tsdb/prometheus.md)
* Column-oriented DBMS
  * [MonetDB](docs/tsdb/monetdb.md)
  * [Kdb+](docs/tsdb/kdpplus.md)
* Relational databases:
  * [MySQL](docs/tsdb/mysql.md)
  * [PostgreSQL](docs/tsdb/postgresql.md)
* Other:
  * [Elasticsearch](docs/tsdb/elasticsearch.md)
  * [h5serv](docs/tsdb/h5serv.md)

## Unsupported databases (WIP)
*  [DalmatinerDB](docs/tsdb/dalmatinerdb.md)
*  [ScyllaDB](docs/tsdb/scylladb.md)
*  [RiakTS](docs/tsdb/riakts.md)
*  [Redis](docs/tsdb/redis.md)

## Supported Elastic Infrastrctures
* [VMware vSphere](docs/ei/vsphere.md)
* [OpenStack](docs/ei/openstack.md)
* [VirtualBox](docs/ei/virtualbox.md)
* [DigitalOcean](docs/ei/digitalocean.md)
* [Amazon Web Services](docs/ei/aws.md)

## Initial Setup of the Elastic Infrastrcture
* This must done only once and only for one elastic infrastructure
* All images are available at http://tsdbbench.allweathercomputing.com/bin/, can use them directly from there.
* See the articles for the five supported elastic infrastructures for specific instructions
    * [VMware vSphere](docs/ei/vsphere.md)
    * [OpenStack](docs/ei/openstack.md)
    * [VirtualBox](docs/ei/virtualbox.md)
    * [DigitalOcean](docs/ei/digitalocean.md)
    * [Amazon Web Services](docs/ei/aws.md)

## Initial Setup of local pc or Control-VM
* To control TSDBBench, a local pc or a Control-VM (a VM with everything preinstalled) can be used (only vSphere and OpenStack)
1. Local PC:
    1. Install packages:
        ```bash
        sudo apt-get install python-dateutil python-jinja2 python-numpy python-pandas python-flask python-redis python-requests python-six python-tornado python-werkzeug python-markupsafe python-greenlet python-zmq python-yaml python-pip wkhtmltopdf python-magic fabric vagrant zlib1g-dev zlib1g libxml2 libxml2-dev libxslt1.1 libxslt1-dev python-webcolors python-pyvmomi
        ```
    2. Install pip packages:
        ```bash
        sudo pip install bokeh python-vagrant pdfkit
        ```
    3. Install vagrant plugins:
        ```bashvagrant plugin install vagrant-vsphere
        vagrant plugin install vagrant-openstack-provider
        ```
    4. Reconfigure locales and make sure that en_US.UTF-8 is generated
        ```bash
        sudo dpkg-reconfigure locales
        ```
    5. Checking out & Prepairing Git Repo
        ```bash
        cd /path/to/some/folder/
        git clone https://github.com/baderas/TSDBBench
        cd TSDBBench
        vagrant box add --name dummy dummy.box
        copy hooks/pre-commit .git/hooks/
        cd ..
        ```
    6. Edit config for the chosen elastic infrastructure (change everything that says '' for your chosen elastic infrastructure)
        ```bash
        cd TSDBBench
        nano vagrant_files/vagrantconf.rb
        nano vagrant_files/vagrantconf_db.rb
        nano vagrant_files/vagrantconf_gen.rb
        ```
2. Control-VM
    1. Create Control-VM according to [VMware vSphere](docs/ei/vsphere.md) or [OpenStack](docs/ei/openstack.md)
    2. Login to your Control-VM
    3. Edit config for the chosen elastic infrastructure (change everything that says '' for your chosen elastic infrastructure)
        ```bash
        cd TSDBBench
        nano vagrant_files/vagrantconf.rb
        nano vagrant_files/vagrantconf_db.rb
        nano vagrant_files/vagrantconf_gen.rb
        ```

## Running a testworkload
 - without creation of html file:
    ```bash
    cd TSDBBench
    ./TSDBBench.py -t /path/to/some/tmpfolder -f vagrant_files -d mysql_cl1_rf1 --provider 'vsphere' -w "testworkloada" -l```
 - with creation of html file:
    ```bash
    cd TSDBBench
    ./TSDBBench.py -t /path/to/some/tmpfolder -f vagrant_files -d mysql_cl1_rf1 --provider 'vsphere' -w "testworkloada" -l -m```
 - with creation of html files and multiple databases:
    ```bash
    cd TSDBBench
    ./TSDBBench.py -t /path/to/some/tmpfolder -f vagrant_files -d mysql_cl1_rf1 postgresql_cl1_rf1 --provider 'vsphere' -w "testworkloada" -l -m --provider "vsphere"```
    
## Creating html files (when not using -m)
 - Creating a html file from a ycsb_*.log file:
    ```bash
    cd TSDBBench
    ./ProcessYcsbLog.py -f some_ycsb_logfile.log
    ```
 - Creating a html file from a ycsb_*.ydc file:
    ```bash
    cd TSDBBench
    ./ProcessYcsbLog.py -f some_ycsb_logfile.ydc
    ```
 - Creating a combined html file a set of from a ycsb_*.ydc/.log files:
    ```bash
    cd TSDBBench
    ./ProcessYcsbLog.py -f some_ycsb_logfile1.ydc ome_ycsb_logfile2.log ome_ycsb_logfile3.ydc ...
    ```
    
## Additional Information
* Everything was tested and used on Debian Jessie x64, but should work on Ubuntu.
    * Ubuntu has different package names for a lot of the packages, you need to find and change them
* Logfiles/Benchmark Results are stored compressed as .ydc Files 

## Development Information
* Development specific details on databases and elastic infrastructures can be found on their specific files (see links at the beginning)
* [Adding a New Database](docs/dev/adding_database.md)

## Related Work
* [Comparison of TSDBs (Andreas Bader)](http://www2.informatik.uni-stuttgart.de/cgi-bin/NCSTRL/NCSTRL_view.pl?id=DIP-3729&mod=0&engl=0&inst=FAK)
* [Survey and Comparison of Open Source TSDBs (Andreas Bader, Oliver Kopp, Michael Falkenthal)](http://www2.informatik.uni-stuttgart.de/cgi-bin/NCSTRL/NCSTRL_view.pl?id=INPROC-2017-06&mod=0&engl=0&inst=IPVS)
* [Ultimate Comparison of TSDBs](https://tsdbbench.github.io/Ultimate-TSDB-Comparison/)
* [TSDBBench Box at atlas](https://atlas.hashicorp.com/TSDBBench/boxes/tsdbbench_dummy.box)
* [YCSB-TS](https://github.com/TSDBBench/YCSB-TS)