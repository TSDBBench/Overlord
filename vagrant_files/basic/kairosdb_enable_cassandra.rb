Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.provision "shell", inline: "sed -i \"s/kairosdb.service.datastore=org.kairosdb.datastore.h2.H2Module/#kairosdb.service.datastore=org.kairosdb.datastore.h2.H2Module/g\" /opt/kairosdb/conf/kairosdb.properties"
  config.vm.provision "shell", inline: "sed -i \"s/#kairosdb.service.datastore=org.kairosdb.datastore.cassandra.CassandraModule/kairosdb.service.datastore=org.kairosdb.datastore.cassandra.CassandraModule/g\" /opt/kairosdb/conf/kairosdb.properties"
end