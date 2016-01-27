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
    dbConfig["db_folders"]=["/var/opt/influxdb"] # because /var/opt/influxdb/data does not exist at start (was: ["/var/opt/influxdb/data", "/var/opt/influxdb/wal"])
    dbConfig["db_client"]="influxdb"
    dbConfig["db_args"]="-p ip=%%IP%% -p port=8086"
    dbConfig["db_name"]="influxdb2"
    dbConfig["db_desc"]="InfluxDB on 5 VMs with Replication Factor 5."
    dbConfig["jvm_args"]="-jvm-args='-Xmx4096m'"
    dbConfig["prerun_once"]= []
    dbConfig["postrun_once"]= []
    dbConfig["prerun"]= ["%%SSH%%sudo -s bash -c 'echo -e \"%%IP0%% vm0\" >> /etc/hosts'",
        "%%SSH%%sudo -s bash -c 'echo -e \"%%IP1%% vm1\" >> /etc/hosts'",
        "%%SSH%%sudo -s bash -c 'echo -e \"%%IP2%% vm2\" >> /etc/hosts'",
        "%%SSH%%sudo -s bash -c 'echo -e \"%%IP3%% vm3\" >> /etc/hosts'",
        "%%SSH%%sudo -s bash -c 'echo -e \"%%IP4%% vm4\" >> /etc/hosts'",
        "%%SSH%%sudo -s bash -c 'systemctl start influxdb.service; sleep 5'"] # the sleep makes sure that 0,1,2 are raft, 3,4 are data vms
    dbConfig["postrun"]= []
    dbConfig["prerun_master"]= []
    dbConfig["postrun_master"]= []
    dbConfig["prerun_slaves"]= []
    dbConfig["postrun_slaves"]= []
    dbConfig["prerun_dict"]= {
        0 : [
            "%%SSH%%sudo -s bash -c 'exit $(curl -G http://localhost:8086/query --data-urlencode \"q=CREATE DATABASE testdb\" 2>&1 | grep -c \"error\")'",
            "%%SSH%%sudo -s bash -c 'exit $(curl -G http://localhost:8086/query --data-urlencode \"q=ALTER RETENTION POLICY default ON testdb DURATION INF REPLICATION 5\" 2>&1 | grep -c \"error\")'",
            ]
    }
    dbConfig["postrun_dict"]= {}
    # Checking that influxdb service runs, not exited and SHOW SERVERS show 3 raft servers + 2 non-raft servers
    # For versions > 0.9.4 there is a new coloumn raft-leader for "SHOW SERVERS"
    dbConfig["check"]= ["%%SSH%%sudo -s bash -c 'exit $(systemctl status influxdb.service | grep -c \"active (exited)\")'",
                        "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status influxdb.service | grep -c \"active (running)\")-1))'",
                        # "%%SSH%%sudo -s bash -c 'exit $(($(/opt/influxdb/influx -execute \"SHOW SERVERS\"| grep -c \"true\")-"+
                        # "$(/opt/influxdb/influx -execute \"SHOW SERVERS\"| grep -c \"false\")-1))'"]
                        "%%SSH%%sudo -s bash -c 'exit $(($(/opt/influxdb/influx -execute \"SHOW SERVERS\"| grep -c \"true\")-"+
                        "$(/opt/influxdb/influx -execute \"SHOW SERVERS\"| grep -v \"true\" | grep -c \"false\")-1))'"]
    dbConfig["check_master"]= []
    dbConfig["check_slaves"]= []
    dbConfig["check_dict"]= {}
    dbConfig["basic"]= False
    dbConfig["sequence"]=[0,1,2,3,4]
    return dbConfig