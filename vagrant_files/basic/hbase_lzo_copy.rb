Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
   config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y install liblzo2-2"
   #config.vm.provision "shell", privileged: false,  inline: "if [ -d /vagrant/files/lzo ]; then cp -r /vagrant/files/lzo/* /home/vagrant/hbase-1.1.2/lib/; chown -R vagrant:vagrant /home/vagrant/hbase-1.1.2/lib/; fi"
    config.vm.provision "shell", privileged: false,  inline: "if [ -d /vagrant/files/lzo  -a -f /vagrant/files/lzo/hadoop-lzo-0.4.15.tar.gz ]; then tar -xvzf /vagrant/files/lzo/hadoop-lzo-0.4.15.tar.gz -C /home/vagrant/hbase-1.1.2/lib/; chown -R vagrant:vagrant /home/vagrant/hbase-1.1.2/lib/;  fi"
end