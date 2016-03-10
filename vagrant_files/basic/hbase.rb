Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing HBase
  config.vm.provision "shell", privileged: false,  inline: "wget -t 10 -O hbase.tar.gz --retry-connrefused -nv \"#{$links_hbase}\""
  config.vm.provision "shell", privileged: false,  inline: "tar -xvzf hbase.tar.gz"
  config.vm.provision "shell", privileged: false,  inline: "mv /home/vagrant/hbase-* /home/vagrant/hbase"
  config.vm.provision "shell", privileged: false,  inline: "rm hbase.tar.gz"
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|# export JAVA_HOME=/usr/java/jdk1.6.0/|export JAVA_HOME=$(readlink -f /usr/bin/java | sed 's:bin/java::')|g\" /home/vagrant/hbase/conf/hbase-env.sh"
  config.vm.provision "shell", inline: "mkdir /home/vagrant/zookeeper"
end