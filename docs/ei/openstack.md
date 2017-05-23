# OpenStack

## Links
* https://www.openstack.org/

## Information
* for OpenStack qcow2 images are sued
    * the images are created from the autoninstalling iso files 
    * the iso files for OpenStack have only minor differences to those of vSphere, see the corresponding preseed files.
    
## Initial Elastic Infrastructure Setup
1. Copy http://tsdbbench.allweathercomputing.com/bin/debian-8.8.0-amd64-netinst-vsphere-autoinstall.qcow2 to your images in Openstack
2. (optional) If you want a Control-VM, do the following:
    3. Copy http://tsdbbench.allweathercomputing.com/bin/debian-8.8.0-amd64-netinst-vsphere-controlvm-autoinstall.qcow2 to your images in OpenStack
    4. Create a new VM using the Control-VM image

## Creating Your Own Images (Generator/Database)
* If you want to create your own images, do the following (example on Debian Jessie):
    1. `sudo apt-get install qemu-kvm libvirt-bin`
    2. `sudo gpasswd -a $USER kvm`
    3. `sudo gpasswd -a $USER libvirt`
    4. `sudo reboot` (or logout and login)
    5. `cd /path/to/another/folder/`
    6. `wget http://cdimage.debian.org/debian-cd/8.8.0/amd64/iso-cd/debian-8.8.0-amd64-netinst.iso`
    7. `cd /path/to/some/folder/`
    8. `git clone https://github.com/baderas/TSDBBench`
    9. `cd TSDBBench`
    10. `./MakeDebianIso.py -t /path/to/tmpfolder -i /path/to/another/folder/debian-8.8.0-amd64-netinst.iso -f /path/to/outputfolder/ -p preseed-openstack.cfg`
    11. `./MakeDebianQcow2.py -i /path/to/outputfolder/debian-8.8.0-amd64-netinst-openstack-autoinstall.iso -f /path/to/outputfolder/`
    12. Upload the resulting file to your Openstack Storage

## Creating your own Control-VM Image
1. `sudo apt-get install qemu-kvm libvirt-bin`
2. `sudo gpasswd -a $USER kvm`
3. `sudo gpasswd -a $USER libvirt`
4. `sudo reboot` (or logout and login)
5. `cd /path/to/another/folder/`
6. `wget http://cdimage.debian.org/debian-cd/8.8.0/amd64/iso-cd/debian-8.8.0-amd64-netinst.iso`
7. `cd /path/to/some/folder/`
8. `git clone https://github.com/baderas/TSDBBench`
9. `cd TSDBBench`
10. `./MakeDebianIso.py -t /path/to/tmpfolder -i /path/to/another/folder/debian-8.8.0-amd64-netinst.iso -f /path/to/outputfolder/ -p preseed-openstack-controlvm.cfg`
11. `./MakeDebianQcow2.py -i /path/to/outputfolder/debian-8.8.0-amd64-netinst-openstack-controlvm-autoinstall.iso -f /path/to/outputfolder/`
12. Upload the resulting file to your Openstack Storage

[Back to README.md](../../README.md)
