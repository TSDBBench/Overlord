Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = 'dummy'
  config.vm.box_url = 'dummy.box'
  config.ssh.username = 'vagrant'
  
  config.vm.provider :vsphere do |vsphere|
    vsphere.host = ''          
    vsphere.compute_resource_name = ''            
    vsphere.resource_pool_name = ''
    vm_base_path = ''     
    vsphere.data_store_name = ''
    vsphere.user = ''                                    
    vsphere.password = ''                            
    vsphere.insecure = true                                    
  end
  config.vm.provider :openstack do |openstack|
    openstack.openstack_auth_url = ''
    openstack.username           = ''
    openstack.password           = ''
    openstack.tenant_name        = ''
    openstack.image              = ''
    openstack.floating_ip_pool   = ''
    openstack.openstack_image_url = ''
  end
end

# links to prepackaged/precompiled stuff
$links_ycsbts = 'http://nemarcontrolvm.iaas.uni-stuttgart.de/bin/ycsb-0.4.0.tar.gz'
$links_blueflood = 'http://nemarcontrolvm.iaas.uni-stuttgart.de/bin/blueflood-all-2.0.0-SNAPSHOT-jar-with-dependencies.jar'
  