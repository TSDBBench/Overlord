Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.provision "shell", inline: "/root/change_hostname.sh #{HOSTNAME}"
end