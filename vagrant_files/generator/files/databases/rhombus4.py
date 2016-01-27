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
    dbConfig["db_folders"]=["/var/lib/cassandra"]
    dbConfig["db_client"]="rhombus"
    dbConfig["db_args"]="-p ip=\"%%IP0%%,%%IP1%%,%%IP2%%,%%IP3%%,%%IP4%%\" -p keySpacedefinitionfile=\"/home/vagrant/files/rhombus_repl2.json\""
    dbConfig["db_name"]="rhombus4"
    dbConfig["db_desc"]="Rhombus with Cassandra on 5 VMs with Replication Factor 2."
    dbConfig["jvm_args"]="-jvm-args='-Xmx4096m'"
    dbConfig["prerun_once"]= []
    dbConfig["postrun_once"]= []
    dbConfig["prerun"]= ["%%SSH%%sudo -s bash -c 'sed -i \"s|- seeds: \\\\\"127.0.0.1\\\\\"|- seeds: \\\\\"%%IP0%%,%%IP1%%,%%IP2%%,%%IP3%%,%%IP4%%\\\\\"|g\" /etc/cassandra/cassandra.yaml'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|listen_address: localhost|listen_address: %%IP%%|g\" /etc/cassandra/cassandra.yaml'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|rpc_address: localhost|rpc_address: %%IP%%|g\" /etc/cassandra/cassandra.yaml'"]
    dbConfig["postrun"]= []
    dbConfig["prerun_master"]= ["%%SSH%%sudo -s bash -c 'systemctl start cassandra.service'",
                                "%%SSH%%sudo -s bash -c 'sleep 60'"]
    dbConfig["postrun_master"]= []
    # Sleep is needed for slaves, otherwise all slaves would connect at the same time which
    # leads to an error. systemctl start for cassandra is non-blocking, delay is added by hand
    dbConfig["prerun_slaves"]= ["%%SSH%%sudo -s bash -c 'systemctl start cassandra.service && sleep 60'"]
    dbConfig["postrun_slaves"]= []
    dbConfig["prerun_dict"]= {}
    dbConfig["postrun_dict"]= {}
    # check if cassandra runs but has not exited (active+exited = error/not running anymore)
    dbConfig["check"]= ["%%SSH%%sudo -s bash -c 'exit $(systemctl status cassandra.service | grep -c \"active (exited)\")'",
                        "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status cassandra.service | grep -c \"active (running)\")-1))'"]
   # check the same for newts but only on master
    dbConfig["check_master"]= ["%%SSH%%sudo -s bash -c 'exit $(($(nodetool status | grep -c \"UN\")-5))'"]
    dbConfig["check_slaves"]= []
    dbConfig["check_dict"]= {}
    dbConfig["basic"]= False
    dbConfig["sequence"]=[0,1,2,3,4]
    return dbConfig