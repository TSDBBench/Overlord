Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing deps
  config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y  install git cmake libboost-dev libboost-system-dev libboost-thread-dev libboost-filesystem-dev libboost-test-dev libboost-coroutine-dev libboost-context-dev libboost-program-options-dev libboost-regex-dev libapr1-dev libaprutil1-dev libaprutil1-dbd-sqlite3 libmicrohttpd-dev liblog4cxx10-dev liblog4cxx10 libjemalloc-dev libsqlite3-dev"
  config.vm.provision "shell", inline: "cd /home/vagrant/ && git clone \"#{$git_akumuli_link}\""
  config.vm.provision "shell", inline: "cd /home/vagrant/Akumuli && git checkout \"#{$git_akumuli_hash}\""
  config.vm.provision "shell", inline: "cd /home/vagrant/Akumuli && cmake ."
  config.vm.provision "shell", inline: "cd /home/vagrant/Akumuli && make -j"
  config.vm.provision "shell", inline: "apt-get -q -y install sysstat libc6 net-tools netcat-openbsd libboost-dev libapr1 libaprutil1 libaprutil1-dbd-sqlite3  liblog4cxx10 libboost1.55-all-dev libmicrohttpd-dev libjemalloc-dev libsqlite3-dev"
  config.vm.provision "shell", inline: "cd /home/vagrant/Akumuli/akumulid && ./akumulid --init"
  config.vm.provision "shell", inline: "cd /home/vagrant/Akumuli/akumulid && ./akumulid --create"
  config.vm.provision "shell", inline: "cp /vagrant/files/akumuli.service /etc/systemd/system"
  config.vm.provision "shell", inline: "chown root:root /etc/systemd/system/akumuli.service"
  config.vm.provision "shell", inline: "systemctl daemon-reload"
  config.vm.provision "shell", inline: "systemctl start akumuli.service"  
end
