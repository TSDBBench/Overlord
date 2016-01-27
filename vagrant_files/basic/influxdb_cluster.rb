Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Setup InfluxDB Cluster
  config.vm.provision "shell", inline: "sed -i 's|hostname = \"localhost\"|hostname = \"#{HOSTNAME}\"|' /etc/influxdb/influxdb.conf"
  if INFLUXDBHOSTNAMES != ""
    config.vm.provision "shell", inline: "echo 'INFLUXD_OPTS=\"-join #{INFLUXDBHOSTNAMES}\"' >>/etc/default/influxdb"
  end
end