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
    dbConfig["db_folders"]=["/home/vagrant/hadoop"]
    dbConfig["db_client"]="opentsdb"
    dbConfig["db_args"]="-p ip=%%IP%% -p port=4242"
    dbConfig["db_name"]="opentsdb_cl5_rf1"
    dbConfig["db_desc"]="OpenTSDB with HBase and Hadoop on 5 VMs and Replication Factor 1."
    dbConfig["jvm_args"]="-jvm-args='-Xmx4096m'"
    dbConfig["prerun_once"]= []
    dbConfig["postrun_once"]= []
    dbConfig["prerun"]= [ "%%SSH%%sudo -s bash -c 'echo -e \"%%IP0%% vm0\" >> /etc/hosts'",
        "%%SSH%%sudo -s bash -c 'echo -e \"%%IP1%% vm1\" >> /etc/hosts'",
        "%%SSH%%sudo -s bash -c 'echo -e \"%%IP2%% vm2\" >> /etc/hosts'",
        "%%SSH%%sudo -s bash -c 'echo -e \"%%IP3%% vm3\" >> /etc/hosts'",
        "%%SSH%%sudo -s bash -c 'echo -e \"%%IP4%% vm4\" >> /etc/hosts'"]
        # "%%SSH%%sudo -s bash -c 'echo -e \"%%IP0%% $(dig -x %%IP0%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )\" >> /etc/hosts'",
        # "%%SSH%%sudo -s bash -c 'echo -e \"%%IP1%% $(dig -x %%IP1%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )\" >> /etc/hosts'",
        # "%%SSH%%sudo -s bash -c 'echo -e \"%%IP2%% $(dig -x %%IP2%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )\" >> /etc/hosts'",
        # "%%SSH%%sudo -s bash -c 'echo -e \"%%IP3%% $(dig -x %%IP3%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )\" >> /etc/hosts'",
        # "%%SSH%%sudo -s bash -c 'echo -e \"%%IP4%% $(dig -x %%IP4%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )\" >> /etc/hosts'",
        # "%%SSH%%sudo -s bash -c 'sed -i \"s/master0/$(dig -x %%IP0%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )/g\" /home/vagrant/hadoop-2.7.1/etc/hadoop/slaves'",
        # "%%SSH%%sudo -s bash -c 'sed -i \"s/slave0/$(dig -x %%IP1%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )/g\" /home/vagrant/hadoop-2.7.1/etc/hadoop/slaves'",
        # "%%SSH%%sudo -s bash -c 'sed -i \"s/slave1/$(dig -x %%IP2%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )/g\" /home/vagrant/hadoop-2.7.1/etc/hadoop/slaves'",
        # "%%SSH%%sudo -s bash -c 'sed -i \"s/slave2/$(dig -x %%IP3%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )/g\" /home/vagrant/hadoop-2.7.1/etc/hadoop/slaves'",
        # "%%SSH%%sudo -s bash -c 'sed -i \"s/slave3/$(dig -x %%IP4%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )/g\" /home/vagrant/hadoop-2.7.1/etc/hadoop/slaves'",
        #"%%SSH%%sudo -s bash -c 'sed -i \"s/master0/$(dig -x %%IP0%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )/g\" /home/vagrant/hadoop-2.7.1/etc/hadoop/core-site.xml'",
        #"%%SSH%%sudo -s bash -c 'sed -i \"s/master0/$(dig -x %%IP0%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )/g\" /home/vagrant/hadoop-2.7.1/etc/hadoop/yarn-site.xml'"]
        # ]
    dbConfig["postrun"]= []
    dbConfig["prerun_master"]= []#"%%SSH%%sudo -s bash -c 'echo \"$(dig -x %%IP0%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )\" >> /home/vagrant/hadoop-2.7.1/etc/hadoop/slaves'",
        # "%%SSH%%sudo -s bash -c 'echo \"$(dig -x %%IP1%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )\" >> /home/vagrant/hadoop-2.7.1/etc/hadoop/slaves'",
        # "%%SSH%%sudo -s bash -c 'echo \"$(dig -x %%IP2%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )\" >> /home/vagrant/hadoop-2.7.1/etc/hadoop/slaves'",
        # "%%SSH%%sudo -s bash -c 'echo \"$(dig -x %%IP3%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )\" >> /home/vagrant/hadoop-2.7.1/etc/hadoop/slaves'",
        # "%%SSH%%sudo -s bash -c 'echo \"$(dig -x %%IP4%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )\" >> /home/vagrant/hadoop-2.7.1/etc/hadoop/slaves'",
        # "%%SSH%%sudo -s bash -c 'echo \"$(dig -x %%IP0%% | grep -A1 \"ANSWER SECTION\" | tail -n1 | awk \"{print $ 5}\" | sed \"s/\.$//g\" )\" >> /home/vagrant/hadoop-2.7.1/etc/hadoop/masters'",
        # "%%SSH%%sudo -s bash -c '/home/vagrant/hadoop-2.7.1/bin/hdfs namenode -format test'"]
        #"%%SSH%%sudo -s bash /home/vagrant/hadoop-2.7.1/sbin/start-dfs.sh",
        #"%%SSH%%sudo -s bash /home/vagrant/hadoop-2.7.1/sbin/start-yarn.sh"]
    dbConfig["postrun_master"]= []
    dbConfig["prerun_slaves"]= []
    dbConfig["postrun_slaves"]= []
    dbConfig["prerun_dict"]= {
        0 : ["%%SSH%%sudo -s bash -c '/home/vagrant/hadoop-2.7.1/bin/hdfs namenode -format test'",
             "%%SSH%%sudo -s bash /home/vagrant/hadoop-2.7.1/sbin/start-dfs.sh",
             #"%%SSH%%sudo -s bash /home/vagrant/hadoop-2.7.1/sbin/start-yarn.sh"
             "%%SSH%%sudo -s bash /home/vagrant/hbase/bin/start-hbase.sh",
             "%%SSH%%sudo -s bash -c 'sleep 10'",
             "%%SSH%%sudo -s bash -c \"COMPRESSION=LZO HBASE_HOME=/home/vagrant/hbase /usr/share/opentsdb/tools/create_table.sh\"",
             "%%SSH%%sudo -s bash -c 'systemctl start opentsdb.service'",
             "%%SSH%%sudo -s bash -c '/usr/share/opentsdb/bin/tsdb mkmetric usermetric'"
             ],
    }
    dbConfig["postrun_dict"]= {}
    dbConfig["check"]= []
    dbConfig["check_master"]= ["%%SSH%%sudo -s bash -c 'exit $(systemctl status opentsdb.service | grep -c \"active (exited)\")'",
                               "%%SSH%%sudo -s bash -c 'exit $(($(systemctl status opentsdb.service | grep -c \"active (running)\")-1))'",
                               "%%SSH%%sudo -s bash -c 'exit $(($(ps ax | grep \"hbase\" | grep -v \"grep hbase\" | wc -l)-5))'",
                               "%%SSH%%sudo -s bash -c 'exit $(($(ps ax | grep \"hadoop\" | grep -v \"grep hadoop\" | wc -l)-5))'"]
    dbConfig["check_slaves"]= []
    dbConfig["check_dict"]= {
        1 : ["%%SSH%%sudo -s bash -c 'exit $(($(ps ax | grep \"hbase\" | grep -v \"grep hbase\" | wc -l)-6))'",
             "%%SSH%%sudo -s bash -c 'exit $(($(ps ax | grep \"hadoop\" | grep -v \"grep hadoop\" | wc -l)-4))'"],
        2 : ["%%SSH%%sudo -s bash -c 'exit $(($(ps ax | grep \"hbase\" | grep -v \"grep hbase\" | wc -l)-6))'",
             "%%SSH%%sudo -s bash -c 'exit $(($(ps ax | grep \"hadoop\" | grep -v \"grep hadoop\" | wc -l)-4))'"],
        3 : ["%%SSH%%sudo -s bash -c 'exit $(($(ps ax | grep \"hbase\" | grep -v \"grep hbase\" | wc -l)-4))'",
             "%%SSH%%sudo -s bash -c 'exit $(($(ps ax | grep \"hadoop\" | grep -v \"grep hadoop\" | wc -l)-3))'"],
        4 : ["%%SSH%%sudo -s bash -c 'exit $(($(ps ax | grep \"hbase\" | grep -v \"grep hbase\" | wc -l)-4))'",
             "%%SSH%%sudo -s bash -c 'exit $(($(ps ax | grep \"hadoop\" | grep -v \"grep hadoop\" | wc -l)-3))'"],
    }
    dbConfig["basic"]= False
    dbConfig["sequence"]=[1,2,3,4,0]
    return dbConfig