Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # KairosDB/Cassandra Replication Factor = 2
  config.vm.provision "shell", inline: "sed -i \"s/kairosdb.datastore.cassandra.replication_factor=1/kairosdb.datastore.cassandra.replication_factor=2/g\" /opt/kairosdb/conf/kairosdb.properties"
end