# TSDBBench
[![Build Status](https://api.travis-ci.org/TSDBBench/TSDBBench.svg?branch=master)](https://travis-ci.org/TSDBBench/TSDBBench)

The Python and Vagrant part of TSDBBench

The VMs are running on vSphere or Openstack, but you can choose to run TSDBBench.py on your local pc or on a Control VM.


# Supported databases

* Timeseries databases with a Requirement on NoSQL DBMS:
  * [Axibase Time Series Database](docs/tsdb/axibase.md)
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

# Unsupported databases (WIP)

*  [DalmatinerDB](docs/tsdb/dalmatinerdb.md)
*  [ScyllaDB](docs/tsdb/scylladb.md)
*  [RiakTS](docs/tsdb/riakts.md)

# Supported Elastic Infrastrctures

* [VMware vSphere](docs/ei/vsphere.md)
* [OpenStack](docs/ei/openstack.md)
* [VirtualBox](docs/virtualbox.md)
* [DigitalOcean](docs/digitalocean.md)
* [Amazon Web Services](docs/aws.md)

## Setup Elastic Infrastructure
For your elastic infrastructure you need image(s) as bases for vagrant to derive generator and tsdb vms from. You can choose wheter you want to use vSohere or Openstack, you don't need both.

1. Create/Copy images:
 - All images are available at http://nemarcontrolvm.iaas.uni-stuttgart.de/isos/, you can use them directly from there (no need to download to your local pc!).
   - for vSphere:
     - Copy http://nemarcontrolvm.iaas.uni-stuttgart.de/isos/debian-8.1.0-amd64-netinst-vsphere-autoinstall.iso to your vSphere datastore
   - for Openstack:
     - Copy http://nemarcontrolvm.iaas.uni-stuttgart.de/isos/debian-8.1.0-amd64-netinst-openstack-autoinstall.qcow2 to your images in Openstack
 - If you still want to create own images (changed preseed file e.g.) (run on your local pc):
   - for vSphere:

            cd /path/to/another/folder/
            wget http://cdimage.debian.org/debian-cd/8.2.0/amd64/iso-cd/debian-8.2.0-amd64-netinst.iso
            cd /path/to/some/folder/
            git clone https://github.com/baderas/TSDBBench
            cd TSDBBench
            ./MakeDebianIso.py -t /path/to/tmpfolder -i /path/to/another/folder/debian-8.2.0-amd64-netinst.iso -f /path/to/outputfolder/ -p preseed-vsphere.cfg
   - for Openstack

            sudo apt-get install qemu-kvm libvirt-bin
            sudo gpasswd -a $USER kvm
            sudo gpasswd -a $USER libvirt
            sudo reboot (or logout and login)
            cd /path/to/another/folder/
            wget http://cdimage.debian.org/debian-cd/8.2.0/amd64/iso-cd/debian-8.2.0-amd64-netinst.iso
            cd /path/to/some/folder/
            git clone https://github.com/baderas/TSDBBench
            cd TSDBBench
            ./MakeDebianIso.py -t /path/to/tmpfolder -i /path/to/another/folder/debian-8.2.0-amd64-netinst.iso -f /path/to/outputfolder/ -p preseed-openstack.cfg
            ./MakeDebianQcow2.py -i /path/to/outputfolder/debian-8.2.0-amd64-netinst-openstack-autoinstall.iso -f /path/to/outputfolder/
            upload the resulting file to your Openstack Storage
2. (Only for vSphere) Create templates (run on your local pc):

        cd /path/to/some/folder/
        git clone https://github.com/baderas/TSDBBench
        cd TSDBBench
        nano vagrant_files/vagrantconf.rb (add everything that says '')
        nano vagrant_files/vagrantconf_db.rb (add everything that says '')
        nano vagrant_files/vagrantconf_gen.rb (add everything that says '')
        ./pySetupVsphere.py -f /path/to/some/folder/TSDBBench/vagrant_files/

## Setup
Everything was tested and used on Debian Jessie x64, but should work on Ubuntu. But Ubuntu has different package names for a lot of the packages, you need to find and change them!
### Choice 1: local pc
1. Install packages:

        sudo apt-get install python-dateutil python-jinja2 python-numpy python-pandas python-flask python-redis python-requests python-six python-tornado python-werkzeug python-markupsafe python-greenlet python-zmq python-yaml python-pip wkhtmltopdf python-magic fabric vagrant zlib1g-dev zlib1g libxml2 libxml2-dev libxslt1.1 libxslt1-dev python-webcolors python-pyvmomi
2. Install pip packages:

        sudo pip install bokeh python-vagrant pdfkit
3. Install vagrant plugins:

        vagrant plugin install vagrant-vsphere
        vagrant plugin install vagrant-openstack-provider
4. Reconfigure locales and make sure that en_US.UTF-8 is generated

        sudo dpkg-reconfigure locales
5. Checking out & Prepairing Git Repo

        cd /path/to/some/folder/
        git clone https://github.com/baderas/TSDBBench
        cd TSDBBench
        vagrant box add --name dummy dummy.box
        copy hooks/pre-commit .git/hooks/
        cd ..
6. Edit Config (change everything that says '')

        cd /path/to/some/folder/TSDBBench
        nano vagrant_files/vagrantconf.rb
        nano vagrant_files/vagrantconf_db.rb
        nano vagrant_files/vagrantconf_gen.rb

### Choice 2: Control VM
  - Coming soon...

## Running a testworkload
 - without creating html file:

        cd /path/to/some/folder/TSDBBench
        ./TSDBBench.py -t /path/to/tmpfolder -f /path/to/some/folder/TSDBBench/vagrant_files -d mysql1 -l --provider 'vsphere' -w "testworkloada"
 - with creating html file:

        cd /path/to/some/folder/TSDBBench
        ./TSDBBench.py -t /path/to/tmpfolder -f /path/to/some/folder/TSDBBench/vagrant_files -d mysql1 -l --provider 'vsphere' -w "testworkloada" -m

## Creating html files (when not using -m)
 - Creating a html file from a ycsb_*.log file:

        cd /path/to/some/folder/TSDBBench
        ./ProcessYcsbLog.py -f some_ycsb_logfile.log

 - Creating a html file from a ycsb_*.ydc file:

        cd /path/to/some/folder/TSDBBench
        ./ProcessYcsbLog.py -f some_ycsb_logfile.ydc

 - Creating a combined html file a set of from a ycsb_*.ydc/.log files:

        cd /path/to/some/folder/TSDBBench
        ./ProcessYcsbLog.py -f some_ycsb_logfile1.ydc ome_ycsb_logfile2.log ome_ycsb_logfile3.ydc ...

## Steps to add a new TSDB:
for this example consider your new tsdb would be opentsdb:
  1. Add Vagrantfiles:
   1. Create at least one folder in /path/to/some/folder/TSDBBench/vagrant_files
      - e.g. opentsdb1
   2. Create at least one Vagrantfile in this new folder
      - named same as the folder but with _ + number + .vagrant as suffix
      - e.g. /path/to/some/folder/TSDBBench/vagrant_files/opentsdb1/opentsdb1_0
   3. In this Vagrantfile put deployment tasks like installing and configuring
      - but nothing where you need to know IPs from other nodes of the cluster (that comes later)
   4. Use basic scripts as much as possible
      - see /path/to/some/folder/TSDBBench/vagrant_files/basic
  2. Add the python part
   1. Add a python file to /path/to/some/folder/TSDBBench/databases
     - named like the folder + .py (.e.g. opentsdb1.py)
   2. In this file you add:
     1. Deployment tasks that requires IPs from all nodes of the cluster
     2. Checks that the database is running
     3. Some basic db configs (everything that starts with db_)
   3. Look at other database python files, there are comments that explain every field in every file
  3. Testing
   - You need to copy the database files to /path/to/some/folder/TSDBBench/vagrant_files/generator/files/databases/
   - You can run either run "hooks/pre-commit" or "git commit -a" (runs the hook as well if setup correctly).

## Related Projects
 * [VPS Benchmarks](http://www.vpsbenchmarks.com/) - measurement of VPS performance
