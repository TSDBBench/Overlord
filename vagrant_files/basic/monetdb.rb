Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing MonetDB
  config.vm.provision "shell", inline: "echo \"deb http://dev.monetdb.org/downloads/deb/ jessie monetdb\" >> /etc/apt/sources.list"
  config.vm.provision "shell", inline: "echo \"deb-src http://dev.monetdb.org/downloads/deb/ jessie monetdb\" >> /etc/apt/sources.list"
  config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y update"
  config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y  install monetdb5-sql monetdb-client"
  config.vm.provision "shell", inline: "/etc/init.d/monetdb5-sql stop"
  config.vm.provision "shell", privileged: false, inline: "echo -e \"user=monetdb\npassword=monetdb\nlanguage=sql\n\" > /home/vagrant/.monetdb"
  config.vm.provision "shell", inline: "echo -e \"user=monetdb\npassword=monetdb\nlanguage=sql\n\" > /root/.monetdb"
end