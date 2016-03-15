#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import time

__author__ = 'Andreas Bader'
__version__ = "0.01"

import argparse
import logging
import Util
import os
import shutil
from fabric.api import *
import re

neededTools = ["which", "VBoxManage", "vagrant"]

creation_commands = [
    "VBoxManage createvm --name \"{name}\" --register",
    "VBoxManage modifyvm \"{name}\" --ostype Debian_64",
    "VBoxManage modifyvm \"{name}\" --memory 1024",
    "VBoxManage modifyvm \"{name}\" --vram 8",
    "VBoxManage modifyvm \"{name}\" --acpi on",
    "VBoxManage modifyvm \"{name}\" --ioapic on",
    "VBoxManage modifyvm \"{name}\" --boot1 dvd",
    "VBoxManage modifyvm \"{name}\" --pae on",
    "VBoxManage modifyvm \"{name}\" --longmode on",
    "VBoxManage modifyvm \"{name}\" --synthcpu off",
    "VBoxManage modifyvm \"{name}\" --hwvirtex on",
    "VBoxManage modifyvm \"{name}\" --nestedpaging on",
    "VBoxManage modifyvm \"{name}\" --largepages off",
    "VBoxManage modifyvm \"{name}\" --vtxvpid on",
    "VBoxManage modifyvm \"{name}\" --vtxux on",
    "VBoxManage modifyvm \"{name}\" --accelerate3d off",
    "VBoxManage modifyvm \"{name}\" --accelerate2dvideo off",
    "VBoxManage modifyvm \"{name}\" --chipset piix3",
    "VBoxManage modifyvm \"{name}\" --biossystemtimeoffset 0",
    "VBoxManage modifyvm \"{name}\" --firmware bios",
    "VBoxManage modifyvm \"{name}\" --monitorcount 1",
    "VBoxManage modifyvm \"{name}\" --cpus 2",
    "VBoxManage modifyvm \"{name}\" --rtcuseutc on",
    "VBoxManage modifyvm \"{name}\" --nic1 nat",
    "VBoxManage createhd --filename \"{path}/{name}.vdi\" --size \"{size}\" --format VDI --variant Standard",
    "VBoxManage storagectl \"{name}\" --name \"IDE Controller\" --add ide",
    "VBoxManage storagectl \"{name}\" --name \"SATA Controller\" --add sata",
    "VBoxManage storageattach \"{name}\" --storagectl \"SATA Controller\" --port 0 --device 0 --type hdd --medium \"{path}/{name}.vdi\"",
    "VBoxManage storageattach \"{name}\" --storagectl \"IDE Controller\" --port 0 --device 0 --type dvddrive --medium \"{iso}\""
]

timeout = 3600 # 1 hour should be enough

def delete_vm(name, logger):
    with settings(warn_only=True), hide('output','running','warnings'):
        ret = local("VBoxManage list vms", capture=True)
        if base_box_name in ret.stdout:
            uuid = re.search("^\"%s\"\s+\{[a-z0-9\-]+\}" % name,ret,re.MULTILINE)
            if uuid is None:
                logger.error("uuid of VM %s can't be found." %(name))
                return False
            uuid = re.search("\{[a-z0-9\-]+\}", uuid.group())
            if uuid is None:
                logger.error("uuid of VM %s can't be extracted from '%s'." %(name, uuid.group()))
                return False
            uuid = uuid.group().replace("{","").replace("}","")
            # deleting all drives without iso files
            # not necessary, --delete for unrgeistervm does it already
            # drives = local("VBoxManage showvminfo %s" % uuid, capture=True)
            # for res in re.findall("^IDE-Controller.+$|^SATA-Controller.+$", drives, re.MULTILINE):
            #     if ".iso" in res.lower():
            #         continue
            #     hdd_uuid = re.search("\(UUID:\s+[a-z0-9\-]+\)$",res)
            #     if hdd_uuid == None:
            #         logger.warning("Can't find UUID for hdd in '%s'. Please delete it by hand." %(hdd_uuid))
            #         continue
            #     hdd_uuid = hdd_uuid.group().replace("(UUID: ","").replace(")","")
            if status_vm(uuid, logger):
                logger.info("VM %s is running, stopping it..." %(name))
                stop_vm(uuid, logger)
            deleted = local("VBoxManage unregistervm %s --delete" % uuid)
            if deleted.return_code != 0:
                logger.error("Error while deleting VM %s with UUID %s. Please delete by hand!" %(name, uuid))
        else:
            logger.error("VM %s can't be found." %(name))
            return False
        return True

def create_vm(name, size, path, iso, logger):
    with settings(warn_only=True), hide('output','running','warnings'):
        for command in creation_commands:
            ret = local(command.format(name=name, size=size, path=path, iso=iso), capture=True)
            logger.info("Executing '%s'." % (command.format(name=name, size=size, path=path, iso=iso)))
            if ret.return_code != 0:
                logger.error("Command '%s' failed and returned with error code %s and stdout '%s' and stderr '%s'." %
                             (command.format(name=name, size=size, path=path, iso=iso), ret.return_code, ret.stdout, ret.stderr))
                return False
            logger.info("Command '%s' returned 0." % (command.format(name=name, size=size, path=path, iso=iso)))
    return True

def start_vm(name, graphic, logger):
    with settings(warn_only=True), hide('output','running','warnings'):
        headless_arg=""
        if not graphic:
            headless_arg = " --type headless"
        ret = local("VBoxManage startvm \"%s\"%s" %(name, headless_arg), capture=True)
        logger.info("Executing 'VBoxHeadless --startvm \"%s\"%s'." % (name, headless_arg))
        if ret.return_code != 0:
            logger.error("Command 'VBoxHeadless --startvm \"%s\"%s' failed and returned with error "
                         "code %s and stdout '%s' and stderr '%s'." %
                         (name, headless_arg, ret.return_code, ret.stdout, ret.stderr))
            return False
        logger.info("Command 'VBoxHeadless --startvm \"%s\"%s' returned 0." % (name, headless_arg))
    return True

def stop_vm(name, logger):
    with settings(warn_only=True), hide('output','running','warnings'):
        if status_vm(name, logger):
            logger.info("Trying soft poweroff...")
            ret = local("vboxmanage controlvm \"%s\" poweroff soft" % (name))
            logger.info("Command 'vboxmanage controlvm \"%s\" poweroff soft' returned %s." % (name, ret.return_code))
            if ret.return_code != 0:
                logger.info("Soft poweroff failed, trying (hard) poweroff...")
                ret = local("vboxmanage controlvm \"%s\" poweroff" % (name))
                logger.info("Command 'vboxmanage controlvm \"%s\" poweroff' returned %s." % (name, ret.return_code))
                if ret.return_code != 0:
                    return False
    return True


def status_vm(name, logger):
    with settings(warn_only=True), hide('output','running','warnings'):
        ret = local("VBoxManage showvminfo \"%s\"" % name, capture=True)
        if ret.return_code == 0:
            state = re.search("State:\s+running", ret.stdout)
            if state == None:
                return False
            else:
                return True
        else:
            logger.error("Error while checking of VM %s, can't determine state." %(name))
            return False

def exist_vm(name, logger):
    with settings(warn_only=True), hide('output','running','warnings'):
        ret = local("VBoxManage list vms", capture=True)
        if ret.return_code == 0:
            if name in ret.stdout:
                return True
            else:
                return False
        else:
            logger.error("Error while checking of VM %s, can't determine existence." %(name))
            return True

def package_vm(name, output_file, logger):
    with settings(warn_only=True), hide('output','running','warnings'):
        logger.info("Packaging vm with 'vagrant package --base \"%s\"'." %(name))
        ret = local("vagrant package --base \"%s\" --output \"%s\"" %(name, output_file), capture=True)
        if ret.return_code == 0:
            logger.info("Packaging of VM %s returned 0." %(name))
            return True
        else:
            logger.error("Packaging of VM %s returned %s with stdout '%s' and stderr '%s'."
                         % (name, ret.return_code, ret.stdout, ret.stderr))
            return False

# Configure ArgumentParser
parser = argparse.ArgumentParser(prog="MakeDebianVB.py",version=__version__,description="Creates an Vagrant Box with/for VirtualBox for use with TSDBBench.", formatter_class=argparse.RawDescriptionHelpFormatter, epilog="")
parser.add_argument("-i", "--isofile", metavar="ISOFILE", required=True, help="path to Debian Autoinstall Iso")
parser.add_argument("-f", "--outputfolder", metavar="OUTPUTFOLDER", required=True, help="path to outputfolder (will be created if not existent) (> 5 gb)")
parser.add_argument("-g", "--graphic", action="store_true", help="show graphic output, normally -nographic is used. Useful if you don't use a preseeded iso.")
parser.add_argument("-o", "--overwrite", action="store_true", help="overwrite if VM is existing")
parser.add_argument("-l", "--log", action='store_true', help="Be more verbose, log vagrant output.")
parser.add_argument("-s", "--size", metavar="SIZE", type=int, default=50, help="Size in Gigabyte (50 is default), e.g. 50 for 50G (will be compressed, Qcow2 file size will be much lesser!)")
args = parser.parse_args()

# Configure Logging
logLevel = logging.WARN
if args.log:
    logLevel = logging.DEBUG
logging.basicConfig(level=logLevel)
logger = logging.getLogger(__name__)

# Check ob alle Tools da sind
for tool in neededTools:
    with settings(warn_only=True), hide('output','running','warnings'):
        ret=local("which '%s'" %(tool))
        if ret.return_code != 0:
            logger.error("'%s' not found, please install." %(tool))
            exit(-1)

if not (Util.check_file_exists(args.isofile) and Util.check_file_readable(args.isofile)):
    logger.error("Isofile %s does not exist or is not readable." %(args.isofile))
    exit(-1)

if not Util.check_folder(args.outputfolder,logger,False,True):
    if not Util.create_folder(args.outputfolder) or not Util.check_folder(args.outputfolder,logger):
        logger.error("Can't create %s." %(args.outputfolder))
        exit(-1)

isoFileName=os.path.basename(args.isofile)
base_box_name="default"
if len(os.path.splitext(args.isofile)) > 0:
    base_box_name=os.path.splitext(isoFileName)[0]
outputFileName="%s.box" %(base_box_name)

## Checking if Virtualbox exists
if exist_vm(base_box_name, logger):
    if not args.overwrite:
        logger.error("Error: VM %s already exists." % base_box_name)
    else:
        if not delete_vm(base_box_name, logger):
                                logger.error("Error: VM %s already exists and can't be deleted." % base_box_name)
                                exit(-1)

if create_vm(base_box_name, int(round(args.size*953.674)), args.outputfolder, args.isofile, logger):
    if start_vm(base_box_name, args.graphic, logger):
        logger.info("Waiting for Installation to finish...")
        start_time = time.time()
        while status_vm(base_box_name, logger) and time.time()-start_time <= timeout:
            time.sleep(1)
        if time.time()-start_time > timeout:
            logger.error("VM took more than %s seconds. Timeout activated." % timeout)
        else:
            logger.info("VM is now powered off.")
            logger.info("Packaging VM with Vagrant.")
            if package_vm(base_box_name, os.path.join(args.outputfolder, outputFileName), logger):
                print "Packaging was successful. You can now import your new base box with" \
                      " 'vagrant box add tsdbbench-debian %s'" %(os.path.join(args.outputfolder, outputFileName))
        logger.info("Deleting VM.")
        if not delete_vm(base_box_name, logger):
            logger.warning("Error: VM %s can't be deleted, please delete by hand." % base_box_name)
    else:
        logger.error("Error: VM %s can't be started." % base_box_name)
        exit(-1)
else:
    logger.error("Error: VM %s can't be created." % base_box_name)
    exit(-1)

exit(0)