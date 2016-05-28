Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing deps
  config.vm.provision "shell", inline: "cp /vagrant/files/libakumuli_so /vagrant/files/libakumuli.so"
  config.vm.provision "shell", inline: "apt-get -q -y install sysstat libc6 net-tools netcat-openbsd libboost-dev libapr1 libaprutil1 libaprutil1-dbd-sqlite3  liblog4cxx10 libboost1.55-all-dev libmicrohttpd-dev libjemalloc-dev libsqlite3-dev"
  config.vm.provision "shell", inline: "cd /vagrant/files/ ; ./akumulid --init"
  config.vm.provision "shell", inline: "cd /vagrant/files/ ; ./akumulid --create"
  config.vm.provision "shell", inline: '/vagrant/files/daemonize -c /vagrant/files/ -e /var/log/akumulid.err -o /var/log/akumulid.log -l /var/run/akumulid.lock -v /vagrant/files/akumulid'
end
