# Oracle VirtualBox

## Links
* https://www.virtualbox.org/

## Information
* Virtualbox was used as first locally running development plattform
* A specific BaseBox must exist in Vagrant (comparable to templates in vSphere or qcow2 images in OpenStack)
    * Steps how to create this BaseBox are missing

## Initial VirtualBox Setup
1. `cd /path/to/some/folder/`
2. `wget http://tsdbbench.allweathercomputing.com/bin/debian-8.8.0-amd64-netinst-vsphere-autoinstall.box`
3. Import the new Box with Vagrant: `vagrant box add tsdbbench-debian debian-8.8.0-amd64-netinst-virtualbox-autoinstall.box`

## Creating Your Own Images (Generator/Database)
* If you want to create your own images, do the following (example on Debian Jessie):
    1. Install VirtualBox, e.g. see https://wiki.debian.org/VirtualBox for Debian Jessie
    5. `cd /path/to/another/folder/`
    6. `wget http://cdimage.debian.org/debian-cd/8.8.0/amd64/iso-cd/debian-8.8.0-amd64-netinst.iso`
    7. `cd /path/to/some/folder/`
    8. `git clone https://github.com/TSDBBench/Overlord`
    9. `cd Overlord`
    10. `./MakeDebianIso.py -t /path/to/tmpfolder -i /path/to/another/folder/debian-8.8.0-amd64-netinst.iso -f /path/to/outputfolder/ -p preseed-virtualbox.cfg`
    11. `./MakeDebianVB.py -i debian-8.8.0-amd64-netinst-virtualbox-autoinstall.iso -f /path/to/outputfolder/`
    12. Import the new Box with Vagrant: `vagrant box add tsdbbench-debian /path/to/outputfolder/debian-8.8.0-amd64-netinst-virtualbox-autoinstall.box`


[back](../)
