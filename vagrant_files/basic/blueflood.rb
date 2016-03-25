Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing Blueflood
  config.vm.provision "shell", privileged: false, inline: "wget -O /home/vagrant/bluefllod.jar -t 10 --retry-connrefused -nv \"#{$links_blueflood}\""
  config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y  install openjdk-7-jre:amd64 "
  config.vm.provision "shell", privileged: false, inline: "cp /vagrant/files/{blueflood-log4j.properties,blueflood.conf} /home/vagrant/"
  config.vm.provision "shell", inline: "cp /vagrant/files/blueflood.service /etc/systemd/system"
  config.vm.provision "shell", inline: "chown root:root /etc/systemd/system/blueflood.service"
  config.vm.provision "shell", inline: "systemctl daemon-reload"
end
