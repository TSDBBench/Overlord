Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing Cassandra
  config.vm.provision "shell", inline: "echo \"deb http://www.apache.org/dist/cassandra/debian 21x main\" >> /etc/apt/sources.list"
  config.vm.provision "shell", inline: "echo \"deb-src http://www.apache.org/dist/cassandra/debian 21x main\" >> /etc/apt/sources.list"
  config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y update"
  config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y  install cassandra"
  config.vm.provision "shell", inline: "systemctl stop cassandra.service"
  config.vm.provision "shell", inline: "if [ $(ps ax | grep \"cassandra\" | grep -v \"grep\" | wc -l) -ne 0 ]; then for pid in $(ps ax | grep \"cassandra\" | grep -v \"grep\" | grep -Eo \"^[[:blank:]]*[0-9]{1,7}\" | sed \"s:[[:blank:]]::g\"); do kill -9 $pid; done; fi"
  config.vm.provision "shell", inline: "rm -rf /var/lib/cassandra/*"
  # Fix for JAVA Bug when Java is version is over 100
  # see https://issues.apache.org/jira/browse/CASSANDRA-11661
  # should be fixed with  2.1.15 
  config.vm.provision "shell", inline: "sed -i 's|\\[ \"$JVM_PATCH_VERSION\" \\\\< \"25\" \\]|\\[ \"$JVM_PATCH_VERSION\" -lt \"25\" \\]|g' /etc/cassandra/cassandra-env.sh"
end