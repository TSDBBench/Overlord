Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing KairosDB
  config.vm.provision "shell", privileged: false, inline: "wget -O /home/vagrant/kairosdb_1.0.0-1_all.deb -t 10 --retry-connrefused -nv \"https://github.com/kairosdb/kairosdb/releases/download/v1.0.0/kairosdb_1.0.0-1_all.deb\""
  config.vm.provision "shell", inline: "dpkg -i /home/vagrant/kairosdb_1.0.0-1_all.deb"
  config.vm.provision "shell", privileged: false,  inline: "rm /home/vagrant/kairosdb_1.0.0-1_all.deb"
  config.vm.provision "shell", inline: "systemctl stop kairosdb.service"
end