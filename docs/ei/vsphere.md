# VMWare vSphere

## Links
* http://www.vmware.com/products/vsphere.html

## Information
* for vSphere autoinstalling iso files are used to create templates that can be reused
    * the whole process is scripted

## Initial Elastic Infrastructure Setup
1. Copy http://tsdbbench.allweathercomputing.com/bin/debian-8.8.0-amd64-netinst-vsphere-autoinstall.iso to your vSphere datastore
2. `cd /path/to/some/folder/`
3. `git clone https://github.com/baderas/TSDBBench`
4. `cd TSDBBench`
5. `nano vagrant_files/vagrantconf.rb` (add everything that says '' and is vSphere related)
6. `nano vagrant_files/vagrantconf_db.rb` (add everything that says '' and is vSphere related)
7. `nano vagrant_files/vagrantconf_gen.rb` (add everything that says '' and is vSphere related)
8. `nano SetupVsphere.py` (change baseDbVmConfig and baseGenVmConfig)
9. `./SetupVsphere.py -f /path/to/some/folder/TSDBBench/vagrant_files/`
10. (optional) If you want a Control-VM, do the following:
    11. Copy http://tsdbbench.allweathercomputing.com/bin/debian-8.8.0-amd64-netinst-vsphere-controlvm-autoinstall.iso to your vSphere datastore
    12. Create a new VM and use the image to install the Control-VM on it (automated)

## Creating Your Own Images (Generator/Database)
* If you want to create your own images, do the following:
    1. `cd /path/to/another/folder/`
    2. `wget http://cdimage.debian.org/debian-cd/8.8.0/amd64/iso-cd/debian-8.8.0-amd64-netinst.iso`
    3. `cd /path/to/some/folder/`
    4. `git clone https://github.com/baderas/TSDBBench`
    5. `cd TSDBBench`
    6. `./MakeDebianIso.py -t /path/to/tmpfolder -i /path/to/another/folder/debian-8.8.0-amd64-netinst.iso -f /path/to/outputfolder/ -p preseed-vsphere.cfg`
    7. `nano vagrant_files/vagrantconf.rb` (add everything that says '' and is vSphere related)
    8. `nano vagrant_files/vagrantconf_db.rb` (add everything that says '' and is vSphere related)
    9. `nano vagrant_files/vagrantconf_gen.rb` (add everything that says '' and is vSphere related)
    10. `nano SetupVsphere.py` (change baseDbVmConfig and baseGenVmConfig)
    11. `./SetupVsphere.py -f /path/to/some/folder/TSDBBench/vagrant_files/`

## Creating your own Control-VM Image
1. `cd /path/to/another/folder/`
2. `wget http://cdimage.debian.org/debian-cd/8.8.0/amd64/iso-cd/debian-8.8.0-amd64-netinst.iso`
3. `cd /path/to/some/folder/`
4. `git clone https://github.com/baderas/TSDBBench`
5. `cd TSDBBench`
6. `./MakeDebianIso.py -t /path/to/tmpfolder -i /path/to/another/folder/debian-8.8.0-amd64-netinst.iso -f /path/to/outputfolder/ -p preseed-vsphere-controlvm.cfg`
7. Import the resulting iso file to your vSphere datastore, create a new VM and use the iso image to install the Control-VM on it

[Back to README.md](../../README.md)
