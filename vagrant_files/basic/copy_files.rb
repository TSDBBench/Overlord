Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.provision "shell", privileged: false,  inline: "if [ -d /vagrant/files ]; then cp -r /vagrant/files ~/; fi"
  config.vm.provision "shell", privileged: false,  inline: "if [ -d ~/files ]; then chmod +x -f ~/files/*.sh; exit 0; fi"
end