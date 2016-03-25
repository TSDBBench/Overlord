#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Andreas Bader'
__version__ = "0.01"

import logging
import argparse
from fabric.api import *
import os
import time
import Util
import subprocess
import threading
import Vm

logFile='pyvagrant.log'
pyYcsbPdfGenPath="ProcessYcsbLog.py"
testDBs=['basicdb','basicjdbc','basickairosdb','basicopentsdb']
vagrantCredFiles=["vagrantconf.rb", "vagrantconf_gen.rb", "vagrantconf_db.rb"]
vagrantBasicFilesFolder="basic"

availProviders=['virtualbox', 'vsphere', 'openstack', 'digital_ocean'] # First one is default

def run_workload(genDict, dbDict, dbName, workloadName, timeseries, granularity, bucket, test, onlyPrerun, debug, logger):
    if test:
        command = ""
    else:
        command = "nohup "
    ipStr = ""
    for dbKey in  sorted(dbDict.keys()):
        if dbDict[dbKey] == None or dbDict[dbKey] == "":
            ipStr += "%s " %(dbDict[dbKey].vm.hostname())
            logger.warning("IP of vm %s is None or an empty string, using hostname instead. This does not work on some providers (e.g. OpenStack)!" %(dbKey))
        else:
            ipStr += "%s " %(dbDict[dbKey].ip)
    ip0 = dbDict[dbDict.keys()[0]].ip
    if ip0 == None or ip0 == "":
        ip0 = dbDict[dbDict.keys()[0]].vm.hostname()
    logger.info("BEGIN: Running workload '%s' on %s with ip string %s." %(workloadName,ip0,ipStr))
    command+="python2 /home/vagrant/files/RunWorkload.py -d %s -w %s -i %s" %(dbName,workloadName,ipStr)
    if timeseries:
        command+=" -t"
    if granularity:
        command+=" -g %s" % (granularity)
    if onlyPrerun:
        command+=" -p"
        if not test:
            command += " -n"
    if bucket:
        command+=" -b %s" % (bucket)
    if debug:
        command += " --debug"
    if not test:
        command += " </dev/null"
    else:
        command += " -n"
    # here we expect to get an error and return code 255, seems to be normal when starting a backround process!
    ret =  genDict[genDict.keys()[0]].run_without_output(True, command, True,True,test)
    logger.info("END: Running workload '%s' on %s." %(workloadName,ip0))
    return ret

def wait_for_vm(vms, logger, timeout=3600, noshutdown=False):
    timerBegin=time.clock()
    if len(vms.keys()) < 1:
        logger.error("DB VM Dict has zero keys.")
        return False
    keyOfFirst=sorted(vms.keys())[0]
    while vms[keyOfFirst].vm.status()[0].state == "running":
        time.sleep(10)
        if time.clock()-timerBegin > 3600:
            logger.error("VM % is still up, waiting for it to shutdown timeouted after %s seconds." %(Vm.hostname(),timeout))
            return False
    if noshutdown:
        logger.info("Noshutdown is activated, trying to boot it up again.")
        for vmKey in sorted(vms.keys()):
            vms[vmKey].vm.up()
    return True

def get_remote_file(vm,remotePath,localPath,logger):
    with settings(host_string= vm.user_hostname_port(),
                 key_filename = vm.keyfile(),
                 disable_known_hosts = True):
        ret = get(remote_path=remotePath, local_path=localPath)
    if len(ret) > 1:
        logger.warning("More than one file copied from %s to %s: %s." %(remotePath, localPath, ret))
    if len(ret) < 1:
        logger.error("No files copied from %s to %s." %(remotePath, localPath))
    return ret

def rm_remote_file(vm,remotePath,logger):
    with settings(host_string= vm.user_hostname_port(),
                 key_filename = vm.keyfile(),
                 disable_known_hosts = True):
        run ("rm %s" %(remotePath))

def get_ycsb_file(vm,dbName,workloadName,logger):
    ret = get_remote_file(vm,"/home/vagrant/ycsb_%s_%s_*.log" %(dbName,workloadName),".",logger)
    if len(ret) > 1:
        logger.warning("More than one file copied for %s %s: %s. Taking first one." %(dbName, workloadName, ret))
    if len(ret) < 1:
        return None
    return ret[0]

def check_result_file(path):
    if Util.check_file_exists(path):
        file = open(path,"r")
        errorsFound = False
        errors = []
        warningsFound = False
        warnings = []
        exceptionsFound = False
        exceptions = []
        for line in file:
            if "warn" in line.lower():
                warningsFound = True
                warnings.append(line)
            if "error" in line.lower():
                errorsFound = True
                errors.append(line)
            if "exception" in line.lower():
                exceptionsFound = True
                exceptions.append(line)
        file.close();
        if errorsFound:
            logger.error("The following errors occurred: ")
            for error in errors:
                logger.error(error)
        if warningsFound:
            logger.warning("The following warnings occurred: ")
            for warning in warnings:
                logger.warning(warning)
        if exceptionsFound:
            logger.error("The following exceptions occurred: ")
            for exception in exceptions:
                logger.error(exception)
    else:
        logger.error("%s not found, can't check for errors." %(path))

def generate_html(paths, pdf, overwrite):
    if Util.check_file_exists(pyYcsbPdfGenPath):
        tsString = ""
        if args.timeseries:
            tsString=" -t"
        overwriteString = ""
        if overwrite:
            overwriteString=" -o"
        ycsbFileString = "-f"
        if len(paths) < 1:
            logger.error("Can't create html or pdf, paths is empty." )
            return False
        for path in paths:
            ycsbFileString += " %s" %(path)
        pdfString = ""
        if args.pdf:
            pdfString = " -p"
        multiStr = ""
        if len(paths) > 1:
            multiStr = " -s"
        try:
            retcode = subprocess.call("python2 %s %s%s%s%s%s" %(pyYcsbPdfGenPath,ycsbFileString,tsString,pdfString,overwriteString,multiStr), shell=True)
            if retcode != 0:
                logger.error("Generation of pdf/html returned with %s." %(retcode))
            else:
                logger.info("Successfully generated pdf/html file.")
        except OSError, e:
            logger.error("Errors occured while running pdf/html creation process.", exc_info=True)

    else:
        logger.error("Can't create html or pdf, %s does not exist." %(pyYcsbPdfGenPath))

def cleanup_vm(name, vm, pathFolder, pathVagrantfile, logger, linear):
    logger.info("Cleaning up %s." %(name))
    if vm != None and linear:
        vm.destroy()
    if pathFolder != None and pathFolder != "":
        if not Util.delete_folder(pathFolder,logger,True):
            logger.warning("Error while cleaning up %s." %(name))
            return False
    if pathVagrantfile != None and pathVagrantfile != "":
        if not Util.delete_file(pathVagrantfile,logger,True):
            logger.warning("Error while cleaning up %s." %(name))
            return False
    return True

def cleanup_vms(vmDict,logger, linear):
    logger.info("Begin Cleaning up.")
    if not linear:
        logger.info("Waiting to finish creation if not finished...")
        for key in vmDict.keys():
            # Wait for Creation to finish if unfinished
            vmDict[key].join()
            if vmDict[key].created:
                # Start Destroying if created :)
                vmDict[key].start()
                # Wait for Destroying to finish if unfinished
                vmDict[key].join()
    for key in vmDict.keys():
        cleanup_vm(key, vmDict[key].vm,vmDict[key].pathFolder,vmDict[key].pathVagrantfile, logger, linear)
        vmDict.pop(key)

# Configure ArgumentParser
parser = argparse.ArgumentParser(prog="TSDBBench.py",version=__version__,description="Bla", formatter_class=argparse.RawDescriptionHelpFormatter, epilog="")
parser.add_argument("-l", "--log", action='store_true', help="Be more verbose, log vagrant output.")
parser.add_argument("-t", "--tmpfolder", metavar="TMP", required=True, help="Path to Temp Space")
parser.add_argument("-f", "--vagrantfolders", metavar="VAGRANT", nargs='+', required=True, help="Path to folder(s) with Vagrantfiles. Files from additional folder(s) overwrite existing files from preceding folder(s).")
parser.add_argument("-w", "--workload", metavar="WORKLOAD", help="Only process workload WORKLOAD")
parser.add_argument("-d", "--databases", metavar="DATABASES", nargs='+', help="Only process workloads for all machines for DATABASE (Generator will always be created!), Set to 'all' for all DATABASES, set to 'test' for some special test DB set.)")
parser.add_argument("-n", "--nodestroy", action='store_true', help="Do not destroy VMs")
parser.add_argument("-o", "--noshutdown", action='store_true', help="Do not shutdown db vms, leave them running. Remember: After finishing workload they are rebooted!")
parser.add_argument("-s", "--timeseries", action='store_true', help="Force workload to do timeseries output")
parser.add_argument("-g", "--granularity", metavar="GRANULARITY", type=int, default=1000, help="If forcing to do timeseries output, use granularity GRANULARITY. Default:1000")
parser.add_argument("-b", "--bucket", metavar="BUCKET", type=int, default=100000, help="Use BUCKET bucket size for measurement histograms. Default:100000")
parser.add_argument("-m", "--html", action='store_true', help="Generate html output (ProcessYcsbLog.py required!")
parser.add_argument("-p", "--pdf", action='store_true', help="Generate pdf output (ProcessYcsbLog.py required!")
parser.add_argument("-u", "--nohup", action='store_true', help="Also fetch nohup output (for debugging only)")
parser.add_argument("-c", "--linear", action='store_true', help="Create VMs linear, do not use parallelisation.")
parser.add_argument("-r", "--provider", metavar="PROVIDER", type=str, default=availProviders[0], choices=availProviders, help="Which provider to use. Available: %s" %(availProviders))

args = parser.parse_args()

# Configure Logging
logLevel = logging.WARN
if args.log:
    logLevel = logging.DEBUG
logging.basicConfig(level=logLevel)
logger = logging.getLogger(__name__)
handler = logging.FileHandler(logFile)
handler.setLevel(logLevel)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

if args.provider == "digital_ocean" and not args.linear:
    logger.warning("Provider '%s' does not support parallel creation of VMs. Linear creation is automatically enabled. See https://github.com/devopsgroup-io/vagrant-digitalocean/pull/230 for further details." % args.provider)
    args.linear = True

# File checks and deletions (if necessary)
for folder in args.vagrantfolders:
    if not Util.check_folder(folder,logger):
        exit(-1)
for vagrantCredFile in vagrantCredFiles:
    found_cred_file = False
    for folder in args.vagrantfolders:
        if Util.check_file_exists(os.path.join(folder,vagrantCredFile)):
           found_cred_file = True
    if not found_cred_file:
        logger.error("%s not found in any of the given vagrantfolders (%s)." %(vagrantCredFile, args.vagrantfolders))
        exit(-1)
if not Util.check_folder(args.tmpfolder,logger):
    exit(-1)
if not Util.delete_file(logFile,logger,True):
    exit(-1)

generators={} # list of generator vms
dbs={} # dictinary of db vms
# format "name" = {"path_folder" : "/bla/tmppath", "path_vagrantfile":"/bla/tmppath/file", "vm": vm}


# Generating Generator VMs
generatorFound=False
for path, dir in Util.unsorted_paths(args.vagrantfolders,logger,"",True):
    if os.path.isdir(os.path.join(path, dir)) and dir == "generator":
        generatorFound=True
        found=0 # how many .vagrant files are found, At least 1 is needed!
        # search in all generator folders
        for path, file in Util.unsorted_paths(args.vagrantfolders,logger, "generator", True):
            if os.path.isfile(os.path.join(path, file)):
                split = file.rsplit(".vagrant", 1)
                # if rsplit is used on bla.vagrant, the result should be ["bla",""]
                if len(split)>1 and split[1] == "":
                    if split[0] in generators.keys():
                        continue
                    found+=1
                    # check if Generator, generator, Generator_1, etcpp. as machine is used, but always create if
                    # something else than Generator is given (Generator is always created!)
                    if not args.databases or args.databases == None or args.databases == [] \
                            or not Util.check_if_in_databases("generator", args.databases) \
                            or (args.databases and Util.check_if_eq_databases(split[0], args.databases)) \
                            or (args.databases and Util.check_if_eq_databases(split[0].rsplit("_",1)[0], args.databases)):
                        if args.linear:
                            virtMachine =  Vm.Vm(args.vagrantfolders, vagrantCredFiles, vagrantBasicFilesFolder, args.tmpfolder, split[0], logger, args.provider, args.log)
                            virtMachine.create_vm()
                            generators[virtMachine.name] = virtMachine
                            if not virtMachine.created:
                                logger.error("VM %s could not be created." %(split[0]))
                                if not args.nodestroy:
                                    cleanup_vms(generators,logger, args.linear)
                                exit(-1)
                        else:
                            virtMachine =  Vm.Vm(args.vagrantfolders, vagrantCredFiles, vagrantBasicFilesFolder, args.tmpfolder, split[0], logger, args.provider, args.log)
                            virtMachine.start()
                            Util.sleep_random(1.0,5.0)  # needed for openstack, otherwise two vms get the same floating ip
                            generators[virtMachine.name] = virtMachine
        if found == 0:
            logger.error("No .vagrant files found in %s." %(Util.unsorted_paths(args.vagrantfolders, logger, "generator")))
            exit(-1)
        break

if not generatorFound:
    logger.error("No Generator found, %s does not exist." %(Util.unsorted_paths(args.vagrantfolders, logger, "generator")))
    exit(-1)

if args.databases and (Util.check_if_eq_databases("generator",args.databases) or Util.check_if_eq_databases_rsplit("generator",args.databases)):
    if not args.linear:
        for generatorKey in generators.keys():
            logger.info("Wait for creation of %s to finish." %(generators[generatorKey].name))
            generators[generatorKey].join()
            if not generators[generatorKey].created:
                logger.error("VM %s could not be created." %(generators[generatorKey].name))
                if not args.nodestroy:
                    cleanup_vms(generators, logger, args.linear)
                exit(-1)
    if not args.nodestroy:
        cleanup_vms(generators, logger, args.linear)
    exit(0)

ycsbfiles=[]
processedDatabaseVMs=[] # for multi-vagrantfolder-function
processedDatabases=[]

# Doing Tests if basic or test is in given dbs
if args.databases and (Util.check_if_eq_databases("basic", args.databases) or Util.check_if_eq_databases("test", args.databases)):
    if not args.linear:
        for generatorKey in generators.keys():
            logger.info("Wait for creation of %s to finish." %(generators[generatorKey].name))
            generators[generatorKey].join()
            if not generators[generatorKey].created:
                logger.error("VM %s could not be created." %(generators[generatorKey].name))
                if not args.nodestroy:
                    cleanup_vms(generators, logger, args.linear)
                exit(-1)
    logger.info("Processing Test Databases")
    for database in testDBs:
        if args.workload:
            logger.info("Starting workload '%s' on Generator %s." %(database,generators[generators.keys()[0]].vm.hostname()))
            run_workload(generators, generators, database, args.workload, args.timeseries, args.granularity, args.bucket, True, False, args.log, logger)
            ycsbFile = get_ycsb_file(generators[generators.keys()[0]].vm,database.lower(),args.workload.lower(),logger)
            ycsbfiles.append(ycsbFile)
            check_result_file(ycsbFile)
            if (args.html or args.pdf) and len(ycsbfiles) == 1:
                generate_html([ycsbFile],args.pdf,False)

        else:
            logger.info("No Workload given, doing nothing.")
    if not args.nodestroy:
        cleanup_vms(generators, logger, args.linear)
else:
    # Generating Database VMs
    logger.info("Processing Database VMs" )
    for path, dir in Util.unsorted_paths(args.vagrantfolders, logger, "", False):
        if os.path.isdir(os.path.join(path, dir)):
            if dir== "generator" or dir.find(".")==0 or dir in processedDatabases:
                continue
            found=0 # how many .vagrant files are found, At least 1 is needed!
            if not args.databases or args.databases == "" \
                    or (args.databases and not Util.check_if_eq_databases(dir, args.databases) and not Util.check_if_eq_databases("all", args.databases)):
                continue
            logger.info("Processing %s." % (dir))
            for path2, file in Util.unsorted_paths(args.vagrantfolders, logger, dir, True):
                if os.path.isfile(os.path.join(path, dir, file)):
                    split = file.rsplit(".vagrant", 1)
                    # if rsplit is used on bla.vagrant, the result should be ["bla",""]
                    if len(split)>1 and split[1] == "":
                        found+=1
                        if args.databases and args.databases != None and args.databases != [] \
                                and split[0] not in processedDatabaseVMs \
                                and (Util.check_if_eq_databases(split[0], args.databases) \
                                or Util.check_if_eq_databases(split[0].rsplit("_",1)[0], args.databases) \
                                or Util.check_if_eq_databases("all", args.databases)):
                            processedDatabaseVMs.append(split[0])
                            if args.linear:
                                virtMachine =  Vm.Vm(args.vagrantfolders, vagrantCredFiles, vagrantBasicFilesFolder, args.tmpfolder, split[0], logger, args.provider, args.log)
                                virtMachine.create_vm()
                                dbs[virtMachine.name] = virtMachine
                                if not virtMachine.created:
                                    logger.error("VM %s could not be created." %(split[0]))
                                    if not args.nodestroy:
                                        cleanup_vms(generators, logger, args.linear)
                                        cleanup_vms(dbs, logger, args.linear)
                                    exit(-1)
                            else:
                                virtMachine =  Vm.Vm(args.vagrantfolders, vagrantCredFiles, vagrantBasicFilesFolder, args.tmpfolder, split[0], logger, args.provider, args.log)
                                virtMachine.start()
                                Util.sleep_random(1.0,5.0)  # needed for openstack, otherwise two vms get the same floating ip
                                dbs[virtMachine.name] = virtMachine
            processedDatabases.append(dir)
            if not args.linear:
                for generatorKey in generators.keys():
                    logger.info("Wait for creation of %s to finish." %(generators[generatorKey].name))
                    generators[generatorKey].join()
                    if not generators[generatorKey].created:
                        logger.error("VM %s could not be created." %(generators[generatorKey].name))
                        if not args.nodestroy:
                            cleanup_vms(generators, logger, args.linear)
                            cleanup_vms(dbs, logger, args.linear)
                        exit(-1)
                for dbKey in dbs.keys():
                    logger.info("Wait for creation of %s to finish." %(dbs[dbKey].name))
                    dbs[dbKey].join()
                    if not dbs[dbKey].created:
                        logger.error("VM %s could not be created." %(dbs[dbKey].name))
                        if not args.nodestroy:
                            cleanup_vms(generators, logger, args.linear)
                            cleanup_vms(dbs, logger, args.linear)
                        exit(-1)
            if found == 0:
                logger.error("No .vagrant files found in %s." % (Util.unsorted_paths(args.vagrantfolders, logger, dir)))


            if args.workload:
                logger.info("Starting workload '%s' on %s on Generator %s." %(args.workload,dbs[dbs.keys()[0]].vm.hostname(),generators[generators.keys()[0]].vm.hostname()))
                run_workload(generators, dbs, dir, args.workload, args.timeseries, args.granularity, args.bucket, False, False, args.log, logger)
                logger.info("Waiting for workload to finish...")
                wait_for_vm(dbs, logger, 3600, args.noshutdown)
                ycsbFile = get_ycsb_file(generators[generators.keys()[0]].vm, dir.lower(), args.workload.lower(), logger)
                ycsbfiles.append(ycsbFile)
                if args.nohup:
                    logger.info("Trying to fetch nohup files from generators.")
                    nohupCounter=0
                    for generatorKey in generators.keys():
                        get_remote_file(generators[generatorKey].vm,"/home/vagrant/nohup.out","./nohup_%s_%s_%s.out" % (dir.lower(), args.workload.lower(), nohupCounter), logger)
                        rm_remote_file(generators[generatorKey].vm,"/home/vagrant/nohup.out",logger)
                        nohupCounter+=1;

                check_result_file(ycsbFile)
                if (args.html or args.pdf) and len(args.databases) == 1 and len(ycsbfiles) == 1:
                    generate_html([ycsbFile],args.pdf,False)

            else:
                logger.info("No Workload given, just running Prerun commands.")
                run_workload(generators, dbs, dir, args.workload, args.timeseries, args.granularity, args.bucket, False, True, args.log, logger)
                if args.nohup:
                    logger.info("Trying to fetch nohup files from generators.")
                    nohupCounter=0
                    for generatorKey in generators.keys():
                        get_remote_file(generators[generatorKey].vm,"/home/vagrant/nohup.out","./nohup_%s_%s_%s.out" % (dir.lower(), "none", nohupCounter), logger)
                        rm_remote_file(generators[generatorKey].vm,"/home/vagrant/nohup.out",logger)
                        nohupCounter+=1;

            if not args.nodestroy and not args.noshutdown:
                cleanup_vms(dbs,logger, args.linear)

    if not args.nodestroy and not args.noshutdown:
        cleanup_vms(dbs, logger, args.linear)
        cleanup_vms(generators, logger , args.linear)

if (args.html or args.pdf) and len(ycsbfiles) > 1:
    logger.info("More than one DB given, also generating combined html/pdf file.")
    generate_html(ycsbfiles,args.pdf,True)

exit(0)