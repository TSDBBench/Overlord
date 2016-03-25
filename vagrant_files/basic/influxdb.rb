Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing InfluxDB
  # BUG in 0.9.4 (stable): https://github.com/influxdb/influxdb/issues/4170 -> use 0.9.5 (NIGHTLY)
  #config.vm.provision "shell", privileged: false, inline: "wget -t 10 --retry-connrefused -nv \"http://influxdb.s3.amazonaws.com/influxdb_0.9.4.2_amd64.deb\""
  #config.vm.provision "shell", inline: "dpkg -i influxdb_0.9.4.2_amd64.deb"
  #config.vm.provision "shell", privileged: false,  inline: "rm influxdb_0.9.4.2_amd64.deb"
  config.vm.provision "shell", privileged: false, inline: "wget -O /home/vagrant/influxdb_nightly_amd64.deb -t 10 --retry-connrefused -nv \"https://s3.amazonaws.com/influxdb/influxdb_nightly_amd64.deb\""
  # temporary fix for nightly, mkdir seems missing in postinst file in package (date: 2015-08-01) #
  config.vm.provision "shell", inline: "mkdir /var/lib/influxdb"
  config.vm.provision "shell", inline: "mkdir /var/log/influxdb"
  config.vm.provision "shell", inline: "touch /etc/lsb-release"
  ############################################################
  config.vm.provision "shell", inline: "dpkg -i /home/vagrant/influxdb_nightly_amd64.deb"
  config.vm.provision "shell", privileged: false,  inline: "rm /home/vagrant/influxdb_nightly_amd64.deb"
  config.vm.provision "shell", inline: "systemctl stop influxdb.service"
end
