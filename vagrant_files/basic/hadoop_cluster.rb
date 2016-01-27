Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Setting up Hadoop Cloud
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|JAVA_HOME=\\${JAVA_HOME}|JAVA_HOME=$(readlink -f /usr/bin/java | sed 's:bin/java::')|g\" /home/vagrant/hadoop-2.7.1/etc/hadoop/hadoop-env.sh"
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|<configuration>|<configuration>\\n    <property>\\n        <name>fs.defaultFS</name>\\n        <value>hdfs://vm0:54310</value>\\n    </property>\\n    <property>\\n        <name>hadoop.tmp.dir</name>\\n        <value>/home/vagrant/hadoop</value>\\n    </property>|g\" /home/vagrant/hadoop-2.7.1/etc/hadoop/core-site.xml"
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|<configuration>|<configuration>\\n    <property>\\n        <name>dfs.replication</name>\\n        <value>5</value>\\n    </property>|g\" /home/vagrant/hadoop-2.7.1/etc/hadoop/hdfs-site.xml"
end