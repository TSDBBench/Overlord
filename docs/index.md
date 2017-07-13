# Overlord

This is the Python and Vagrant part of TSDBBench

<!-- toc -->

- [Supported databases](#supported-databases)
  * [Timeseries databases with a requirement on NoSQL DBMS](#timeseries-databases-with-a-requirement-on-nosql-dbms)
  * [Timeseries databases with no requirement on any DBMS](#timeseries-databases-with-no-requirement-on-any-dbms)
  * [Column-oriented DBMS](#column-oriented-dbms)
  * [Relational databases](#relational-databases)
  * [Other](#other)
- [Unsupported databases (WIP)](#unsupported-databases-wip)
- [Supported Elastic Infrastructures](#supported-elastic-infrastructures)
- [Initial Setup of the Elastic Infrastructure](#initial-setup-of-the-elastic-infrastructure)
- [Initial Setup of local pc or Control-VM](#initial-setup-of-local-pc-or-control-vm)
- [Running a testworkload](#running-a-testworkload)
- [Creating html files (when not using -m)](#creating-html-files-when-not-using--m)
- [Additional Information](#additional-information)
- [Development Information](#development-information)

<!-- tocstop -->

## Supported databases

### Timeseries databases with a requirement on NoSQL DBMS

  * [Axibase](tsdb/axibase)
  * [Blueflood](tsdb/blueflood)
  * [Databus](tsdb/databus)
  * [KairosDB](tsdb/kairosdb)
  * [NewTS](tsdb/newts)
  * [OpenTSDB](tsdb/opentsdb)
  * [Rhombus](tsdb/rhombus)
  * [Graphite](tsdb/graphite)

### Timeseries databases with no requirement on any DBMS

  * [Akumuli](tsdb/akumuli)
  * [Druid](tsdb/druid)
  * [InfluxDB](tsdb/influxdb)
  * [Gnocchi](tsdb/gnocchi)
  * [Seriesly](tsdb/seriesly)
  * [Prometheus](tsdb/prometheus)

### Column-oriented DBMS
  * [MonetDB](tsdb/monetdb)
  * [Kdb+](tsdb/kdpplus)

### Relational databases

  * [MySQL](tsdb/mysql)
  * [PostgreSQL](tsdb/postgresql)

### Other

  * [Elasticsearch](tsdb/elasticsearch)
  * [h5serv](tsdb/h5serv)

## Unsupported databases (WIP)
*  [DalmatinerDB](tsdb/dalmatinerdb)
*  [ScyllaDB](tsdb/scylladb)
*  [RiakTS](tsdb/riakts)
*  [Redis](tsdb/redis)

## Supported Elastic Infrastructures
* [VMware vSphere](ei/vsphere)
* [OpenStack](ei/openstack)
* [VirtualBox](ei/virtualbox)
* [DigitalOcean](ei/digitalocean)
* [Amazon Web Services](ei/aws)

## Initial Setup of the Elastic Infrastructure
* This must done only once and only for one elastic infrastructure
* All images are available at http://tsdbbench.allweathercomputing.com/bin/, can use them directly from there.
* See the articles for the five supported elastic infrastructures for specific instructions
    * [VMware vSphere](ei/vsphere)
    * [OpenStack](ei/openstack)
    * [VirtualBox](ei/virtualbox)
    * [DigitalOcean](ei/digitalocean)
    * [Amazon Web Services](ei/aws)

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
    1. Create Control-VM according to [VMware vSphere](ei/vsphere) or [OpenStack](ei/openstack)
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
* [Adding a New Database](dev/adding_database)
