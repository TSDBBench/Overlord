Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
   # Installing h5serv
   # newer python-numpy from testing is required, otherwise "AttributeError: 'numpy.ndarray' object has no attribute 'tobytes'" will occur
   # its faster to use debian packages, all can be build by pip as an alternative (slower)
   config.vm.provision "shell", inline: "echo 'APT::Default-Release \"jessie\";' > /etc/apt/apt.conf.d/99defaultrelease"
   config.vm.provision "shell", inline: "echo 'deb http://ftp.de.debian.org/debian stretch main contrib non-free' >> /etc/apt/sources.list"
   config.vm.provision "shell", inline: "echo 'deb-src http://ftp.de.debian.org/debian stretch main contrib non-free' >> /etc/apt/sources.list"
   config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y update"  
   config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y  install python2.7 cython python-dev python-pip git libhdf5-serial-dev python-h5py python-requests python-tables python-tz python-tornado"
   config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y -t stretch install python-numpy"
   # alternatively all can be build with pip (slower!):
   #config.vm.provision "shell", inline: "pip install numpy"
   #config.vm.provision "shell", inline: "env CPPFLAGS='-I/usr/lib/x86_64-linux-gnu/hdf5/serial/include/' LDFLAGS='-L/usr/lib/x86_64-linux-gnu/hdf5/serial/lib/' pip install h5py"
   #config.vm.provision "shell", inline: "pip install requests"
   #config.vm.provision "shell", inline: "env CPPFLAGS='-I/usr/lib/x86_64-linux-gnu/hdf5/serial/include/' LDFLAGS='-L/usr/lib/x86_64-linux-gnu/hdf5/serial/lib/' HDF5_DIR='/usr/lib/x86_64-linux-gnu/hdf5/serial/lib/' pip install tables"
   #config.vm.provision "shell", inline: "pip install pytz"
   #config.vm.provision "shell", inline: "pip install tornado"
   config.vm.provision "shell", privileged: false,  inline: "cd /home/vagrant/ && git clone https://github.com/HDFGroup/hdf5-json.git"
   config.vm.provision "shell", privileged: false,  inline: "cd /home/vagrant/hdf5-json && git checkout \"#{$git_h5json}\""
   config.vm.provision "shell", inline: "cd /home/vagrant/hdf5-json && env CPPFLAGS='-I/usr/lib/x86_64-linux-gnu/hdf5/serial/include/' LDFLAGS='-L/usr/lib/x86_64-linux-gnu/hdf5/serial/lib/' HDF5_DIR='/usr/lib/x86_64-linux-gnu/hdf5/serial/lib/' python setup.py install"
   config.vm.provision "shell", inline: "cd /home/vagrant/hdf5-json && python testall.py --unit"  
   config.vm.provision "shell", privileged: false,  inline: "cd /home/vagrant/ && git clone https://github.com/HDFGroup/h5serv.git"
   config.vm.provision "shell", privileged: false,  inline: "cd /home/vagrant/h5serv && git checkout \"#{$git_h5serv}\""
   config.vm.provision "shell", inline: "cp /vagrant/files/h5serv.service /etc/systemd/system"
   config.vm.provision "shell", inline: "chown root:root /etc/systemd/system/h5serv.service"
   config.vm.provision "shell", inline: "systemctl daemon-reload"
   config.vm.provision "shell", inline: "systemctl start h5serv.service"  
   config.vm.provision "shell", privileged: false, inline: "cd /home/vagrant/h5serv && python test/testall.py"  
   config.vm.provision "shell", inline: "systemctl stop h5serv.service"  
   config.vm.provision "shell", inline: "rm -r /home/vagrant/h5serv/data/*"  
   config.vm.provision "shell", inline: "sed -i \"s/'debug':  True/'debug':  False/g\" /home/vagrant/h5serv/server/config.py"
   config.vm.provision "shell", inline: "systemctl start h5serv.service"  
end
