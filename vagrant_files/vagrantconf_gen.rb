Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.provider :vsphere do |vsphere, override|
    vsphere.template_name = ''
  end
  config.vm.provider :openstack do |openstack, override|
    openstack.flavor             = ''
  end
  config.vm.provider :virtualbox do |virtualbox, override|
    virtualbox.customize ["modifyvm", :id, "--memory", "1024"]
  end
  config.vm.provider :digital_ocean do |digitalocean, override|
    digitalocean.image = "debian-8-x64"
    digitalocean.size = "512mb"
  end
  config.vm.provider :aws do |aws, override|
    aws.instance_type = "t2.micro"
    aws.ami = "ami-ccc021a3" # Debian Jessie
    aws.block_device_mapping = [{ 'DeviceName' => '/dev/xvda', 'Ebs.VolumeSize' => 20, 'Ebs.VolumeType' => 'gp2' }]
  end
end