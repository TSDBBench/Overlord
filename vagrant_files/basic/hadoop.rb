Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing Hadoop
  config.vm.provision "shell", privileged: false, inline: "wget -t 10 --retry-connrefused -nv \"http://ftp.fau.de/apache/hadoop/common/hadoop-2.7.1/hadoop-2.7.1.tar.gz\""
  config.vm.provision "shell", privileged: false,  inline: "tar -xvzf hadoop-2.7.1.tar.gz"
  config.vm.provision "shell", privileged: false,  inline: "rm hadoop-2.7.1.tar.gz"
end