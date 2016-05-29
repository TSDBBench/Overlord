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

# Does not work with 5 VMs, needs more historical nodes for replication 5 times?
# replication is not expected to bring performance bonus: https://groups.google.com/forum/#!topic/druid-development/0TBL5-3Z2PI

def getDict():
    dbConfig={}
    dbConfig["db_folders"]=["/tmp/druid/indexCache", "/tmp/persistent/zk_druid", "/tmp/persistent/task/", "/tmp/druid/localStorage", "/var/lib/mysql"]
    dbConfig["db_client"]="druid"
    dbConfig["db_args"]="-p zookeeperip=%%IP0%% -p queryip=%%IP1%% -p zookeeperport=2181 -p queryport=8090 -p replicants=2"
    dbConfig["db_name"]="druid_cl5_rf2"
    dbConfig["db_desc"]="Druid (Broker,Coordinator,Historical,MiddleManager,Overlord) on 5 VMs with Replication Factor 2. Ingest via Tranquility/Finagle, Query via REST."
    dbConfig["jvm_args"]="-jvm-args='-Xmx4096m'"
    dbConfig["prerun_once"]= []
    dbConfig["postrun_once"]= []
    dbConfig["prerun"]= ["%%SSH%%sudo -s bash -c 'sed -i \"s|localhost|%%IP0%%|g\" /home/vagrant/config/_common/common.runtime.properties'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|localhost|%%IP1%%|g\" /home/vagrant/config/broker/runtime.properties'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|localhost|%%IP0%%|g\" /home/vagrant/config/coordinator/runtime.properties'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|localhost|%%IP2%%|g\" /home/vagrant/config/historical/runtime.properties'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|localhost|%%IP3%%|g\" /home/vagrant/config/middleManager/runtime.properties'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|localhost|%%IP4%%|g\" /home/vagrant/config/overlord/runtime.properties'"]
    dbConfig["postrun"]= []
    dbConfig["prerun_master"]= []
    dbConfig["postrun_master"]= []
    dbConfig["prerun_slaves"]= []
    dbConfig["postrun_slaves"]= []
    dbConfig["prerun_dict"]= {
        0 : ["%%SSH%%sudo -s bash -c 'systemctl start druid_coordinator.service'"],
        1 : ["%%SSH%%sudo -s bash -c 'systemctl start druid_broker.service'"],
        2 : ["%%SSH%%sudo -s bash -c 'systemctl start druid_historical.service'"],
        3 : ["%%SSH%%sudo -s bash -c 'systemctl start druid_middlemanager.service'"],
        4 : ["%%SSH%%sudo -s bash -c 'systemctl start druid_overlord.service'",
             "bash -c 'sleep 180'"]
    }
    dbConfig["postrun_dict"]= {}
    dbConfig["check"]= []
    dbConfig["check_master"]= []
    dbConfig["check_slaves"]= []
    dbConfig["check_dict"]= {
        0 : ["%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_repo.service | grep -c \"inactive (dead)\")-1))'",
             "%%SSH%%sudo -s bash -c 'exit $(systemctl status druid_coordinator.service | grep -c \"active (exited)\")'",
             "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_coordinator.service | grep -c \"active (running)\")-1))'"],
        1 : ["%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_repo.service | grep -c \"inactive (dead)\")-1))'",
             "%%SSH%%sudo -s bash -c 'exit $(systemctl status druid_broker.service | grep -c \"active (exited)\")'",
             "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_broker.service | grep -c \"active (running)\")-1))'"],
        2 : ["%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_repo.service | grep -c \"inactive (dead)\")-1))'",
             "%%SSH%%sudo -s bash -c 'exit $(systemctl status druid_historical.service | grep -c \"active (exited)\")'",
             "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_historical.service | grep -c \"active (running)\")-1))'"],
        3 : ["%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_repo.service | grep -c \"inactive (dead)\")-1))'",
             "%%SSH%%sudo -s bash -c 'exit $(systemctl status druid_middlemanager.service | grep -c \"active (exited)\")'",
             "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_middlemanager.service | grep -c \"active (running)\")-1))'"],
        4 : ["%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_repo.service | grep -c \"inactive (dead)\")-1))'",
             "%%SSH%%sudo -s bash -c 'exit $(systemctl status druid_overlord.service | grep -c \"active (exited)\")'",
             "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status druid_overlord.service | grep -c \"active (running)\")-1))'"]
    }
    dbConfig["basic"]= False
    dbConfig["sequence"]=[0,1,2,3,4]
    dbConfig["include"] = []
    return dbConfig