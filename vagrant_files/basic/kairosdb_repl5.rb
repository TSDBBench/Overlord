Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # KairosDB/Cassandra Replication Factor = 5
  config.vm.provision "shell", inline: "sed -i \"s/kairosdb.datastore.cassandra.replication_factor=1/kairosdb.datastore.cassandra.replication_factor=5/g\" /opt/kairosdb/conf/kairosdb.properties"
end