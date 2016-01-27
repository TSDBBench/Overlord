Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing Opentsdb
  config.vm.provision "shell", privileged: false, inline: "wget -t 10 --retry-connrefused -nv \"https://github.com/OpenTSDB/opentsdb/releases/download/v2.2.0RC1/opentsdb-2.2.0RC1_all.deb\""
  config.vm.provision "shell", inline: "dpkg -i opentsdb-2.2.0RC1_all.deb"
  config.vm.provision "shell", privileged: false,  inline: "rm opentsdb-2.2.0RC1_all.deb"
  config.vm.provision "shell", inline: "systemctl stop opentsdb.service"
end
