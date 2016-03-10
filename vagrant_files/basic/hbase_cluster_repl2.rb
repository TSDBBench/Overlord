Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Setup Replication = 2
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|<configuration>|<configuration>\\n  <property>\\n    <name>dfs.replication</name>\\n    <value>2</value>\\n  </property>|g\" /home/vagrant/hbase/conf/hbase-site.xml"
end