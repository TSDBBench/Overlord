#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Andreas Bader'
__version__ = "0.01"

# db_folders -> List of DB Folder (for space check)
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

# this configures a influxdb cluster
# only node 0,1,2 are members of raft (at least three raft nodes, amount of raft nodes must not be even)

def getDict():
    baseConfig={}
    baseConfig["db_folders"]=[]
    baseConfig["prerun_once"]= []
    baseConfig["postrun_once"]= []
    baseConfig["prerun"] = [
        "%%SSH%%sudo -s bash -c 'echo \"INFLUXD_OPTS=\\\\\"-join %%HN0%%:8091,%%HN1%%:8091,%%HN2%%:8091\\\\\"\" >>/etc/default/influxdb'",
        "%%SSH%%sudo -s bash -c 'sed -i \"s|#\\\\s\\\\+hostname = \\\\\"localhost\\\\\"|hostname = \\\\\"%%HN%%\\\\\"|\" /etc/influxdb/influxdb.conf'",

    ]
    baseConfig["postrun"]= []
    baseConfig["prerun_master"]= []
    baseConfig["postrun_master"]= []
    baseConfig["prerun_slaves"]= []
    baseConfig["postrun_slaves"]= []
    baseConfig["prerun_dict"]= {
        0: [
            "%%SSH%%sudo -s bash -c 'systemctl start influxdb.service; sleep 5'", # the sleep makes sure that 0,1,2 are raft, 3,4 are data vms
        ],
        1: [
            "%%SSH%%sudo -s bash -c 'systemctl start influxdb.service; sleep 5'" # the sleep makes sure that 0,1,2 are raft, 3,4 are data vms
        ],
        2: [
            "%%SSH%%sudo -s bash -c 'systemctl start influxdb.service; sleep 5'" # the sleep makes sure that 0,1,2 are raft, 3,4 are data vms
        ],
        3: [
            "%%SSH%%sudo -s bash -c 'sed -i \"0,/enabled\\\\s\\\\+=\\\\s\\\\+true/{s/enabled\\\\s\\\\+=\\\\s\\\\+true/enabled = false/}\" /etc/influxdb/influxdb.conf'",
            "%%SSH%%sudo -s bash -c 'systemctl start influxdb.service; sleep 5'" # the sleep makes sure that 0,1,2 are raft, 3,4 are data vms
        ],
        4: [
            "%%SSH%%sudo -s bash -c 'sed -i \"0,/enabled\\\\s\\\\+=\\\\s\\\\+true/{s/enabled\\\\s\\\\+=\\\\s\\\\+true/enabled = false/}\" /etc/influxdb/influxdb.conf'",
            "%%SSH%%sudo -s bash -c 'systemctl start influxdb.service; sleep 5'", # the sleep makes sure that 0,1,2 are raft, 3,4 are data vms
            "%%SSH%%sudo -s bash -c 'exit $(curl -G http://%%HN0%%:8086/query --data-urlencode \"q=CREATE DATABASE testdb\" 2>&1 | grep -c -i -E \"error|failed\")'" # must be done here, because otherwise the cluster is not started (is started after three rafts nodes are ready)
        ],
    }
    baseConfig["postrun_dict"]= {}
    # Checking that influxdb service runs, not exited and SHOW SERVERS show 3 raft servers + 2 non-raft servers
    baseConfig["check"]= [
        "%%SSH%%sudo -s bash -c 'exit $(systemctl status influxdb.service | grep -c \"active (exited)\")'",
        "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status influxdb.service | grep -c \"active (running)\")-1))'",
        "%%SSH%%sudo -s bash -c 'exit $(($(/usr/bin/influx -execute \"SHOW SERVERS\"| grep -c -E \"vm\S+:[0-9]+\")-8))'"
    ]
    baseConfig["check_master"]= []
    baseConfig["check_slaves"]= []
    baseConfig["check_dict"]= {}
    baseConfig["include"] = []
    return baseConfig