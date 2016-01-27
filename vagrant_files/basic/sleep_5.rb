Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.provision "shell", privileged: false,  inline: "sleep 5"
end