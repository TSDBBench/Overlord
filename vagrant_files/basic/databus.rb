Vagrant.configure(VAGRANTFILE_API_VERSION) do |config| 
  config.vm.provision "shell", inline: 'apt-get --allow-unauthenticated -q -y install unzip openjdk-7-jdk'
  config.vm.provision "shell", privileged: false, inline: "mkdir ~vagrant/files"
  config.vm.provision "shell", privileged: false, inline: "cd ~vagrant/files ; wget -t 10 --retry-connrefused -nv \"https://github.com/deanhiller/databus/archive/1.1.0-3661.zip\""
  config.vm.provision "shell", privileged: false, inline: "cd ~vagrant/files ; unzip 1.1.0-3661.zip"
  config.vm.provision "shell", inline: "cd ~vagrant/files/databus-1.1.0-3661 ; ./build.sh build"
end
