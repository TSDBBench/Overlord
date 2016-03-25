Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing Hadoop
  config.vm.provision "shell", privileged: false, inline: "wget -O /home/vagrant/hadoop.tar.gz -t 10 --retry-connrefused -nv \"http://ftp.fau.de/apache/hadoop/common/hadoop-2.7.1/hadoop-2.7.1.tar.gz\""
  config.vm.provision "shell", privileged: false,  inline: "tar -C /home/vagrant/ -xvzf /home/vagrant/hadoop.tar.gz"
  config.vm.provision "shell", privileged: false,  inline: "rm /home/vagrant/hadoop.tar.gz"
end