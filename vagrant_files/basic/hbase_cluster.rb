Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Setup HBase Cloud
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|<configuration>|<configuration>\\n  <property>\\n    <name>hbase.rootdir</name>\\n    <value>hdfs://vm0:54310/hbase</value>\\n  </property>\\n  <property>\\n    <name>hbase.cluster.distributed</name>\\n    <value>true</value>\\n  </property>\\n  <property>\\n    <name>hbase.zookeeper.quorum</name>\\n    <value>vm0,vm1,vm2,vm3,vm4</value>\\n  </property>\\n  <property>\\n    <name>hbase.zookeeper.property.dataDir</name>\\n    <value>/home/vagrant/zookeeper</value>\\n  </property>|g\" /home/vagrant/hbase/conf/hbase-site.xml"
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|localhost|vm1\\nvm2\\nvm3\\nvm4|\" /home/vagrant/hbase/conf/regionservers"
  config.vm.provision "shell", privileged: false,  inline: "echo -e \"vm1\\nvm2\" >> /home/vagrant/hbase/conf/backup-masters"
end