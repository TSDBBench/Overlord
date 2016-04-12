#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Andreas Bader'
__version__ = "0.01"

## replaces old workload_<dbname>.sh scripts for better multi vm support

import argparse
import logging
import databases
from fabric.api import *
import re
import locale
import time

def clean_exit(code, hostnames, shutdown=True):
    if shutdown:
        for hostname in hostnames:
            run_on_vm(hostname, "/home/vagrant/.ssh/id_rsa", True, "sudo poweroff",logger,False,True,True,False)
    exit(code)

def run_on_vm (hostString, keyFilename, disableKnownHosts,command,logger,warn_only=False,quiet=False,test=False,getResult=False):
    # Same as TSDBBench.py run_on_vm
    with settings(host_string= hostString,
                 key_filename = keyFilename,
                 disable_known_hosts = disableKnownHosts):
        result = run(command,warn_only=warn_only, quiet=quiet)
        if result.return_code == 0 or (warn_only and result.return_code == 255) or (test and result.return_code == -1):
            if getResult:
                return result
            return True
        else:
            logger.error("Command '%s' on %s returned %s." %(command, hostString, result.return_code))
            if getResult:
                return result
            return False

def run_local (command, logger, test=False, getResult=False):
    result = local(command, capture=True)
    if result.return_code == 0 or (test and result.return_code == -1):
        if getResult:
            return result
        return True
    else:
        logger.error("Command '%s' returned %s (local)." %(command, result.return_code))
        if getResult:
            return result
        return False

def get_local_ip(logger):
    result = run_local('sudo ifconfig | grep -E -o "(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)" | head -n1',logger,False,True)
    if result != None and result != False and result.return_code == 0:
        return result.stdout
    else:
        if result != None and result != False:
            logger.error("Can't get local IP. Return Code: '%s' STDOUT: '%s'." %(result.return_code,result.stdout))
        else:
            logger.error("Can't get local IP.")
        return None

def get_local_hostname(logger):
    result = run_local('hostname', logger, False, True)
    if result != None and result != False and result.return_code == 0:
        return result.stdout
    else:
        if result != None and result != False:
            logger.error(
                "Can't get local Hostname. Return Code: '%s' STDOUT: '%s'." % (result.return_code, result.stdout))
        else:
            logger.error("Can't get local Hostname.")
        return None

def check_keys(dict, keys):
    foundAll = True
    for key in keys:
        if key not in dict.keys():
            foundAll = False
    return foundAll

def get_time_file():
    act_loc=locale.getlocale()
    try:
        locale.setlocale(locale.LC_ALL,'en_US.UTF-8')
    except Exception, e:
        logger.error('Failed to set locale, do you have locale en_US.UTF-8 installed?', exc_info=True)
        clean_exit(-1,  args.ip, not args.noshutdown)
    timeStr=time.strftime("%Y%m%d%H%M",time.localtime())
    locale.setlocale(locale.LC_ALL,act_loc)
    return timeStr

def get_time_log():
    act_loc=locale.getlocale()
    try:
        locale.setlocale(locale.LC_ALL,'en_US.UTF-8')
    except Exception, e:
        logger.error('Failed to set locale, do you have locale en_US.UTF-8 installed?', exc_info=True)
        clean_exit(-1,  args.ip, not args.noshutdown)
    timeStr=time.strftime("%a %b %d %H:%M:%S %Z %Y",time.localtime())
    locale.setlocale(locale.LC_ALL,act_loc)
    return timeStr

# gets space for every db for every folder and appends it to spaceDict
def get_space(ips, spaceDict, folders, local):
    if local:
        space=0
        if "basic" not in spaceDict.keys():
            spaceDict["basic"]=[]
        for folder in folders:
            spaceStr = run_local("sudo du %s --summarize" %(folder), logger, False, True)
            if spaceStr == None or spaceStr == "":
                logger.error('Failed to get space for folder %s (local).' %(folder))
                clean_exit(-1,  args.ip, not args.noshutdown)
            try:
                searchRes = re.search("[0-9]+",spaceStr)
                if searchRes == None:
                    logger.error('Failed to get space for folder %s (local).' %(folder))
                    clean_exit(-1,  args.ip, not args.noshutdown)
                try:
                    space += int(searchRes.group(0))
                except Exception, e:
                    logger.error("Can't convert %s to int." %(space), exc_info=True)
                    clean_exit(-1,  args.ip, not args.noshutdown)
            except Exception, e:
                logger.error('Failed to get space for folder %s (local).' %(folder), exc_info=True)
                clean_exit(-1,  args.ip, not args.noshutdown)
        spaceDict["basic"] += [space]
    else:
        for ip in ips:
            if ip not in spaceDict.keys():
                spaceDict[ip] = []
            space=0
            for folder in folders:
                spaceStr = run_on_vm (ip, "/home/vagrant/.ssh/id_rsa", True,"sudo du %s --summarize" %(folder),logger,False,True,False, True)
                if spaceStr == None or spaceStr == "":
                    logger.error('Failed to get space for folder %s for vm %s.' %(folder, ip))
                    clean_exit(-1,  args.ip, not args.noshutdown)
                try:
                    searchRes = re.search("[0-9]+",spaceStr)
                    if searchRes == None:
                        logger.error('Failed to get space for folder %s for vm %s.' %(folder, ip))
                        clean_exit(-1,  args.ip, not args.noshutdown)
                    try:
                        space += int(searchRes.group(0))
                    except Exception, e:
                        logger.error("Can't convert %s to int." %(space), exc_info=True)
                        clean_exit(-1,  args.ip, not args.noshutdown)
                except Exception, e:
                    logger.error('Failed to get space for folder %s for vm %s.' %(folder, ip), exc_info=True)
                    clean_exit(-1,  args.ip, not args.noshutdown)
            spaceDict[ip] += [space]

def check_add_space(spaceDict):
    listLen = -1
    totalSpace=[]
    for key in spaceDict.keys():
        if listLen == -1:
            listLen = len(spaceDict[key])
            totalSpace = list(spaceDict[key])
        elif len(spaceDict[key]) != listLen:
            logger.error('Got two space lists that do not have the same length. This should not happen.')
            clean_exit(-1,  args.ip, not args.noshutdown)
        else:
            for i in range(0,len(spaceDict[key])):
                totalSpace[i] += spaceDict[key][i]
    return totalSpace

def make_space_str(spaceList):
    spaceStr=""
    for element in spaceList:
        if spaceStr == "":
            spaceStr+="%s" %(element)
        else:
            spaceStr+=" %s" %(element)
    return spaceStr

def remote_sync(ips):
    for ip in ips:
        if not run_on_vm (ip, "/home/vagrant/.ssh/id_rsa", True,"sudo sync",logger,False,True,False, False):
            logger.error('Failed to sync for %s.' %(ip))
            clean_exit(-1,  args.ip, not args.noshutdown)

def local_sync():
    run_local("sudo sync",logger,False)

def replStrIp(ips, ip, str, localIp):
    return replStr(ips, ip, str, localIp, "IP", ips)

def replStrHn(hostnames, hostname, str, localHn, ips):
    return replStr(hostnames, hostname, str, localHn, "HN", ips)


def replStr(strings, string, str, local_string, baseStr, ips):
    commandRepl=str
    commandRepl=commandRepl.replace("%%%%%s%%%%" % (baseStr), string);
    commandRepl=commandRepl.replace("%%%%%sgen%%%%" % (baseStr), local_string);
    ipAll=""
    for ipAddr in strings:
        ipAll+="%s " %(string)
    ipAll="\"%s\"" %(ipAll[:-1])
    commandRepl=commandRepl.replace("%%%%%sall%%%%" % (baseStr) ,ipAll);
    findallRes = re.findall("%%%%%s[0-9]+%%%%" % (baseStr), commandRepl)
    for res in findallRes:
        searchRes = re.search("[0-9]+", res)
        if searchRes != None:
            try:
                key = int(searchRes.group(0))
                if len(strings) > key:
                    commandRepl=commandRepl.replace(res, strings[key]);
                else:
                    logger.error('Key to high, not enough ips for key %s.' %(key))
                    logger.error(commandRepl)
                    logger.error(baseStr)
                    clean_exit(-1, ips, not args.noshutdown)
            except:
                logger.error("Can't convert key to int: %s." %(key))
                clean_exit(-1, ips, not args.noshutdown)
        else:
            logger.error('Failed to find number in %s.' %(res))
            clean_exit(-1, ips, not args.noshutdown)
    return commandRepl

# Configure ArgumentParser
parser = argparse.ArgumentParser(prog="RunWorkload.py",version=__version__,description="replaces old workload_<dbname>.sh scripts for better multi vm support", formatter_class=argparse.RawDescriptionHelpFormatter, epilog="")
parser.add_argument("-d", "--database",  metavar="DATABASE", required=True, help="Process database DATABASE")
parser.add_argument("-w", "--workload",  metavar="WORKLOAD", required=True, help="Process workload WORKLOAD")
parser.add_argument("-i", "--ip", metavar="IP", required=True, nargs='+', help="connect to IP; Can be more than one.")
parser.add_argument("-s", "--hostname", required=True, metavar="HOSTNAMES", nargs='+', help="Hostnames of the nodes, same order as IPs. Can be more than one.")
parser.add_argument("-g", "--granularity", metavar="GRANULARITY", type=int, default=1000, help="use TS Granularity")
parser.add_argument("-b", "--bucket", metavar="BUCKET", type=int, default=10000, help="set Bucketsize for histogram measurements")
parser.add_argument("-t", "--timeseries", action='store_true', help="do timeseries instead of histogramm")
parser.add_argument("-n", "--noshutdown", action='store_true', help="Don't shutdown vms at cleanup/exit (for debugging only)")
parser.add_argument("-p", "--prerunonly", action='store_true', help="Stop after prerun.")
parser.add_argument("--debug", action='store_false', help="Debug remote commands.")
args = parser.parse_args()

logLevel = logging.WARN
logging.addLevelName(31,"TIMESERIES")
logging.addLevelName(32,"GRANULARITY")
logging.addLevelName(33,"BUCKET")
logging.addLevelName(34,"SPACE")
logging.addLevelName(35,"START")
logging.addLevelName(36,"END")
logging.addLevelName(37,"DESCRIPTION")
logger = logging.getLogger(__name__)
handler = logging.FileHandler("/home/vagrant/ycsb_%s_%s_%s.log" %(args.database.lower(), args.workload.lower(), get_time_file()))
handler.setLevel(logLevel)
formatter = logging.Formatter('%(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

dbConfig=databases.getDict(logger)
if dbConfig == None or dbConfig == {}:
    clean_exit(-1, args.ip, not args.noshutdown)

# this is a dict which holds configs (also dicts) for every special database
# format: key -> dbname
# this results in a dict with the following keys:
# db_folders -> List of DB Folder (for space check)
# db_client -> name of ycsb client
# db_args -> special ycsb arguments for this db
# db_name -> name of this db (e.g. for workload file)
# db_desc -> more detailed name/description
# jvm_args -> special jvm_args for this db and ycsb
# prerun_once -> list of commands to run local once before ycsb (%%IP%% uses first db vm) (without ycsb, sync or space diff or poweroff commands!)
# postrun_once -> list of commands to run local once after ycsb (%%IP%% uses first db vm) (without ycsb, sync or space diff or poweroff commands!)
# prerun -> list of commands to run before ycsb (all vms or local) (without ycsb, sync or space diff or poweroff commands!)
# postrun -> list of commands to run after ycsb (all vms or local) (without ycsb, sync or space diff or poweroff commands!)
# prerun_master -> list of commands to run before ycsb (only on master(first=ID 0) vm or local)) (without ycsb, sync or space diff or poweroff commands!)
# postrun_master -> list of commands to run after ycsb (only on master(first=ID 0) vm or local)) (without ycsb, sync or space diff or poweroff commands!)
# prerun_slaves -> list of commands to run before ycsb (only on slave (all without master(=ID 0)) vms or local)) (without ycsb, sync or space diff or poweroff commands!)
# postrun_slaves -> list of commands to run after ycsb (only on slave (all without master(=ID 0)) vms or local)) (without ycsb, sync or space diff or poweroff commands!)
# prerun_dict -> list of commands to run before ycsb for each db vm (key=number of vm) (without ycsb, sync or space diff or poweroff commands!) (%%SSH%% not needed)
# postrun_dict -> list of commands to run after ycsb for each db vm (key=number of vm) (without ycsb, sync or space diff or poweroff commands!) (%%SSH%% not needed)
# check -> list of commands to run after prerun (all vms or local) for checking if everything runs correctly (systemctl start xyz oftern returns true even if start failed somehow. Check that here!)
# check_master -> list of commands to run after prerun (all vms or local) for checking if everything runs correctly (only on master(first=ID 0) vm or local))
# check_slaves -> list of commands to run after prerun (all vms or local) for checking if everything runs correctly (all without master(=ID 0)) vms or local))
# check_dict -> list of commands to run after prerun for each db vm (key=number of vm) (without ycsb, sync or space diff or poweroff commands!) (%%SSH%% not needed)
# basic -> True/False, if True this is a basic database, so no need to ssh for space checking
# sequence -> which vm should be provisioned first? (for all postrun/prerun dicts/lists. First number is considered master db vm, rest are slaves.)
# include -> which base modules should be imported and added to the dictionary (standard functions that are reusable). Warning: infinite import loop possible!
# the following variables are possible in prerun_once, postrun_once, prerun, prerun_master, prerun_slaves, check, check_master, check_slaves, postrun, postrun_master, postrun_slaves, prerun_dict, postrun_dict, check_dict, db_args:
# %%IP%% -> IP of (actual) db vm
# %%IPgen%% -> IP of (actual) generator vm (on which this script runs)
# %%IPn%% -> IP of db vm number n (e.g. %%IP2%%)
# %%IPall%% -> give String with IP of all vms)
# %%HN%% -> Hostname of (actual) db vm
# %%HNgen%% -> Hostname of (actual) generator vm (on which this script runs)
# %%HNn%% -> Hostname of db vm number n (e.g. %%HN2%%)
# %%HNall%% -> give String with Hostname of all vms)
# %%SSH%% -> if SSH should be used (set at the beginning)
# Order of Preruns/Postruns:
# 1. prerun/postrun/check, 2. prerun_master/postrun_master/check_master, 3. preun_skaves/postrun_slaves/check_slaves, 4.prerun_dict/postrun_dict/check_dict
# General Order:
#  prerun -> check -> ycsb -> postrun

knownKeys=["db_folders","db_client","db_args","db_name","db_desc","jvm_args","prerun_once","postrun_once", "prerun","postrun", "check","prerun_master","postrun_master", "check_master", "prerun_slaves","postrun_slaves", "check_slaves","basic", "prerun_dict", "postrun_dict", "check_dict", "sequence"]

if args.database.lower() in dbConfig.keys():
    localIp = get_local_ip(logger)
    localHn = get_local_hostname(logger)
    if localIp == None:
        logger.error("Can't get local IP, abort.")
        clean_exit(-1,args.ip, not args.noshutdown)
    # Sort ips once and for all
    ips = []
    hostnames = {} # keys = ips
    if len(dbConfig[args.database.lower()]["sequence"]) != len(args.ip):
        logger.error("Sequence list has not the same length as IP list. That can not work!")
        clean_exit(-1,args.ip, not args.noshutdown)
    if len(args.hostname) != len(args.ip):
        logger.error("Hostname list has not the same length as IP list. That can not work!")
        clean_exit(-1, args.ip, not args.noshutdown)
    for ipIdx in dbConfig[args.database.lower()]["sequence"]:
        # do not sort here! this would only sort ips/hostnames alphanumerically. they must be come in sorted and then use the given sequence
        ips.append(args.ip[ipIdx])
        hostnames[args.ip[ipIdx]] = args.hostname[ipIdx]
    if not check_keys(dbConfig[args.database.lower()], knownKeys):
        logger.error("Some keys are missing for %s" %(args.database.lower()))
        clean_exit(-1,ips, not args.noshutdown)
    logger.info("Running prerun commands for %s." %(args.database.lower()))
    # Prerun once
    for command in dbConfig[args.database.lower()]["prerun_once"]:
        commandRepl = command
        commandRepl = replStrIp(args.ip, ips[0], commandRepl, localIp)
        commandRepl = replStrHn(args.hostname, hostnames[ips[0]], commandRepl, localHn, args.ip)
        if "%%SSH%%" in commandRepl:
            commandRepl = commandRepl.replace("%%SSH%%","")
        run_local (commandRepl,logger, False)
    # Prerun for all vms
    for command in dbConfig[args.database.lower()]["prerun"]:
        for ip in ips:
            commandRepl = command
            commandRepl = replStrIp(args.ip, ip, commandRepl, localIp)
            commandRepl = replStrHn(args.hostname, hostnames[ip], commandRepl, localHn, args.ip)
            if "%%SSH%%" in commandRepl:
                commandRepl = commandRepl.replace("%%SSH%%","")
                run_on_vm (ip, "/home/vagrant/.ssh/id_rsa", True, commandRepl,logger,False,args.debug,False,False)
            else:
                run_local (commandRepl,logger, False)
    # Prerun for master (first) vm
    for command in dbConfig[args.database.lower()]["prerun_master"]:
        commandRepl = command
        commandRepl = replStrIp(args.ip, args.ip[0], commandRepl, localIp)
        commandRepl = replStrHn(args.hostname, hostnames[args.ip[0]], commandRepl, localHn, args.ip)
        if "%%SSH%%" in commandRepl:
            commandRepl = commandRepl.replace("%%SSH%%","")
            run_on_vm (args.ip[0], "/home/vagrant/.ssh/id_rsa", True, commandRepl,logger,False,args.debug,False,False)
        else:
            run_local (commandRepl,logger, False)
    # Prerun for slave (all without first) vm
    for command in dbConfig[args.database.lower()]["prerun_slaves"]:
        ipsWithoutMaster=list(ips)
        ipsWithoutMaster.remove(args.ip[0])
        if len(ipsWithoutMaster) > 0:
            for ip in ipsWithoutMaster:
                commandRepl = command
                commandRepl = replStrIp(args.ip, ip, commandRepl, localIp)
                commandRepl = replStrHn(args.hostname, hostnames[ip], commandRepl, localHn, args.ip)
                if "%%SSH%%" in commandRepl:
                    commandRepl = commandRepl.replace("%%SSH%%","")
                    run_on_vm (ip, "/home/vagrant/.ssh/id_rsa", True, commandRepl,logger,False,args.debug,False,False)
                else:
                    run_local (commandRepl,logger, False)
        else:
            logger.warning("There is only one db vm or more sequence keys than vms, can't run slave prerun commands via ssh.")
    # Prerun for dict
    for key in dbConfig[args.database.lower()]["sequence"]:
        if key in dbConfig[args.database.lower()]["prerun_dict"].keys():
            if len(args.ip) > key:
               for command in dbConfig[args.database.lower()]["prerun_dict"][key]:
                    commandRepl = command
                    commandRepl = replStrIp(args.ip, args.ip[key], commandRepl, localIp)
                    commandRepl = replStrHn(args.hostname, hostnames[args.ip[key]], commandRepl, localHn, args.ip)
                    if "%%SSH%%" in commandRepl:
                        commandRepl = commandRepl.replace("%%SSH%%","")
                    run_on_vm (args.ip[key], "/home/vagrant/.ssh/id_rsa", True, commandRepl,logger,False,args.debug,False,False)
            else:
                logger.warning("Key to high, not enough IPs to run prerun command for key: %s." %(key))
    # Check for all vms
    for command in dbConfig[args.database.lower()]["check"]:
        for ip in ips:
            commandRepl = command
            commandRepl = replStrIp(args.ip, ip, commandRepl, localIp)
            commandRepl = replStrHn(args.hostname, hostnames[ip], commandRepl, localHn, args.ip)
            if "%%SSH%%" in commandRepl:
                commandRepl = commandRepl.replace("%%SSH%%","")
                run_on_vm (ip, "/home/vagrant/.ssh/id_rsa", True, commandRepl,logger,False,args.debug,False,False)
            else:
                run_local (commandRepl,logger, False)
    # Check for master (first) vm
    for command in dbConfig[args.database.lower()]["check_master"]:
        commandRepl = command
        commandRepl = replStrIp(args.ip, args.ip[0], commandRepl, localIp)
        commandRepl = replStrHn(args.hostname, hostnames[args.ip[0]], commandRepl, localHn, args.ip)
        if "%%SSH%%" in commandRepl:
            commandRepl = commandRepl.replace("%%SSH%%","")
            run_on_vm (args.ip[0], "/home/vagrant/.ssh/id_rsa", True, commandRepl,logger,False,args.debug,False,False)
        else:
            run_local (commandRepl,logger, False)
    # Check for slave (all without first) vm
    for command in dbConfig[args.database.lower()]["check_slaves"]:
        ipsWithoutMaster=list(ips)
        ipsWithoutMaster.remove(args.ip[0])
        if len(ipsWithoutMaster) > 0:
            for ip in ipsWithoutMaster:
                commandRepl = command
                commandRepl = replStrIp(args.ip, ip, commandRepl, localIp)
                commandRepl = replStrHn(args.hostname, hostnames[ip], commandRepl, localHn, args.ip)
                if "%%SSH%%" in commandRepl:
                    commandRepl = commandRepl.replace("%%SSH%%","")
                    run_on_vm (ip, "/home/vagrant/.ssh/id_rsa", True, commandRepl,logger,False,args.debug,False,False)
                else:
                    run_local (commandRepl,logger, False)
        else:
            logger.warning("There is only one db vm or more sequence keys than vms, can't run slave check commands via ssh.")
    # Check for dict
    for key in dbConfig[args.database.lower()]["sequence"]:
        if key in dbConfig[args.database.lower()]["check_dict"].keys():
            if len(args.ip) > key:
               for command in dbConfig[args.database.lower()]["check_dict"][key]:
                    commandRepl = command
                    commandRepl = replStrIp(args.ip, args.ip[key], commandRepl, localIp)
                    commandRepl = replStrHn(args.hostname, hostnames[args.ip[key]], commandRepl, localHn, args.ip)
                    if "%%SSH%%" in commandRepl:
                        commandRepl = commandRepl.replace("%%SSH%%","")
                    run_on_vm (args.ip[key], "/home/vagrant/.ssh/id_rsa", True, commandRepl,logger,False,args.debug,False,False)
            else:
                logger.warning("Key to high, not enough IPs to run check command for key: %s." %(key))
    if args.prerunonly:
        logger.info("Prerun only, stopping here.")
        clean_exit(0,ips, not args.noshutdown)
    command = "ycsb/bin/ycsb"
    if dbConfig[args.database.lower()]["jvm_args"] != None and dbConfig[args.database.lower()]["jvm_args"] != "":
        command += " %s" %(dbConfig[args.database.lower()]["jvm_args"])
    command += " %s" # for load/run
    command += " %s" %(dbConfig[args.database.lower()]["db_client"])
    command += " -P ycsb/workloads/%s" %(args.workload)
    if len(args.ip) > 0:
        command += " %s" %(replStrIp(args.ip, args.ip[0], dbConfig[args.database.lower()]["db_args"], localIp))
    else:
        command += " %s" %(dbConfig[args.database.lower()]["db_args"])
    if args.timeseries:
        logger.log(31,1)
        command += " -p measurementtype=timeseries"
    else:
        logger.log(31,0)
    logger.log(32,args.granularity)
    logger.log(37,dbConfig[args.database.lower()]["db_desc"])
    command += " -p timeseries.granularity=%s" %(args.granularity)
    logger.log(33,args.bucket)
    command += " -p histogram.buckets=%s" %(args.bucket)
    spaceDict={} # contains every db vm as key, for every key an List of 3 space values (start, between, end)
    logger.log(35,"%s: Start Test" %(get_time_log()))
    get_space(ips,spaceDict,dbConfig[args.database.lower()]["db_folders"],dbConfig[args.database.lower()]["basic"])
    logger.log(35,"%s: Start Load" %(get_time_log()))
    res = run_local(command %("load"),logger,False,True)
    logger.log(35, res.stdout )
    logger.log(35, res.stderr )
    logger.log(36,"%s: End Load" %(get_time_log()))
    local_sync()
    remote_sync(ips)
    get_space(ips,spaceDict,dbConfig[args.database.lower()]["db_folders"],dbConfig[args.database.lower()]["basic"])
    logger.log(35,"%s: Start Run" %(get_time_log()))
    res = run_local(command %("run"),logger,False,True)
    logger.log(35, res.stdout )
    logger.log(35, res.stderr )
    logger.log(36,"%s: End Run" %(get_time_log()))
    remote_sync(ips)
    get_space(ips,spaceDict,dbConfig[args.database.lower()]["db_folders"],dbConfig[args.database.lower()]["basic"])
    logger.log(36,"%s: End Test" %(get_time_log()))
    logger.log(34,"%s" %(make_space_str(check_add_space(spaceDict))))
    logger.info("Running postrun commands for %s." %(args.database.lower()))
     # Postrun once
    for command in dbConfig[args.database.lower()]["postrun_once"]:
        commandRepl = command
        commandRepl = replStrIp(args.ip, ips[0], commandRepl, localIp)
        commandRepl = replStrHn(args.hostname, hostnames[ips[0]], commandRepl, localHn)
        if "%%SSH%%" in commandRepl:
            commandRepl = commandRepl.replace("%%SSH%%","")
        run_local (commandRepl,logger, False)
    # Postrun for all vms
    for command in dbConfig[args.database.lower()]["postrun"]:
        for ip in ips:
            commandRepl = command
            commandRepl = replStrIp(args.ip, ip, commandRepl, localIp)
            commandRepl = replStrHn(args.hostname, hostnames[ip], commandRepl, localHn)
            if "%%SSH%%" in commandRepl:
                commandRepl = commandRepl.replace("%%SSH%%","")
                run_on_vm (ip, "/home/vagrant/.ssh/id_rsa", True, commandRepl,logger,False,args.debug,False,False)
            else:
                run_local (commandRepl,logger, False)
    # Postrun for master (first) vm
    for command in dbConfig[args.database.lower()]["postrun_master"]:
        commandRepl = command
        commandRepl = replStrIp(args.ip, args.ip[0], commandRepl, localIp)
        commandRepl = replStrHn(args.hostname, hostnames[args.ip[0]], commandRepl, localHn)
        if "%%SSH%%" in commandRepl:
            commandRepl = commandRepl.replace("%%SSH%%","")
            run_on_vm (args.ip[0], "/home/vagrant/.ssh/id_rsa", True, commandRepl,logger,False,args.debug,False,False)
        else:
            run_local (commandRepl,logger, False)
    # Postrun for slave (all without first) vm
    for command in dbConfig[args.database.lower()]["postrun_slaves"]:
        ipsWithoutMaster=list(ips)
        ipsWithoutMaster.remove(args.ip[0])
        if len(ipsWithoutMaster) > 0:
            for ip in ipsWithoutMaster:
                commandRepl = command
                commandRepl = replStrIp(args.ip, ip, commandRepl, localIp)
                commandRepl = replStrHn(args.hostname, hostnames[ip], commandRepl, localHn)
                if "%%SSH%%" in commandRepl:
                    commandRepl = commandRepl.replace("%%SSH%%","")
                    run_on_vm (ip, "/home/vagrant/.ssh/id_rsa", True, commandRepl,logger,False,args.debug,False,False)
                else:
                    run_local (commandRepl,logger, False)
        else:
            logger.warning("There is only one db vm or more sequence keys than vms, can't run slave postrun commands via ssh.")
    # Postrun for dict
    for key in dbConfig[args.database.lower()]["sequence"]:
        if key in dbConfig[args.database.lower()]["postrun_dict"].keys():
            if len(args.ip) > key:
               for command in dbConfig[args.database.lower()]["postrun_dict"][key]:
                    commandRepl = command
                    commandRepl = replStrIp(ips, args.ip[key], commandRepl, localIp)
                    commandRepl = replStrHn(args.hostname, hostnames[args.ip[key]], commandRepl, localHn)
                    if "%%SSH%%" in commandRepl:
                        commandRepl = commandRepl.replace("%%SSH%%","")
                    run_on_vm (args.ip[key], "/home/vagrant/.ssh/id_rsa", True, commandRepl,logger,False,args.debug,False,False)
            else:
                logger.warning("Key to high, not enough IPs to run postrun command for key: %s." %(key))
    clean_exit(0,args.ip, not args.noshutdown)
else:
    logger.error("%s is an unknown database." %(args.database))
    clean_exit(-1,args.ip, not args.noshutdown)