#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Rene Trefft, Dirk Braunschweiger'
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
    dbConfig["db_client"]="databus"
    dbConfig["db_args"]="-p port=8080 -p ip=%%IP%% -p user=admin -p apiKey=adminregkey -p tableType=tstable"
    dbConfig["db_name"]="databus_tstable_cl1_rf1"
    dbConfig["db_desc"]="Databus with Cassandra together on 1 VM."
    dbConfig["jvm_args"]="-jvm-args='-Xmx4096m'"
    dbConfig["prerun_once"]= []
    dbConfig["postrun_once"]= []
    dbConfig["prerun"]= ["%%SSH%%sudo -s bash -c 'sed -i \"s|- seeds: \\\\\"127.0.0.1\\\\\"|- seeds: \\\\\"%%IP0%%\\\\\"|g\" /etc/cassandra/cassandra.yaml'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|listen_address: localhost|listen_address: %%IP%%|g\" /etc/cassandra/cassandra.yaml'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|rpc_address: localhost|rpc_address: %%IP%%|g\" /etc/cassandra/cassandra.yaml'",
						 "%%SSH%%sudo -s bash -c 'sed -i \"s|cluster_name:|#cluster_name:|g\" /etc/cassandra/cassandra.yaml'",
						 "%%SSH%%sudo -s bash -c 'echo \"cluster_name: DatabusCluster\" >> /etc/cassandra/cassandra.yaml'",
                         "%%SSH%%sudo -s bash -c 'cd /home/vagrant/files/databus-1.1.0-3661/webapp ; cp conf/application.conf.prod conf/application.conf'",
                         "%%SSH%%sudo -s bash -c 'sed -i \"s|domain=|#domain=|g\" /home/vagrant/files/databus-1.1.0-3661/webapp/conf/application.conf'",
						 "%%SSH%%sudo -s bash -c 'echo \"domain=none\" >> /home/vagrant/files/databus-1.1.0-3661/webapp/conf/application.conf'",
						 "%%SSH%%sudo -s bash -c 'sed -i \"s|nosql.cassandra.seeds=|#nosql.cassandra.seeds=|g\" /home/vagrant/files/databus-1.1.0-3661/webapp/conf/application.conf'",
						 "%%SSH%%sudo -s bash -c 'echo \"nosql.cassandra.seeds=%%IP%%:9160\"  >> /home/vagrant/files/databus-1.1.0-3661/webapp/conf/application.conf'",
						 "%%SSH%%sudo -s bash -c 'sed -i \"s|nosql.cassandra.clusterName=|#nosql.cassandra.clusterName=|g\" /home/vagrant/files/databus-1.1.0-3661/webapp/conf/application.conf'",
						 "%%SSH%%sudo -s bash -c 'echo \"nosql.cassandra.clusterName=DatabusCluster\" >> /home/vagrant/files/databus-1.1.0-3661/webapp/conf/application.conf'"
						 ]	 
    dbConfig["postrun"]= []
    dbConfig["prerun_master"]= ["%%SSH%%sudo -s bash -c 'systemctl start cassandra.service'",
                                "%%SSH%%sudo -s bash -c 'sleep 60'",
                                "%%SSH%%sudo -s bash -c 'cd /home/vagrant/files/databus-1.1.0-3661/webapp ; nohup ./play1.3.x/play start'",
                                "%%SSH%%sudo -s bash -c 'sleep 60'"]
    dbConfig["postrun_master"]= []
    dbConfig["prerun_slaves"]= []
    dbConfig["postrun_slaves"]= []
    dbConfig["prerun_dict"]= {}
    dbConfig["postrun_dict"]= {}
    dbConfig["check"]= []
    dbConfig["check_master"]= ["%%SSH%%sudo -s bash -c 'exit $(systemctl status cassandra.service | grep -c \"active (exited)\")'",
                        "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status cassandra.service | grep -c \"active (running)\")-1))'"]
    dbConfig["check_slaves"]= []
    dbConfig["check_dict"]= {}
    dbConfig["basic"]= False
    dbConfig["sequence"]=[0]
    return dbConfig
