#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Andreas Bader'
__version__ = "1.00"

import logging
import logging.config
import argparse
from fabric.api import *
import os
import time
import Util
import subprocess
import threading
import Vm
import ConfigParser
import datetime
import re
import platform

pyYcsbPdfGenPath="ProcessYcsbLog.py"
testDBs=['basicdb','basicjdbc','basickairosdb','basicopentsdb']
vagrantCredFiles=["vagrantconf.rb", "vagrantconf_gen.rb", "vagrantconf_db.rb", "aws_commands.txt"]
vagrantBasicFilesFolder="basic"
logFile="debug_log_%s.log" % (time.strftime("%Y%m%d%H%M%S", time.localtime()))
logConfigFile="logging.conf"

availProviders=['virtualbox', 'vsphere', 'openstack', 'digital_ocean', 'aws'] # First one is default

def run_workload(genDict, dbDict, dbName, workloadName, timeseries, granularity, bucket, test, onlyPrerun, debug, logger):
    if test:
        command = ""
    else:
        command = "nohup "
    ipStr = ""
    hnStr = ""
    for dbKey in  sorted(dbDict.keys()):
        if dbDict[dbKey] == None or dbDict[dbKey] == "":
            ipStr += "%s " %(dbDict[dbKey].vm.hostname())
            logger.warning("IP of vm %s is None or an empty string, using hostname instead. This does not work on some providers (e.g. OpenStack)!" %(dbKey))
        else:
            ipStr += "%s " %(dbDict[dbKey].ip)
        hnStr += "%s " % (dbDict[dbKey].name) #.vm.hostname() does not work here!
    ip0 = dbDict[dbDict.keys()[0]].ip
    if ip0 == None or ip0 == "":
        ip0 = dbDict[dbDict.keys()[0]].vm.hostname()
    logger.info("BEGIN: Running workload '%s' on %s with ip string %s and hostname string %s." %(workloadName,ip0,ipStr,hnStr))
    command+="python2 /home/vagrant/files/RunWorkload.py -d %s -w %s -i %s -s %s" %(dbName,workloadName,ipStr,hnStr)
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
    try:
        while vms[keyOfFirst].vm.status()[0].state == "running":
            time.sleep(10)
            if time.clock()-timerBegin > 3600:
                logger.error("VM % is still up, waiting for it to shutdown timeouted after %s seconds." %(Vm.hostname(),timeout))
                return False
    except IndexError:
        logger.error("Python-Vagrant could not parse the output of vagrant status --machine-readable, try check it for "
                     "yourself. The output should be parsable CSV. Sometimes the \"plugin outdated\" message causes "
                     "this error. Check that all vagrant plugins are uptodate.", exc_info=True)
        return False
    if noshutdown:
        logger.info("Noshutdown is activated, trying to boot it up again.")
        for vmKey in sorted(vms.keys()):
            vms[vmKey].vm.up()
    return True

def get_remote_file(vm,remotePath,localPath,logger):
    with hide('output','running', 'warnings', 'stdout', 'stderr'),\
         settings(host_string= vm.user_hostname_port(),
                 key_filename = vm.keyfile(),
                 disable_known_hosts = True, warn_only=True):
        ret = get(remote_path=remotePath, local_path=localPath)
    if len(ret) > 1:
        logger.warning("More than one file copied from %s to %s: %s." %(remotePath, localPath, ret))
    if len(ret) < 1:
        logger.error("No files copied from %s to %s." %(remotePath, localPath))
    return ret

def rm_remote_file(vm,remotePath,logger):
    with hide('output','running', 'stdout'),\
         settings(host_string= vm.user_hostname_port(),
                  key_filename = vm.keyfile(),
                  disable_known_hosts = True,
                  warn_only = True):
        run ("rm %s" %(remotePath))

def get_ycsb_file(vm,dbName,workloadName,logger):
    ret = get_remote_file(vm,"/home/vagrant/ycsb_%s_%s_*.log" %(dbName,workloadName),".",logger)
    if len(ret) > 1:
        logger.warning("More than one file copied for %s %s: %s. Taking first one." %(dbName, workloadName, ret))
    if len(ret) < 1:
        return None
    return ret[0]

# returns True when errors are found
def check_result_file(path, logger):
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
            return True
        if warningsFound:
            logger.warning("The following warnings occurred: ")
            for warning in warnings:
                logger.warning(warning)
            return True
        if exceptionsFound:
            logger.error("The following exceptions occurred: ")
            for exception in exceptions:
                logger.error(exception)
            return True
    else:
        logger.error("%s not found, can't check for errors." %(path))
        return True

# returns True when not all queries are executed
# only possible for testworkload and testworkloadb
# machtes two lines:
# [INSERT], Operations, 1000
# and
# [INSERT], Return=0, 1000
# both numbers on the end of the line must be the same
def check_result_file_extended(path, workload, logger):
    if workload not in ["testworkloada", "testworkloadb"]:
        return False
    if Util.check_file_exists(path):
        file = open(path, "r")
        resultDict={}
        error = False
        atLeastOneReturnedZeroDict = {}
        for line in file:
            if re.match("\[(INSERT|READ|SCAN|AVG|COUNT|SUM)\],\s*(Return=|Operations).+$", line) != None:
                splitters = line.split(",")
                queryType = splitters[0].replace("[","").replace("]","")
                lineType = splitters[1]
                amount = int(splitters[2].replace(" ",""))
                if "Operations" in lineType:
                    if queryType in resultDict.keys():
                        error = True # nothing should be found twice
                    else:
                        resultDict[queryType] = [amount,0]
                elif "Return=" in lineType:
                    # check if at least a few non-INSERT queries returned 0 (=succesful)
                    # INSERT queries must return 0, -1 is not allowed
                    if queryType not in atLeastOneReturnedZeroDict.keys():
                        atLeastOneReturnedZeroDict[queryType] = False
                    if "Return=0" in lineType and "INSERT" in queryType and amount == resultDict[queryType][0]:
                        atLeastOneReturnedZeroDict[queryType] = True
                    elif "Return=0" in lineType and amount > 0:
                        atLeastOneReturnedZeroDict[queryType] = True
                    if queryType not in resultDict.keys():
                        error = True # should already be found in operations line
                    else:
                        resultDict[queryType][1]+=amount
        sum = 0
        for key in resultDict:
            if key != "INSERT":
                sum += resultDict[key][1]
            if resultDict[key][0] != resultDict[key][1]:
                return True
        for key in atLeastOneReturnedZeroDict:
            if not atLeastOneReturnedZeroDict[key]:
                return True
        if (workload == "testworkloada" and len(resultDict.keys()) != 2 and sum !=  resultDict["INSERT"][1]) or \
           (workload == "testworkloadb" and len(resultDict.keys()) != 5 and sum !=  resultDict["INSERT"][1])    :
            return True
        return error
    else:
        logger.error("%s not found, can't check for errors." % (path))
        return True

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

overallTime=datetime.datetime.now()

# Configure ArgumentParser
parser = argparse.ArgumentParser(prog="TSDBBench.py",version=__version__,description="A tool for automated bencharming of time series databases.", formatter_class=argparse.RawDescriptionHelpFormatter, epilog="")
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
parser.add_argument("-z", "--test", action='store_true', help="Test mode. Goes through all or the given databases with the given workload and tests each database. When using testworkloada or testworkloadb it is also checked if the amount of queries matches.")

args = parser.parse_args()

# Configure Logging
logLevel = logging.WARN
if args.log and not args.test:
    logLevel = logging.DEBUG
try:
    logging.config.fileConfig(logConfigFile)
except ConfigParser.NoSectionError:
    print("Error: Can't load logging config from '%s'." %(logConfigFile))
    exit(-1)

logger = logging.getLogger("TSDBBench")
if not args.test:
    for handler in logger.handlers:
        handler.setLevel(logLevel)
else:
    logger.handlers = []

if not Util.delete_file(logFile,logger,True):
    exit(-1)

if args.log or args.test:
    handler = logging.FileHandler(logFile)
    if args.test:
        handler.setLevel(logging.DEBUG)
    else:
        handler.setLevel(logLevel)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

if args.test:
    print("Executing in test mode.")
    print("Python: %s" %(platform.python_version()))
    print("Platform: %s" %(platform.platform()))
    print("Databases: %s" % (args.databases))
    print("Workload: %s" %(args.workload))
    if args.workload == "testworkloada" or args.workload == "testworkloadb":
        print("Result checking is used for this workload.")
    else:
        print("Result checking is NOT used for this workload.")
    print("Provider: %s" %(args.provider))
    print("Parallel creation of VMs: %s" %(not args.linear))
    print("Log is written to '%s'." %(logFile))
    print("Logging to shell is disabled (except fabric warnings).")

if args.provider == "digital_ocean" and not args.linear:
    logger.warning("Provider '%s' does not support parallel creation of VMs. Linear creation is automatically enabled. See https://github.com/devopsgroup-io/vagrant-digitalocean/pull/230 for further details." % args.provider)
    args.linear = True

if len(args.databases) > 1 and (args.nodestroy or args.noshutdown):
    logger.warning("The arguments --noshutdown and --nodestroy do not work with multiple databases at one run. Both are automatically disabled.")
    args.nodestroy = False
    args.noshutdown = False

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

generators={} # list of generator vms
dbs={} # dictinary of db vms
# format "name" = {"path_folder" : "/bla/tmppath", "path_vagrantfile":"/bla/tmppath/file", "vm": vm}

creationTimesGenerators=datetime.datetime.now()

termSize = Util.get_terminal_size(logger)

# Generating Generator VMs
if args.test:
    print(Util.multiply_string("-", termSize))
    print("Stage 1: Creation of generator VMs.")
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
                            if args.test:
                                Util.print_wo_nl(split[0] + Util.multiply_string(".", termSize-len(split[0])-len("[ERROR]")))
                            virtMachine =  Vm.Vm(args.vagrantfolders, vagrantCredFiles, vagrantBasicFilesFolder, args.tmpfolder, split[0], logger, args.provider, args.log)
                            virtMachine.create_vm()
                            generators[virtMachine.name] = virtMachine
                            if not virtMachine.created:
                                if args.test:
                                    print("[ERROR]")
                                else:
                                    logger.error("VM %s could not be created." %(split[0]))
                                if not args.nodestroy:
                                    cleanup_vms(generators,logger, args.linear)
                                exit(-1)
                            if args.test:
                                print("[OK]")
                        else:
                            virtMachine =  Vm.Vm(args.vagrantfolders, vagrantCredFiles, vagrantBasicFilesFolder, args.tmpfolder, split[0], logger, args.provider, args.log)
                            virtMachine.start()
                            Util.sleep_random(1.0,5.0)  # needed for openstack, otherwise two vms get the same floating ip
                            generators[virtMachine.name] = virtMachine
        if found == 0:
            logger.error("No .vagrant files found in %s." %(Util.unsorted_paths(args.vagrantfolders, logger, "generator")))
            exit(-1)
        break

if args.linear:
    creationTimesGenerators = datetime.datetime.now() - creationTimesGenerators

if not generatorFound:
    logger.error("No Generator found, %s does not exist." %(Util.unsorted_paths(args.vagrantfolders, logger, "generator")))
    exit(-1)

if args.databases and (Util.check_if_eq_databases("generator",args.databases) or Util.check_if_eq_databases_rsplit("generator",args.databases)):
    if not args.linear:
        for generatorKey in generators.keys():
            if args.test:
                Util.print_wo_nl(generatorKey + Util.multiply_string(".", termSize - len(generatorKey) - len("[ERROR]")))
            logger.info("Wait for creation of %s to finish." %(generators[generatorKey].name))
            generators[generatorKey].join()
            if not generators[generatorKey].created:
                if args.test:
                    print("[ERROR]")
                else:
                    logger.error("VM %s could not be created." %(generators[generatorKey].name))
                if not args.nodestroy:
                    cleanup_vms(generators, logger, args.linear)
                exit(-1)
            if args.test:
                print("[OK]")
        creationTimesGenerators = datetime.datetime.now() - creationTimesGenerators
    if not args.nodestroy:
        cleanup_vms(generators, logger, args.linear)
    exit(0)

if args.test and args.linear:
    print(Util.multiply_string("-", termSize))
    print("Stage 2: Creation of database VMs  and execution of workloads.")

ycsbfiles=[]
processedDatabaseVMs=[] # for multi-vagrantfolder-function
processedDatabases=[]

failedDatabases=[]
workingDatabases=[]
notTestedDatabases=list(args.databases)
creationTimesDB={}
workloadTimes={}

# Doing Tests if basic or test is in given dbs
if args.databases and (Util.check_if_eq_databases("basic", args.databases) or Util.check_if_eq_databases("test", args.databases)):
    if not args.linear:
        for generatorKey in generators.keys():
            if args.test:
                Util.print_wo_nl(
                    generatorKey + Util.multiply_string(".", termSize - len(generatorKey) - len("[ERROR]")))
            logger.info("Wait for creation of %s to finish." %(generators[generatorKey].name))
            generators[generatorKey].join()
            if not generators[generatorKey].created:
                if args.test:
                    print("[ERROR]")
                else:
                    logger.error("VM %s could not be created." %(generators[generatorKey].name))
                if not args.nodestroy:
                    cleanup_vms(generators, logger, args.linear)
                exit(-1)
            if args.test:
                print("[OK]")
            creationTimesGenerators = datetime.datetime.now() - creationTimesGenerators
    logger.info("Processing Test Databases")
    for database in testDBs:
        if args.workload:
            logger.info("Starting workload '%s' on Generator %s." %(database,generators[generators.keys()[0]].vm.hostname()))
            run_workload(generators, generators, database, args.workload, args.timeseries, args.granularity, args.bucket, True, False, args.log, logger)
            ycsbFile = get_ycsb_file(generators[generators.keys()[0]].vm,database.lower(),args.workload.lower(),logger)
            ycsbfiles.append(ycsbFile)
            check_result_file(ycsbFile, logger)
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
                    or re.match("basic.*", dir) != None \
                    or (args.databases and not Util.check_if_eq_databases(dir, args.databases) and not Util.check_if_eq_databases("all", args.databases)):
                continue
            if Util.check_if_eq_databases("all", args.databases):
                if "all" in notTestedDatabases:
                    notTestedDatabases.remove("all")
                if dir not in notTestedDatabases and dir not in workingDatabases and dir not in failedDatabases:
                    notTestedDatabases.append(dir)
            logger.info("Processing %s." % (dir))
            creationTimesDB[dir]=datetime.datetime.now()
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
                                if args.test:
                                    Util.print_wo_nl(dir + Util.multiply_string(".", termSize - len(dir) - len("[ERROR]")))
                                virtMachine =  Vm.Vm(args.vagrantfolders, vagrantCredFiles, vagrantBasicFilesFolder, args.tmpfolder, split[0], logger, args.provider, args.log)
                                virtMachine.create_vm()
                                dbs[virtMachine.name] = virtMachine
                                if not virtMachine.created:
                                    if args.test:
                                        print("[ERROR]")
                                    else:
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
            if args.linear:
                creationTimesDB[dir] = datetime.datetime.now() - creationTimesDB[dir]
            processedDatabases.append(dir)
            if not args.linear:
                for generatorKey in generators.keys():
                    if args.test and len(workingDatabases) == 0: # only before first database
                        Util.print_wo_nl(generatorKey + Util.multiply_string(".", termSize - len(generatorKey) - len("[ERROR]")))
                    logger.info("Wait for creation of %s to finish." %(generators[generatorKey].name))
                    generators[generatorKey].join()
                    if not generators[generatorKey].created:
                        if args.test and len(workingDatabases) == 0: # only before first database
                            print("[ERROR]")
                        else:
                            logger.error("VM %s could not be created." %(generators[generatorKey].name))
                        if not args.nodestroy:
                            cleanup_vms(generators, logger, args.linear)
                            cleanup_vms(dbs, logger, args.linear)
                        exit(-1)
                    if args.test and len(workingDatabases) == 0: # only before first database
                        print("[OK]")
                if args.test:
                    if len(workingDatabases) == 0: # only before first database, after last generator VM in parellel mode
                        creationTimesGenerators = datetime.datetime.now() - creationTimesGenerators
                        print(Util.multiply_string("-", termSize))
                        print("Stage 2: Creation of database VMs  and execution of workloads.")
                    Util.print_wo_nl(dir + Util.multiply_string(".", termSize - len(dir) - len("[ERROR]")))
                for dbKey in dbs.keys():
                    logger.info("Wait for creation of %s to finish." %(dbs[dbKey].name))
                    dbs[dbKey].join()
                    if not dbs[dbKey].created:
                        if args.test:
                            print("[ERROR]")
                        else:
                            logger.error("VM %s could not be created." %(dbs[dbKey].name))
                        if not args.nodestroy:
                            cleanup_vms(generators, logger, args.linear)
                            cleanup_vms(dbs, logger, args.linear)
                        exit(-1)
                creationTimesDB[dir] = datetime.datetime.now() - creationTimesDB[dir]
            if found == 0:
                logger.error("No .vagrant files found in %s." % (Util.unsorted_paths(args.vagrantfolders, logger, dir)))


            if args.workload:
                workloadTimes[dir] = datetime.datetime.now()
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
                workloadTimes[dir] = datetime.datetime.now() - workloadTimes[dir]
                checkResult=check_result_file(ycsbFile, logger)
                if args.test:
                    checkRestul2 = check_result_file_extended(ycsbFile, args.workload, logger)
                    if checkResult or checkRestul2:
                        print("[ERROR]")
                        failedDatabases.append(dir)
                        notTestedDatabases.remove(dir)
                    else:
                        print("[OK]")
                        workingDatabases.append(dir)
                        notTestedDatabases.remove(dir)
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
    if args.test:
        print(Util.multiply_string("-", termSize))
        print("Stage 3: Creation ofcombined PDF file.")
    logger.info("More than one DB given, also generating combined html/pdf file.")
    generate_html(ycsbfiles,args.pdf,True)

overallTime = datetime.datetime.now() - overallTime

if args.test:
    print(Util.multiply_string("-", termSize))
    print("Statistics:")
    print("Failed databases: %s" %(failedDatabases))
    print("Not tested databases: %s" % (notTestedDatabases))
    print("Working databases: %s" % (workingDatabases))
    print("Amount of time needed overall: %s" %(Util.timedelta_to_string(overallTime)))
    print("Amount of time needed to create generator VMs: %s" %(Util.timedelta_to_string(creationTimesGenerators)))
    print("Amount of time needed to create database VMs:")
    for key in creationTimesDB.keys():
        timedelta_str = Util.timedelta_to_string(creationTimesDB[key])
        print(key + Util.multiply_string("-", termSize-len(key)-len(timedelta_str)) + timedelta_str)
    print("Amount of time needed to complete %s:" %(args.workload))
    for key in workloadTimes.keys():
        timedelta_str = Util.timedelta_to_string(workloadTimes[key])
        print(key + Util.multiply_string("-", termSize - len(key) - len(timedelta_str)) + timedelta_str)
    print("Ending with return code 0.")

exit(0)