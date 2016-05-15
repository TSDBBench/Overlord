Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.provision "shell", inline: "apt-get -q -y install python-dev apache2 libapache2-mod-wsgi build-essential libcairo2-dev libffi-dev python-pip"
  config.vm.provision "shell", inline: "pip install twisted pytz https://github.com/graphite-project/ceres/tarball/master whisper graphite-api"
  config.vm.provision "shell", inline: "pip install carbon --install-option=\"--prefix=~vagrant/graphite\" --install-option=\"--install-lib=~vagrant/graphite/lib\""

  config.vm.provision "shell", inline: "cp ~vagrant/graphite/conf/carbon.conf.example ~vagrant/graphite/conf/carbon.conf"
  config.vm.provision "shell", inline: "cp ~vagrant/files/storage-schemas.conf ~vagrant/graphite/conf/storage-schemas.conf"
  # Hack: Computes and sets the Whisper data retention duration (seconds from now to the past), so Whisper allows and retains the inserts
  # of the workloads (first time stamp of each workload is epoch seconds 1439241005; 86400s = 1d will be added to the computed duration) 
  config.vm.provision "shell", inline: 'echo "retentions = 1s:$(($(date +%s)-1439241005+86400))s" >> ~vagrant/graphite/conf/storage-schemas.conf'

  config.vm.provision "shell", inline: "mkdir /var/www/wsgi-scripts"
  config.vm.provision "shell", inline: "cp ~vagrant/files/graphite.conf /etc/apache2/conf-available/graphite.conf"
  config.vm.provision "shell", inline: "ln -s /etc/apache2/conf-available/graphite.conf /etc/apache2/conf-enabled/graphite.conf"
  config.vm.provision "shell", inline: "cp ~vagrant/files/graphite-api.wsgi /var/www/wsgi-scripts/graphite-api.wsgi"
  config.vm.provision "shell", inline: "cp ~vagrant/files/graphite-api.yaml /etc/graphite-api.yaml"

  config.vm.provision "shell", inline: "~vagrant/graphite/bin/carbon-cache.py start"
  config.vm.provision "shell", inline: "/etc/init.d/apache2 restart"

end
