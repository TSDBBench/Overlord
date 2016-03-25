Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
   config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y install ant liblzo2-dev git openjdk-7-jdk"
   config.vm.provision "shell", privileged: false,  inline: "cd /home/vagrant && git clone git://github.com/cloudera/hadoop-lzo.git"
   config.vm.provision "shell", privileged: false,  inline: "sed -i 's|    </javah>|      <classpath refid=\"classpath\"/>\\n    </javah>|' /home/vagrant/hadoop-lzo/build.xml"
   config.vm.provision "shell", privileged: false,  inline: "cd /home/vagrant/hadoop-lzo && JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64 CFLAGS=-m64 CXXFLAGS=-m64 ant compile-native tar"
   config.vm.provision "shell", privileged: false,  inline: "mkdir -p /home/vagrant/hbase/lib/native"
   config.vm.provision "shell", privileged: false,  inline: "cp /home/vagrant/hadoop-lzo/build/hadoop-lzo-0.4.15/hadoop-lzo-0.4.15.jar /home/vagrant/hbase/lib"
   config.vm.provision "shell", privileged: false,  inline: "cp -a /home/vagrant/hadoop-lzo/build/hadoop-lzo-0.4.15/lib/native/* /home/vagrant/hbase/lib/native"
end