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
  # download all deps in parallel on multiple VMs (better to do this here in parallel instead via RunWorkload.py); unit has a 5 Minute timeout so no timeout needed here
  # without pre-downloading deps sometimes druid fails because deps cannot be resolved via maven (mostly in single vm cluster)
  config.vm.provision "shell", inline: "systemctl start druid_repo.service"
  config.vm.provision "shell", inline: "while [ $(($(systemctl status druid_repo.service | grep -c \"inactive\")-1)) -ne 0 ]; do sleep 5; done"
end
