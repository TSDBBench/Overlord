Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing HBase
  config.vm.provision "shell", privileged: false,  inline: "wget -t 10 --retry-connrefused -nv \"http://ftp-stud.hs-esslingen.de/pub/Mirrors/ftp.apache.org/dist/hbase/1.1.2/hbase-1.1.2-bin.tar.gz\""
  config.vm.provision "shell", privileged: false,  inline: "tar -xvzf hbase-1.1.2-bin.tar.gz"
  config.vm.provision "shell", privileged: false,  inline: "rm hbase-1.1.2-bin.tar.gz"
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|# export JAVA_HOME=/usr/java/jdk1.6.0/|export JAVA_HOME=$(readlink -f /usr/bin/java | sed 's:bin/java::')|g\" /home/vagrant/hbase-1.1.2/conf/hbase-env.sh"
  config.vm.provision "shell", inline: "mkdir /home/vagrant/zookeeper"
end