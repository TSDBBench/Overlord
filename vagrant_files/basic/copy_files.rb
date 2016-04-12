Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.provision "shell", privileged: false,  inline: "if [ -d /vagrant/files ]; then cp -r /vagrant/files /home/vagrant/; chown -R vagrant:vagrant /home/vagrant/files; fi"
  config.vm.provision "shell", privileged: false,  inline: "if [ -d /home/vagrant/files ]; then chmod +x -f /home/vagrant/files/*.sh; exit 0; fi"
end