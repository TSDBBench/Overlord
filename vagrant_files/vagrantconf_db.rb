Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.provider :vsphere do |vsphere|              
    vsphere.template_name  = ''                      
  end
  config.vm.provider :openstack do |openstack|
    openstack.flavor             = ''
  end
  config.vm.provider :virtualbox do |virtualbox|
    virtualbox.customize ["modifyvm", :id, "--memory", "1024"]   
  end
  config.vm.provider :digital_ocean do |digitalocean|
    digitalocean.image = "debian-8-x64"
    digitalocean.size = "512mb"
  end
end