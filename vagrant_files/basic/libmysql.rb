Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  #  install libmysql
  config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y  install libmysql-java"
end
