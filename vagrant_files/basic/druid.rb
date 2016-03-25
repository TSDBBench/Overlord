Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing Druid
  config.vm.provision "shell", privileged: false, inline: "wget -O /home/vagrant/druid.tar.gz -t 10 --retry-connrefused -nv \"http://static.druid.io/artifacts/releases/druid-0.8.1-bin.tar.gz\""
  config.vm.provision "shell", privileged: false,  inline: "tar -C /home/vagrant -xvzf /home/vagrant/druid.tar.gz"
  config.vm.provision "shell", privileged: false,  inline: "rm /home/vagrant/druid.tar.gz"
  config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y  install openjdk-7-jre:amd64 libmysql-java"
  config.vm.provision "shell", privileged: false, inline: "mkdir -p /tmp/druid/indexCache /tmp/persistent/zk_druid /tmp/persistent/task/ /tmp/druid/localStorage"
  config.vm.provision "shell", inline: "if [ ! -d /var/lib/mysql ]; then mkdir -p /var/lib/mysql; fi"
  config.vm.provision "shell", privileged: false, inline: "cp -r /vagrant/files/config /home/vagrant/"
  config.vm.provision "shell", inline: "cp /vagrant/files/druid*.service /etc/systemd/system"
  config.vm.provision "shell", inline: "chown root:root /etc/systemd/system/druid*.service"
  config.vm.provision "shell", inline: "systemctl daemon-reload"
end
