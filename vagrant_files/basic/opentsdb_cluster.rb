Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Cluster Setting Opentsdb
  config.vm.provision "shell", privileged: false,  inline: "sed -i \"s|#tsd.storage.hbase.zk_quorum = localhost|tsd.storage.hbase.zk_quorum = vm0,vm1,vm2,vm3,vm4|\" /etc/opentsdb/opentsdb.conf"
end
