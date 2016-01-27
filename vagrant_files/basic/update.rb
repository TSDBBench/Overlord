Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
   config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y update"
end