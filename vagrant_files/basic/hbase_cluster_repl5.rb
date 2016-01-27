Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Setup Replication = 5
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|<configuration>|<configuration>\\n  <property>\\n    <name>dfs.replication</name>\\n    <value>5</value>\\n  </property>|g\" /home/vagrant/hbase-1.1.2/conf/hbase-site.xml"
end