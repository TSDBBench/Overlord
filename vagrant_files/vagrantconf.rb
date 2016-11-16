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
    openstack.security_groups     = ['default','allow_all']
    # allow_all or default must at least provide SSH (22) ingress access!
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
  # You need to create a Security Group that allows traffic from your IP (at least) to port 22
  # In this example the security group is called "SSH"
  # Links to Security Groups for region "eu-central-1":
  # https://eu-central-1.console.aws.amazon.com/ec2/v2/home?region=eu-central-1#SecurityGroups:sort=groupId
  # Otherwise you need to use a VPN connection and edit the configuration
  # e.g. set aws. ssh_host_attribute  to :private_ip_address
  # See https://github.com/mitchellh/vagrant-aws for further information
  # A SSH Key must be added in the region used (manually via AWS Management Console)
  # Username is admin in Debian Jessie's image but after aws_commands.txt is executed, user vagrant is existing
  config.vm.provider :aws do |aws, override|
    aws.access_key_id = ""
    aws.secret_access_key = ""
    aws.keypair_name = ""
    aws.region = "eu-central-1"
    aws.monitoring = false
    aws.elastic_ip = false
    aws.associate_public_ip = false
    aws.security_groups = [ "default", "SSH" ] # default allows conntections inside VPC (between VMs)
    aws.tenancy = "default"
    aws.terminate_on_shutdown = false
    aws. ssh_host_attribute = :public_ip_address
    override.ssh.private_key_path = "~/.ssh/id_rsa"
    aws.user_data = File.read("aws_commands.txt")
  end
end

# links to prepackaged/precompiled stuff
$links_ycsbts = 'http://nemarcontrolvm.iaas.uni-stuttgart.de/bin/ycsb-0.4.0.tar.gz'
$links_blueflood = 'http://nemarcontrolvm.iaas.uni-stuttgart.de/bin/blueflood-all-2.0.0-SNAPSHOT-jar-with-dependencies.jar'
  
# Akumuli git link and commit id
$git_akumuli_link = 'https://github.com/akumuli/Akumuli.git'
$git_akumuli_hash = 'fa85dd90a2e09bc28630bbe3fdd28fe155566360'
  
# h5serv (hdf5) git commit ids
$git_h5json = 'a85c6b195dc63687391f8e69be3f6d595679c0f5'
$git_h5serv = '18709351fb173697e323eb62828cb8868f2e1db3'

# hbase
$links_hbase = 'http://ftp-stud.hs-esslingen.de/pub/Mirrors/ftp.apache.org/dist/hbase/1.1.5/hbase-1.1.5-bin.tar.gz'

# influxdb
# influxdb 0.12. and upwards does not support clustering anymore, see https://influxdata.com/blog/update-on-influxdb-clustering-high-availability-and-monetization/
# It uses relay instead for high availability (clustering only in enterprise version)
$links_influxdb = 'https://s3.amazonaws.com/influxdb/influxdb_0.11.1-1_amd64.deb'
