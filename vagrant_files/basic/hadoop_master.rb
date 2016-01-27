Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
#  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|<configuration>|<configuration>\\n    <property>\\n        <name>yarn.resourcemanager.resource-tracker.address</name>\\n        <value>vm0:8025</value>\\n    </property>\\n    <property>\\n        <name>yarn.resourcemanager.scheduler.address</name>\\n        <value>vm0:8030</value>\\n    </property>\\n    <property>\\n        <name>yarn.resourcemanager.address</name>\\n        <value>vm0:8050</value>\\n    </property>|g\" /home/vagrant/hadoop-2.7.1/etc/hadoop/yarn-site.xml"
  config.vm.provision "shell", privileged: false,  inline: "echo -e 'vm0\\nvm1\\nvm2\\nvm3\\nvm4' >> /home/vagrant/hadoop-2.7.1/etc/hadoop/slaves"
  config.vm.provision "shell", privileged: false,  inline: "echo -e 'vm0' >> /home/vagrant/hadoop-2.7.1/etc/hadoop/masters"

end