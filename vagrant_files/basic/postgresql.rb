Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing PostgreSQL
  config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y  install postgresql"
  config.vm.provision "shell", inline: "sudo -u postgres psql -c \"ALTER USER postgres WITH PASSWORD 'vagrant';\""
  config.vm.provision "shell", inline: "sed -i \"s/#listen_addresses = 'localhost'/listen_addresses = '*'/g\" /etc/postgresql/9.4/main/postgresql.conf"
  config.vm.provision "shell", inline: "echo \"host    all             all             all         md5\" >> /etc/postgresql/9.4/main/pg_hba.conf"
  config.vm.provision "shell", inline: "systemctl restart postgresql.service"
end
