Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Installing KairosDB
  config.vm.provision "shell", privileged: false, inline: "wget -t 10 --retry-connrefused -nv \"https://github.com/kairosdb/kairosdb/releases/download/v1.0.0/kairosdb_1.0.0-1_all.deb\""
  config.vm.provision "shell", inline: "dpkg -i kairosdb_1.0.0-1_all.deb"
  config.vm.provision "shell", privileged: false,  inline: "rm kairosdb_1.0.0-1_all.deb"
  config.vm.provision "shell", inline: "systemctl stop kairosdb.service"
  config.vm.provision "shell", inline: "sed -i \"s/kairosdb.service.datastore=org.kairosdb.datastore.h2.H2Module/#kairosdb.service.datastore=org.kairosdb.datastore.h2.H2Module/g\" /opt/kairosdb/conf/kairosdb.properties"
  config.vm.provision "shell", inline: "sed -i \"s/#kairosdb.service.datastore=org.kairosdb.datastore.cassandra.CassandraModule/kairosdb.service.datastore=org.kairosdb.datastore.cassandra.CassandraModule/g\" /opt/kairosdb/conf/kairosdb.properties "
end