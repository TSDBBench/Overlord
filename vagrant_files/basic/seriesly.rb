Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing Axibase
  config.vm.provision "shell", inline: "echo 'deb http://ftp.debian.org/debian jessie-backports main' >> /etc/apt/sources.list"
  config.vm.provision "shell", inline: "apt-get update"
  config.vm.provision "shell", inline: "apt-get -q -y  install git"
  config.vm.provision "shell", inline: "apt-get -q -y -t jessie-backports install golang-go"
  config.vm.provision "shell", privileged: false, inline: "mkdir /home/vagrant/go/; GOPATH=/home/vagrant/go/ go get github.com/dustin/seriesly"
  config.vm.provision "shell", inline: '/vagrant/files/daemonize -e /var/log/seriesly.err -o /var/log/seriesly.log -l /var/run/seriesly.lock -v /home/vagrant/go/bin/seriesly -addr="0.0.0.0:3133"'
end
