#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Andreas Bader'
__version__ = "0.01"

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
# the following variables are possible in prerun_once, postrun_once, prerun, prerun_master, prerun_slaves, check, check_master, check_slaves, postrun, postrun_master, postrun_slaves, prerun_dict, postrun_dict, check_dict, db_args:
# %%IP%% -> IP of (actual) db vm
# %%IPgen%% -> IP of (actual) generator vm (on which this script runs)
# %%IPn%% -> IP of db vm number n (e.g. %%IP2%%)
# %%IPall%% -> give String with IP of all vms)
# %%SSH%% -> if SSH should be used (set at the beginning)
# Order of Preruns/Postruns:
# 1. prerun/postrun/check, 2. prerun_master/postrun_master/check_master, 3. preun_skaves/postrun_slaves/check_slaves, 4.prerun_dict/postrun_dict/check_dict
# General Order:
#  prerun -> check -> ycsb -> postrun

def getDict():
    dbConfig={}
    dbConfig["db_folders"]=["/tmp/druid/indexCache", "/tmp/persistent/zk_druid", "/tmp/persistent/task/", "/tmp/druid/localStorage", "/var/lib/mysql"]
    dbConfig["db_client"]="druid"
    dbConfig["db_args"]="-p zookeeperip=%%IP%% -p queryip=%%IP%% -p zookeeperport=2181 -p queryport=8090 -p replicants=1"
    dbConfig["db_name"]="druid1"
    dbConfig["db_desc"]="Druid (Broker,Coordinator,Historical,MiddleManager,Overlord) on 1 VM. Ingest via Tranquility/Finagle, Query via REST."
    dbConfig["jvm_args"]="-jvm-args='-Xmx4096m'"
    dbConfig["prerun_once"]= []
    dbConfig["postrun_once"]= []
    dbConfig["prerun"]= ["%%SSH%%sudo -s bash -c 'sed -i \"s|localhost|%%IP%%|g\" /home/vagrant/config/broker/runtime.properties'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|localhost|%%IP%%|g\" /home/vagrant/config/coordinator/runtime.properties'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|localhost|%%IP%%|g\" /home/vagrant/config/historical/runtime.properties'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|localhost|%%IP%%|g\" /home/vagrant/config/middleManager/runtime.properties'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|localhost|%%IP%%|g\" /home/vagrant/config/overlord/runtime.properties'"]
    dbConfig["postrun"]= []
    dbConfig["prerun_master"]= ["%%SSH%%sudo -s bash -c 'systemctl start druid.service'", "bash -c 'sleep 180'"]
    dbConfig["postrun_master"]= []
    dbConfig["prerun_slaves"]= []
    dbConfig["postrun_slaves"]= []
    dbConfig["prerun_dict"]= {}
    dbConfig["postrun_dict"]= {}
    dbConfig["check"]= []
    dbConfig["check_master"]= ["%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid.service | grep -c \"active (exited)\")-1))'",
                        "%%SSH%%sudo -s bash -c 'exit $(systemctl status druid_broker.service | grep -c \"active (exited)\")'",
                        "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_broker.service | grep -c \"active (running)\")-1))'",
                        "%%SSH%%sudo -s bash -c 'exit $(systemctl status druid_coordinator.service | grep -c \"active (exited)\")'",
                        "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_coordinator.service | grep -c \"active (running)\")-1))'",
                        "%%SSH%%sudo -s bash -c 'exit $(systemctl status druid_historical.service | grep -c \"active (exited)\")'",
                        "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_historical.service | grep -c \"active (running)\")-1))'",
                        "%%SSH%%sudo -s bash -c 'exit $(systemctl status druid_middlemanager.service | grep -c \"active (exited)\")'",
                        "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_middlemanager.service | grep -c \"active (running)\")-1))'",
                        "%%SSH%%sudo -s bash -c 'exit $(systemctl status druid_overlord.service | grep -c \"active (exited)\")'",
                        "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_overlord.service | grep -c \"active (running)\")-1))'"]
    dbConfig["check_slaves"]= []
    dbConfig["check_dict"]= {}
    dbConfig["basic"]= False
    dbConfig["sequence"]=[0]
    return dbConfig