Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Setup Mysql for Druid
  config.vm.provision "shell", privileged: false, inline: "mysql -u root --password='vagrant' -e \"create database if not exists druid default charset utf8 COLLATE utf8_general_ci;GRANT ALL PRIVILEGES ON druid.* TO druid@'%' IDENTIFIED BY 'diurd';FLUSH PRIVILEGES;\"";  
end
