Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing Axibase
  config.vm.provision "shell", inline: "wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -"
  config.vm.provision "shell", inline: "echo 'deb http://packages.elastic.co/elasticsearch/2.x/debian stable main' | sudo tee -a /etc/apt/sources.list.d/elasticsearch-2.x.list"
  config.vm.provision "shell", inline: "apt-get update"
  config.vm.provision "shell", inline: "apt-get update && apt-get install elasticsearch"
  config.vm.provision "shell", inline: "ln -s /etc/elasticsearch/ /usr/share/elasticsearch/config"
  # do some configuration
  config.vm.provision "shell", inline: "echo 'node.name: #{HOSTNAME}'  >> /etc/elasticsearch/elasticsearch.yml"
  config.vm.provision "shell", inline: "echo 'cluster.name: elasticsearch'  >> /etc/elasticsearch/elasticsearch.yml"
  config.vm.provision "shell", inline: "systemctl enable elasticsearch.service"
  config.vm.provision "shell", inline: "/etc/init.d/elasticsearch start"
  # config.vm.provision "shell", inline: "wget --tries=50 --waitretry=5 --retry-connrefused #{HOSTNAME}:9200 -O -"
end
