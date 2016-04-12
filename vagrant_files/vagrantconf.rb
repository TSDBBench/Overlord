Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = 'dummy'
  config.vm.box_url = 'dummy.box'
  config.ssh.username = 'vagrant'
  
  config.vm.provider :vsphere do |vsphere, override|
    vsphere.host = ''
    vsphere.compute_resource_name = ''
    vsphere.resource_pool_name = ''
    vm_base_path = ''
    vsphere.data_store_name = ''
    vsphere.user = ''
    vsphere.password = ''
    vsphere.insecure = true
  end
  config.vm.provider :openstack do |openstack, override|
    openstack.openstack_auth_url = ''
    openstack.username           = ''
    openstack.password           = ''
    openstack.tenant_name        = ''
    openstack.image              = ''
    openstack.floating_ip_pool   = ''
    openstack.openstack_image_url = ''
  end
  config.vm.provider :virtualbox do |virtualbox, override|
    override.vm.box                = "tsdbbench-debian"
    virtualbox.gui                 = false
    override.vm.network "private_network", type: "dhcp"
  end
  config.vm.provider :digital_ocean do |digitalocean, override|
    # See https://github.com/devopsgroup-io/vagrant-digitalocean for configuration details
    override.ssh.private_key_path = "~/.ssh/id_rsa"
    digitalocean.token = ""
    digitalocean.region = "fra1" # private networking must be supported in this region
    digitalocean.private_networking = true
    digitalocean.ipv6 = false
    digitalocean.setup = true
    digitalocean.backups_enabled = false
  end
end

# links to prepackaged/precompiled stuff
$links_ycsbts = 'http://nemarcontrolvm.iaas.uni-stuttgart.de/bin/ycsb-0.4.0.tar.gz'
$links_blueflood = 'http://nemarcontrolvm.iaas.uni-stuttgart.de/bin/blueflood-all-2.0.0-SNAPSHOT-jar-with-dependencies.jar'
  
# h5serv (hdf5) git commit ids
$git_h5json = 'c31bfb7ff2da864a737ce9464ba1895b0d5af8f4'
$git_h5serv = '18709351fb173697e323eb62828cb8868f2e1db3'

# hbase
$links_hbase = 'http://ftp-stud.hs-esslingen.de/pub/Mirrors/ftp.apache.org/dist/hbase/1.1.4/hbase-1.1.4-bin.tar.gz'

# influxdb
# influxdb 0.12. and upwards does not support clustering anymore, see https://influxdata.com/blog/update-on-influxdb-clustering-high-availability-and-monetization/
# It uses relay instead for high availability (clustering only in enterprise version)
$links_influxdb = 'https://s3.amazonaws.com/influxdb/influxdb_0.11.1-1_amd64.deb'
