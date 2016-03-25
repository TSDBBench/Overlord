Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing NewTS
  config.vm.provision "shell", privileged: false, inline: "wget -O /home/vagrant/newts-1.3.1-bin.tar.gz -t 10 --retry-connrefused -nv \"https://github.com/OpenNMS/newts/releases/download/1.3.1/newts-1.3.1-bin.tar.gz\""
  config.vm.provision "shell", privileged: false, inline: "tar -xvzf /home/vagrant/newts-1.3.1-bin.tar.gz"
  config.vm.provision "shell", privileged: false, inline: "rm /home/vagrant/newts-1.3.1-bin.tar.gz"
  config.vm.provision "shell", inline: "mkdir /var/log/newts"
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|# appenders:|appenders:|\"  /home/vagrant/newts-1.3.1/etc/config.yaml"
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|#   - type: file|   - type: file|\"  /home/vagrant/newts-1.3.1/etc/config.yaml"
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|#     currentLogFilename: /path/to/newts.log|     currentLogFilename: /var/log/newts/newts.log|\"  /home/vagrant/newts-1.3.1/etc/config.yaml"
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|#     threshold: ALL|     threshold: ALL|\"  /home/vagrant/newts-1.3.1/etc/config.yaml"
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|#     archive: true|     archive: true|\"  /home/vagrant/newts-1.3.1/etc/config.yaml"
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|#     archivedLogFilenamePattern: /path/to/newts-%d.log|     archivedLogFilenamePattern: /var/log/newts/newts-%d.log|\"  /home/vagrant/newts-1.3.1/etc/config.yaml"
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|#     archivedFileCount: 5|     archivedFileCount: 5|\"  /home/vagrant/newts-1.3.1/etc/config.yaml"
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|#     timeZone: UTC|     timeZone: UTC|\"  /home/vagrant/newts-1.3.1/etc/config.yaml"
  config.vm.provision "shell", inline: "cp /vagrant/files/newts.service /etc/systemd/system/"
  config.vm.provision "shell", inline: "chown root:root /etc/systemd/system/newts.service"
  config.vm.provision "shell", inline: "systemctl daemon-reload"
end
