Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing InfluxDB
  config.vm.provision "shell", privileged: false,  inline: "wget -t 10 -O /home/vagrant/influxdb.deb --retry-connrefused -nv \"#{$links_influxdb}\""
  config.vm.provision "shell", inline: "dpkg -i /home/vagrant/influxdb.deb"
  config.vm.provision "shell", privileged: false,  inline: "rm /home/vagrant/influxdb.deb"
  config.vm.provision "shell", inline: "systemctl stop influxdb.service"
end
