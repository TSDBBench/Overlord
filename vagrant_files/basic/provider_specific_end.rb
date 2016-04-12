Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    if $provider == "digital_ocean"
        config.vm.provider :digital_ocean do |digitalocean|
            config.vm.provision "shell", inline: "chown -R vagrant:vagrant /home/vagrant/"
        end
    end
end