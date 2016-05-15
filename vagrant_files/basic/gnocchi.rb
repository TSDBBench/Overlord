Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing Axibase
  config.vm.provision "shell", inline: "apt-get update"
#  config.vm.provision "shell", inline: "apt-get -q -y install python3-numpy python3-pandas-lib python3-psycopg2 python3-yaml python3-netifaces"
#  config.vm.provision "shell", inline: "apt-get -q -y install python3-oslo.i18n python3-oslo.utils python3-pandas python3-sqlalchemy python3-msgpack python3-trollius" # deps for api
  config.vm.provision "shell", inline: "apt-get -q -y install python3-psycopg2 python3-yaml python3-netifaces"
  config.vm.provision "shell", inline: "apt-get -q -y install python3-dev postgresql git vim"

  config.vm.provision "shell", inline: "wget https://bootstrap.pypa.io/get-pip.py"
  config.vm.provision "shell", inline: "python3 get-pip.py"


  config.vm.provision "shell", inline: "pip3.4 install tox"
  config.vm.provision "shell", inline: "pip3.4 install monotonic iso8601 debtcollector netaddr netifaces retrying stevedore pytimeparse sqlalchemy_utils wrapt keystoneauth1"  # install deps for api
#  config.vm.provision "shell", inline: "pip3.4 install gnocchi"

  config.vm.provision "shell", inline: "pip3.4 install oslo.db"
  config.vm.provision "shell", inline: "pip3.4 install tooz"
  config.vm.provision "shell", inline: "git clone https://github.com/openstack/gnocchi.git"
  config.vm.provision "shell", inline: "cd gnocchi; git checkout stable/1.3 ; pip3.4 install -e ."


  # setup postgresql as backend
  config.vm.provision "shell", inline: 'echo "host  all all 127.0.0.1/32 trust" > /etc/postgresql/9.4/main/pg_hba.conf'
  config.vm.provision "shell", inline: 'echo "local all all peer" >> /etc/postgresql/9.4/main/pg_hba.conf'
  config.vm.provision "shell", inline: "/etc/init.d/postgresql restart"
  config.vm.provision "shell", inline: "sudo -u postgres psql -c 'create user root superuser;' || true"
  config.vm.provision "shell", inline: "sudo -u postgres psql -c 'create database gnocchi;' || true"

  # setup gnocchi
  config.vm.provision "shell", inline: "/usr/local/bin/gnocchi-dbsync --config-dir /vagrant/files/"
  # start api
  config.vm.provision "shell", inline: "/vagrant/files/daemonize -e /var/log/gnocchi.err -o /var/log/gnocchi.log -l /var/run/gnocchi.lock -v /usr/local/bin/gnocchi-api --config-dir /vagrant/files/"
  # start metricd
  config.vm.provision "shell", inline: "/vagrant/files/daemonize -e /var/log/gnocchi-metricd.err -o /var/log/gnocchi-metricd.log -l /var/run/gnocchi-metricd.lock -v  /usr/local/bin/gnocchi-metricd --config-dir /vagrant/files/"
end
