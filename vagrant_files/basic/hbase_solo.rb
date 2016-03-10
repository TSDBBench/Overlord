Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Setup HBase Solo
   config.vm.provision "shell", privileged: false,  inline:  "sed -i \"s|<configuration>|<configuration>\\n  <property>\\n    <name>hbase.rootdir</name>\\n    <value>file:///home/vagrant/hbase</value>\\n  </property>\\n  <property>\\n    <name>hbase.zookeeper.property.dataDir</name>\\n    <value>/home/vagrant/zookeeper</value>\\n  </property>|g\" /home/vagrant/hbase/conf/hbase-site.xml"
end