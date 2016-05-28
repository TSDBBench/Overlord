Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.provision "shell", inline: "/root/change_hostname.sh #{HOSTNAME}"
  config.vm.provision "shell", inline: "if [ -f /etc/cloud/cloud.cfg ]; then sed -i 's/\(manage_etc_hosts:\).*/\1 false/' /etc/cloud/cloud.cfg; fi"
end