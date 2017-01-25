#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Andreas Bader'
__version__ = "0.01"

from pyVim import connect
from pyVmomi import vmodl, vim
import Util
import os
import argparse
import logging
import atexit
import time
import datetime

# First: Default without template name
# Second: Only Generator template name
# Third: Only DB template name
vagrantCredFiles=["vagrantconf.rb", "vagrantconf_gen.rb", "vagrantconf_db.rb"]

requiredConfigValues={"vsphere.host" : None, # Name + Conversion Method, None = no conversion required only clean '' out
                      "vsphere.compute_resource_name" : None,
                      "vsphere.resource_pool_name" : None,
                      "vsphere.template_name_gen" : None,
                      "vsphere.template_name_db" : None,
                      "vm_base_path" : None,
                      "vsphere.data_store_name" : None,
                      "vsphere.user" : None,
                      "vsphere.password" : None}

baseDbVmConfig={ "name" : "BaseDB-VM",
                 "cpu" : 8,
                 "ram" : 16384,
                 "hdd" : 50, #in GB
                 "network" : "VM Network IAAS",
                 "iso" : "[dsNEMAR_NFS_nemarcontrolvm_v2] debian-8.6.0-amd64-netinst-autoinstall.iso"}
baseGenVmConfig={ "name" : "BaseGen-VM",
                  "cpu" : 4,
                  "ram" : 8192,
                  "hdd" : 50, #in GB
                  "network" : "VM Network IAAS",
                  "iso" : "[dsNEMAR_NFS_nemarcontrolvm_v2] debian-8.6.0-amd64-netinst-autoinstall.iso"}
controlVmConfig={ "name" : "Control-VM",
                  "cpu" : 8,
                  "ram" : 8192,
                  "hdd" : 50, #in GB
                  "network" : "VM Network IAAS",
                  "iso" : "[dsNEMAR_NFS_nemarcontrolvm_v2] debian-8.6.0-amd64-netinst-vsphere-controlvm-autoinstall.iso"}
TestVmConfig={ "name" : "TEST",
                  "cpu" : 1,
                  "ram" : 1024,
                  "hdd" : 10, #in GB
                  "network" : "VM Network IAAS",
                  "iso" : "[dsNEMAR_NFS_nemarcontrolvm_v2] debian-8.1.0-amd64-netinst-autoinstall.iso"}

vmDictList = [baseGenVmConfig, baseDbVmConfig, controlVmConfig]

#######################################################################
# Fix for not validated SSL Certs
# Better (when available): https://github.com/hartsock/pyvmomi/commit/3e12779a6d1fd9e9cfd7ae6f614652b740d25303
import requests
requests.packages.urllib3.disable_warnings()
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context
#######################################################################

def convert_config_item(parameter, item, logger):
    str = item
    if parameter in requiredConfigValues.keys():
            if requiredConfigValues[parameter] == None:
                return str
            try:
                str = requiredConfigValues[parameter](item)
            except Exception, e:
                logger.error("Could not convert %s:%s." %(parameter, item), exc_info=True)
    return str

def handle_vsphere_config_line(line,dict,logger):
    str = Util.clean_newline_space(line)
    strList = str.split("=")
    if len(strList) != 2:
        logger.error("Can't parse line '%s'." %(line))
        return False
    strList[0] = Util.clean_quote_space(strList[0].lower())
    strList[1] = Util.clean_quote_space(strList[1])
    if "template_name" in strList[0]:
        if "vsphere.template_name_gen" in dict.keys() and not "vsphere.template_name_db" in dict.keys():
            strList[0] = "vsphere.template_name_db"
        elif not "vsphere.template_name_db" in dict.keys() and not "vsphere.template_name_gen" in dict.keys():
            strList[0] = "vsphere.template_name_gen"
        else:
            logger.error("template_name_gen or template_name_db was defined twice. Please use only one template_name \
                         argument in gen and in db template file and put them in correct order into the array.")
            return False
    if strList[0] in dict.keys():
        logger.error("Configfile contains '%s' two times." %(strList[0]))
        return False
    dict[strList[0]] = convert_config_item(strList[0], strList[1], logger)
    if dict[strList[0]] == "" or dict[strList[0]] == None:
        if strList[0] in requiredConfigValues:
            logger.error("Empty value for '%s' which is required." %(strList[0]))
            return False
        else:
            logger.warning("Empty value for '%s'." %(strList[0]))
    return True

def get_vsphere_config(vagrantFolder, files,logger):
    dict={}
    for file in files:
        path=os.path.join(vagrantFolder,file)
        if not Util.check_file_readable(path):
            logger.error("Can't read %s." %(path))
            return {}
        file = open(path,"r")
        state = 0 # 0=outside, 1=inside vsphere provider block
        for line in file:
            if "config.vm.provider" in line.lower() and "vsphere" in line.lower():
                if state == 0:
                    state = 1
                else:
                        logger.error("Found a vsphere provider line two times without and end in between.")
                        return {}
            elif "end" in line.lower() and state == 1:
                break
            elif state == 1:
                if not handle_vsphere_config_line(line,dict,logger):
                    return {}
    keys = requiredConfigValues.keys()
    for key in dict.keys():
        if key in keys:
            keys.remove(key)
    if len(keys) > 0:
        logger.error("Not all required values are set. Missing: %s" %(keys))
        return {}
    return dict

def wait_for_task(task):
    while (task.info.state == vim.TaskInfo.State.running and task.info.cancelled == False):
        time.sleep(2)

def check_task(task):
    if task.info.state == vim.TaskInfo.State.success and task.info.error == None and task.info.cancelled == False:
        return True
    else:
        return False

def create_vm(vmDict, vmFolder, resourcePool, dataStore, logger):

    datastorePath = '[' + dataStore + '] ' + vmDict["name"]
    #datastorePath = '[' + datastore + ']'
    # bare minimum VM shell, no disks. Feel free to edit
    vmx_file = vim.vm.FileInfo(logDirectory=None,
                               snapshotDirectory=None,
                               suspendDirectory=None,
                               vmPathName=datastorePath)

    # Sources:
    # https://github.com/karmab/nuages/blob/master/portal/vsphere2.py
    # http://jensd.be/370/linux/create-a-new-virtual-machine-in-vsphere-with-python-pysphere-and-the-vmware-api
    devChanges = []
    scsiSpec = vim.vm.device.VirtualDeviceSpec()
    scsiSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    #scsiCtrl = vim.vm.device.VirtualLsiLogicController()
    scsiCtrl = vim.vm.device.ParaVirtualSCSIController()
    scsiCtrl.key = 1000
    scsiCtrl.busNumber = 0
    scsiCtrl.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.noSharing
    scsiSpec.device = scsiCtrl
    devChanges.append(scsiSpec)
    diskSize = int(vmDict["hdd"]) * 1024 * 1024
    # if int(datastore.freeSpace)/1024/1024/1024 - diskSize) <= 0:
    # error zu wenig speicher, aber bei thin egal?
    diskSpec = vim.vm.device.VirtualDeviceSpec()
    diskSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    diskSpec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.create
    diskSpec.device = vim.vm.device.VirtualDisk()
    diskSpec.device.controllerKey = 1000
    diskSpec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
    diskSpec.device.backing.thinProvisioned = True
    diskSpec.device.backing.diskMode = 'persistent'
    diskSpec.device.unitNumber = 0
    diskSpec.device.capacityInKB = diskSize
    devChanges.append(diskSpec)
    nicSpec = vim.vm.device.VirtualDeviceSpec()
    nicSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    nic = vim.vm.device.VirtualVmxnet3()
    desc = vim.Description()
    desc.label = "Network Adapter 1"
    nicBacking = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
    desc.summary = vmDict["network"]
    nicBacking.deviceName = vmDict["network"]
    nic.backing = nicBacking
    nic.key = 0
    nic.deviceInfo = desc
    nic.addressType = 'generated'
    nicSpec.device = nic
    devChanges.append(nicSpec)
    cdSpec = vim.vm.device.VirtualDeviceSpec()
    cdSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    connect = vim.vm.device.VirtualDevice.ConnectInfo()
    connect.startConnected = True
    connect.allowGuestControl = True
    connect.connected = True
    cd = vim.vm.device.VirtualCdrom()
    cd.connectable = connect
    cdBacking = vim.vm.device.VirtualCdrom.IsoBackingInfo()
    cdBacking.fileName = vmDict["iso"]
    cd.backing = cdBacking
    cd.controllerKey = 201
    cd.unitNumber = 0
    cd.key = -1
    cdSpec.device = cd
    devChanges.append(cdSpec)
    videoSpec = vim.vm.device.VirtualDeviceSpec()
    videoSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    videoSpec.device = vim.vm.device.VirtualVideoCard()
    videoSpec.device.videoRamSizeInKB = 8 * 1024
    videoSpec.device.numDisplays = 1
    videoSpec.device.enable3DSupport = False
    videoSpec.device.use3dRenderer = "automatic"
    devChanges.append(videoSpec)
    toolConfigInfo = vim.vm.ToolsConfigInfo()
    toolConfigInfo.syncTimeWithHost = True
    flagInfo = vim.vm.FlagInfo()
    flagInfo.runWithDebugInfo = False

    config = vim.vm.ConfigSpec(name=vmDict["name"], memoryMB=vmDict["ram"], numCPUs=vmDict["cpu"], files=vmx_file, guestId='debian6_64Guest',
                               version='vmx-10', deviceChange=devChanges, tools=toolConfigInfo, flags=flagInfo,
                               guestAutoLockEnabled=False)
    logger.info("Creating VM %s (vm_folder: %s, resource_pool: %s, datastore: %s)..." %(vmDict["name"], vmFolder.name, resourcePool.name, dataStore))
    task = vmFolder.CreateVM_Task(config=config, pool=resourcePool)
    wait_for_task(task)
    if check_task(task):
        return task.info.result
    else:
        logger.error("Can't create vm '%s': %s" %(vmDict["name"], task.info.error.msg))
        return None

def destroy_vm(vm, logger):
    # vms = search_vm_by_name("TEST", vmFolder)
    # if len(vms) > 1:
    #     logger.info("Found more than 1 VM with name %s, deleting all." %(vmName))
    # elif len(vms) < 1:
    #     return True
    # for vm in vms:
    logger.info("Destroying %s..." %(vm.name))
    if format(vm.runtime.powerState) == "poweredOn":
        logger.info("Attempting to power off %s first." %(vm.name))
        task = vm.PowerOffVM_Task()
        wait_for_task(task)
        if not check_task(task):
            logger.error("Error while powering off VM %s." %(vm.name))
    task = vm.Destroy_Task()
    wait_for_task(task)
    if not check_task(task):
        logger.error("Error while destroying off VM %s." %(vm.name))

def drop_iso(vm, logger):
    # Source https://github.com/rreubenur/vmware-pyvmomi-examples/blob/master/boot_vm_from_iso.py
    cdSpec = None
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualCdrom):
            cdSpec = vim.vm.device.VirtualDeviceSpec()
            cdSpec.device = device
            cdSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            cdSpec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            cdSpec.device.connectable.startConnected = False
            cdSpec.device.connectable.connected = False
    if cdSpec == None:
        logger.warning("Can't find VirtualCdrom on VM %s. " %(vm.name))
        return True
    vmConf = vim.vm.ConfigSpec()
    vmConf.deviceChange = [cdSpec]
    task = vm.ReconfigVM_Task(vmConf)
    wait_for_task(task)
    if not check_task(task):
        logger.error("Can't drop out VirtualCdrom of VM %s." %(vm.name))
        return False
    return True

def clone_vm_to_template(vm, destFolder, name, logger):
    logger.info("Cloning %s to template %s in ds: %s..." %(vm.name, name,destFolder.name))
    cloneSpec = vim.vm.CloneSpec()
    cloneSpec.location = vim.vm.RelocateSpec()
    cloneSpec.location.datastore = vm.datastore[0]
    cloneSpec.location.pool = vm.resourcePool
    cloneSpec.template = True
    cloneSpec.powerOn = False
    task = vm.CloneVM_Task(destFolder,name,cloneSpec)
    wait_for_task(task)
    if not check_task(task):
        logger.error("Error while cloning off VM %s to template %s in ds: %s." %(vm.name, name,destFolder.name))
        return False
    return True

def search_vm_by_name(name, vmFolder, depth=1):
    maxdepth=10
    vmList=[]
    if hasattr(vmFolder, 'childEntity'):
        if depth > maxdepth:
            return []
        for child in vmFolder.childEntity:
            found = search_vm_by_name(name,child,depth+1)
            if found != None and found != []:
                for element in found:
                    vmList.append(element)

    else:
        if vmFolder.name.lower() == name.lower():
            return [vmFolder]
        else:
            return []
    return vmList

def check_if_exist(name,vmFolder, logger):
    res = search_vm_by_name(name,vmFolder)
    if res == None or len(res) <= 0:
        return None
    if len(res) > 1:
        logger.warning("Found more than 1 VM with name %s." %(name))
    return res[0]

def power_on_vm(vm, logger):
    logger.info("Attempting to power on %s." %(vm.name))
    if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOn:
        task = vm.PowerOnVM_Task()
        wait_for_task(task)
        if check_task(task):
            return True
        else:
            logger.error("Error while powering on VM %s." %(vm.name))
            return False
    else:
        logger.warning("VM %s is already powered on." %(vm.name))
        return False

def wait_for_power_off(vm, logger, timeout=3600):
    logger.info("Waiting for %s to power off." %(vm.name))
    start = datetime.datetime.now()
    while vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
        time.sleep(2)
        if (datetime.datetime.now()-start).total_seconds() > timeout:
            logger.error("Waiting for %s to end install process timed out after %s seconds" %(vm["name"],timeout))
            return False
    return True

# Configure ArgumentParser
parser = argparse.ArgumentParser(prog="SetupVsphere.py",version=__version__,description="Bla", formatter_class=argparse.RawDescriptionHelpFormatter, epilog="")
parser.add_argument("-l", "--log", action='store_true', help="Be more verbose, log vagrant output.")
parser.add_argument("-f", "--vagrantfolder", metavar="VAGRANT", required=True, help="Path to folder with Vagrantfiles")
parser.add_argument("-o", "--overwrite", action='store_true', help="Deletes eventually existing templates/vms before creating them")
args = parser.parse_args()

# Configure Logging
logLevel = logging.WARN
if args.log:
    logLevel = logging.DEBUG
logging.basicConfig(level=logLevel)
logger = logging.getLogger(__name__)

# File checks and deletions (if necessary)
if not Util.check_folder(args.vagrantfolder,logger):
    exit(-1)
for vagrantCredFile in vagrantCredFiles:
    if not Util.check_file_exists(os.path.join(args.vagrantfolder,vagrantCredFile)):
        logger.error("%s not found." %(os.path.join(args.vagrantfolder,vagrantCredFile)))
        exit(-1)

vsphereConfigDict = get_vsphere_config(args.vagrantfolder, vagrantCredFiles, logger)
if len(vsphereConfigDict.keys()) < 1:
    logger.error("Error while parsing '%s'" %(os.path.join(args.vagrantfolder,vagrantCredFile)))
    exit(-1)


# def PrintVmInfo(vm, depth=1):
#    """
#    Print information for a particular virtual machine or recurse into a folder
#     with depth protection
#    """
#    maxdepth = 10
#
#    # if this is a group it will have children. if it does, recurse into them
#    # and then return
#    if hasattr(vm, 'childEntity'):
#       if depth > maxdepth:
#          return
#       vmList = vm.childEntity
#       for c in vmList:
#          PrintVmInfo(c, depth+1)
#       return
#
#    summary = vm.summary
#    print vm.summary
#    print("Name       : ", summary.config.name)
#    print("Path       : ", summary.config.vmPathName)
#    print("Guest      : ", summary.config.guestFullName)
#    annotation = summary.config.annotation
#    if annotation != None and annotation != "":
#       print("Annotation : ", annotation)
#    print("State      : ", summary.runtime.powerState)
#    if summary.guest != None:
#       ip = summary.guest.ipAddress
#       if ip != None and ip != "":
#          print("IP         : ", ip)
#    if summary.runtime.question != None:
#       print("Question  : ", summary.runtime.question.text)
#    print("")
#
#
# def get_obj(content, vimtype, name):
#     """
#     Return an object by name, if name is None the
#     first found object is returned
#     """
#     obj = None
#     container = content.viewManager.CreateContainerView(
#         content.rootFolder, vimtype, True)
#     for c in container.view:
#         if name:
#             if c.name == name:
#                 obj = c
#                 break
#         else:
#             obj = c
#             break
#
#     return obj


serviceInstance = None
try:
    serviceInstance = connect.SmartConnect(host=vsphereConfigDict["vsphere.host"],
                                            user=vsphereConfigDict["vsphere.user"],
                                            pwd=vsphereConfigDict["vsphere.password"],
                                            port=443)
    if not serviceInstance:
       logger.error("Could not connect to %s:443." % (vsphereConfigDict["vsphere.host"]))
       exit(-1)
    atexit.register(connect.Disconnect, serviceInstance)
    session_id = serviceInstance.content.sessionManager.currentSession.key
    # find datacenter
    content = serviceInstance.RetrieveContent()
    if len(content.rootFolder.childEntity) > 1:
        logger.warning("Found more than one datacenter, using first one.")
    elif len(content.rootFolder.childEntity) < 1:
        logger.error("Found no datacenters.")
        exit(-1)
    dc = content.rootFolder.childEntity[0]
    vmFolder = dc.vmFolder
    hosts = dc.hostFolder.childEntity
    if len(hosts) < 1:
        logger.error("Found no hosts in datacenter '%s'." %(dc.name))
        exit(-1)
    computeResource=None
    for cR in hosts:
        if cR.name.lower() == vsphereConfigDict["vsphere.compute_resource_name"].lower():
            computeResource = cR
    if computeResource == None:
        logger.error("Could not found compute resource '%s'." %(vsphereConfigDict["vsphere.compute_resource_name"]))
        exit(-1)
    if len(computeResource.resourcePool.resourcePool) < 1:
        logger.error("Found no resourcePools in datacenter '%s' on compute resource '%s'." %(dc.name, computeResource.name))
        exit(-1)
    resourcePool=None
    for rP in computeResource.resourcePool.resourcePool:
        if rP.name.lower() == vsphereConfigDict["vsphere.resource_pool_name"].lower():
            resourcePool = rP
    if resourcePool == None:
        logger.error("Could not found resource pool '%s'." %(vsphereConfigDict["vsphere.resource_pool_name"]))
        exit(-1)
    #
    # content = service_instance.RetrieveContent()
    # for child in content.rootFolder.childEntity:
    #   if hasattr(child, 'vmFolder'):
    #      datacenter = child
    #      vmFolder = datacenter.vmFolder
    #      vmList = vmFolder.childEntity
    #      for vm in vmList:
    #         PrintVmInfo(vm)
    container = content.viewManager.CreateContainerView(
        dc.vmFolder, [vim.Folder], True)
    destFolder=None
    searchFolder=vsphereConfigDict["vm_base_path"].split("/")[-1]
    for folder in container.view:
        if folder.name.lower() == searchFolder.lower():
            if destFolder != None:
                logger.warning("Found folder '%' more than one time, using first one." %(searchFolder.lower()))
            else:
                destFolder = folder

    # destfolder = get_obj(content, [vim.Folder], "nemar/baderas")
    # print destfolder.name
    for vmDict in vmDictList:
        for vmName in [vmDict["name"], "%s-Vorlage" %(vmDict["name"])]:
            vm = check_if_exist(vmName, dc.vmFolder, logger)
            if vm != None:
                if not args.overwrite:
                    logger.error("VM '%s' already exists, overwrite not enabled." %(vm.name))
                    exit(-1)
                else:
                    destroy_vm(vm, logger)
        vm = create_vm(vmDict, destFolder, resourcePool, vsphereConfigDict["vsphere.data_store_name"], logger)
        if vm != None:
            if not power_on_vm(vm, logger):
                exit(-1)
            if not wait_for_power_off(vm, logger, 3600):
                exit(-1)
            if not drop_iso(vm, logger):
                exit(-1)
            if not clone_vm_to_template(vm, destFolder, "%s-Vorlage" %(vmDict["name"]), logger):
                exit(-1)
            destroy_vm(vm, logger)
        else:
            logger.error("'%s' wasn't created, abort." %(vmDict["name"]))
            exit(-1)

except vmodl.MethodFault as error:
        print "Caught vmodl fault : " + error.msg
        connect.Disconnect(serviceInstance)
        exit(-1)
exit(0)