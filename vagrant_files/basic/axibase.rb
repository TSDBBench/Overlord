Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing Axibase
  config.vm.provision "shell", inline: "apt-get -q -y install sysstat openssh-server cron telnet debconf libc6 passwd adduser iproute net-tools curl netcat-openbsd"
  config.vm.provision "shell", inline: "echo 'deb http://archive.ubuntu.com/ubuntu/ xenial main universe' >> /etc/apt/sources.list"
  config.vm.provision "shell", inline: "apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 26AEE425A57967CFB323846008796A6514F3CB79"
  config.vm.provision "shell", inline: "apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 40976EAF437D05B5 3B4FE6ACC0B21F32"
  config.vm.provision "shell", inline: "apt-get update"
  config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y install openjdk-8-jdk libjpeg8"
  config.vm.provision "shell", inline: "useradd -m axibase" # the deb package postinstall script has an error prompting for pw does not work, this part is skipped if the axibase user exists

  config.vm.provision "shell", inline: "apt-get -q -y install software-properties-common"
  config.vm.provision "shell", inline: "add-apt-repository 'deb [arch=amd64] http://axibase.com/public/repository/deb/ ./'"
  config.vm.provision "shell", inline: "apt-get update"
  config.vm.provision "shell", inline: "DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y atsd"

  # give axibase some time to run
  config.vm.provision "shell", inline: "sleep 10"
  # set admin user
  config.vm.provision "shell", inline: "wget --post-data='userBean.username=admin&userBean.password=adminadmin&repeatPassword=adminadmin&type:' -O - http://127.0.0.1:8088/login"

end
