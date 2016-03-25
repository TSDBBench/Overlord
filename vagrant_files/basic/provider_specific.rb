$sshscript = <<SSHSCRIPT
echo "-----BEGIN RSA PRIVATE KEY-----" >> /home/vagrant/.ssh/id_rsa
echo "MIIEogIBAAKCAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+kz4TjGYe7gHzI" >> /home/vagrant/.ssh/id_rsa
echo "w+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6IedplqoP" >> /home/vagrant/.ssh/id_rsa
echo "kcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2" >> /home/vagrant/.ssh/id_rsa
echo "hMNG0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NO" >> /home/vagrant/.ssh/id_rsa
echo "Td0jMZEnDkbUvxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcW" >> /home/vagrant/.ssh/id_rsa
echo "yLbIbEgE98OHlnVYCzRdK8jlqm8tehUc9c9WhQIBIwKCAQEA4iqWPJXtzZA68mKd" >> /home/vagrant/.ssh/id_rsa
echo "ELs4jJsdyky+ewdZeNds5tjcnHU5zUYE25K+ffJED9qUWICcLZDc81TGWjHyAqD1" >> /home/vagrant/.ssh/id_rsa
echo "Bw7XpgUwFgeUJwUlzQurAv+/ySnxiwuaGJfhFM1CaQHzfXphgVml+fZUvnJUTvzf" >> /home/vagrant/.ssh/id_rsa
echo "TK2Lg6EdbUE9TarUlBf/xPfuEhMSlIE5keb/Zz3/LUlRg8yDqz5w+QWVJ4utnKnK" >> /home/vagrant/.ssh/id_rsa
echo "iqwZN0mwpwU7YSyJhlT4YV1F3n4YjLswM5wJs2oqm0jssQu/BT0tyEXNDYBLEF4A" >> /home/vagrant/.ssh/id_rsa
echo "sClaWuSJ2kjq7KhrrYXzagqhnSei9ODYFShJu8UWVec3Ihb5ZXlzO6vdNQ1J9Xsf" >> /home/vagrant/.ssh/id_rsa
echo "4m+2ywKBgQD6qFxx/Rv9CNN96l/4rb14HKirC2o/orApiHmHDsURs5rUKDx0f9iP" >> /home/vagrant/.ssh/id_rsa
echo "cXN7S1uePXuJRK/5hsubaOCx3Owd2u9gD6Oq0CsMkE4CUSiJcYrMANtx54cGH7Rk" >> /home/vagrant/.ssh/id_rsa
echo "EjFZxK8xAv1ldELEyxrFqkbE4BKd8QOt414qjvTGyAK+OLD3M2QdCQKBgQDtx8pN" >> /home/vagrant/.ssh/id_rsa
echo "CAxR7yhHbIWT1AH66+XWN8bXq7l3RO/ukeaci98JfkbkxURZhtxV/HHuvUhnPLdX" >> /home/vagrant/.ssh/id_rsa
echo "3TwygPBYZFNo4pzVEhzWoTtnEtrFueKxyc3+LjZpuo+mBlQ6ORtfgkr9gBVphXZG" >> /home/vagrant/.ssh/id_rsa
echo "YEzkCD3lVdl8L4cw9BVpKrJCs1c5taGjDgdInQKBgHm/fVvv96bJxc9x1tffXAcj" >> /home/vagrant/.ssh/id_rsa
echo "3OVdUN0UgXNCSaf/3A/phbeBQe9xS+3mpc4r6qvx+iy69mNBeNZ0xOitIjpjBo2+" >> /home/vagrant/.ssh/id_rsa
echo "dBEjSBwLk5q5tJqHmy/jKMJL4n9ROlx93XS+njxgibTvU6Fp9w+NOFD/HvxB3Tcz" >> /home/vagrant/.ssh/id_rsa
echo "6+jJF85D5BNAG3DBMKBjAoGBAOAxZvgsKN+JuENXsST7F89Tck2iTcQIT8g5rwWC" >> /home/vagrant/.ssh/id_rsa
echo "P9Vt74yboe2kDT531w8+egz7nAmRBKNM751U/95P9t88EDacDI/Z2OwnuFQHCPDF" >> /home/vagrant/.ssh/id_rsa
echo "llYOUI+SpLJ6/vURRbHSnnn8a/XG+nzedGH5JGqEJNQsz+xT2axM0/W/CRknmGaJ" >> /home/vagrant/.ssh/id_rsa
echo "kda/AoGANWrLCz708y7VYgAtW2Uf1DPOIYMdvo6fxIB5i9ZfISgcJ/bbCUkFrhoH" >> /home/vagrant/.ssh/id_rsa
echo "+vq/5CIWxCPp0f85R4qxxQ5ihxJ0YDQT9Jpx4TMss4PSavPaBH3RXow5Ohe+bYoQ" >> /home/vagrant/.ssh/id_rsa
echo "NE5OgEXk2wVfZczCZpigBKbKZHNYcelXtTt/nP3rsCuGcM4h53s=" >> /home/vagrant/.ssh/id_rsa
echo "-----END RSA PRIVATE KEY-----" >> /home/vagrant/.ssh/id_rsa
SSHSCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.vm.provider :digital_ocean do |digitalocean|
        config.vm.provision "shell", inline: "sed -i 's|http://http.debian.net/debian|http://ftp.de.debian.org/debian/|g' /etc/apt/sources.list"
        config.vm.provision "shell", inline: "sed -i 's|main$|main contrib non-free|g' /etc/apt/sources.list"
    end
end
 
load 'basic/update.rb'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.vm.hostname = HOSTNAME
    config.vm.provider :digital_ocean do |digitalocean|
        # all what is done in preseed files (see preseed-vsphere.cfg for example) must be done here for digitalocean
        config.vm.provision "shell", inline: "echo 'Defaults env_keep += \"SSH_AUTH_SOCK DEBIAN_FRONTEND\"' >> /etc/sudoers"
        config.vm.provision "shell", inline: "echo 'export DEBIAN_FRONTEND=noninteractive' >> /home/vagrant/.bashrc"
        config.vm.provision "shell", inline: "echo 'export DEBIAN_FRONTEND=noninteractive' >> /root/.bashrc"
        # digital_ocean uses specific ssh keys, add vagrant ones
        config.vm.provision "shell", inline: "echo 'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+kz4TjGYe7gHzIw+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6IedplqoPkcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2hMNG0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NOTd0jMZEnDkbUvxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcWyLbIbEgE98OHlnVYCzRdK8jlqm8tehUc9c9WhQ== vagrant insecure public key' >> /home/vagrant/.ssh/authorized_keys"
        config.vm.provision "shell", inline: "echo 'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+kz4TjGYe7gHzIw+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6IedplqoPkcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2hMNG0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NOTd0jMZEnDkbUvxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcWyLbIbEgE98OHlnVYCzRdK8jlqm8tehUc9c9WhQ== vagrant insecure public key' >> /home/vagrant/.ssh/id_rsa.pub"
        config.vm.provision "shell", inline: "echo 'Host *' >> /home/vagrant/.ssh/config"
        config.vm.provision "shell", inline: "echo '   StrictHostKeyChecking no' >> /home/vagrant/.ssh/config"
        config.vm.provision "shell", inline: "echo '   UserKnownHostsFile=/dev/null' >> /home/vagrant/.ssh/config"
        config.vm.provision "shell", inline: $sshscript
        config.vm.provision "shell", inline: "chmod 640 /home/vagrant/.ssh/id_rsa.pub"
        config.vm.provision "shell", inline: "chmod 600 /home/vagrant/.ssh/id_rsa"
        config.vm.provision "shell", inline: "chown -R vagrant:vagrant /home/vagrant/.ssh"
        config.vm.provision "shell", inline: "chmod -R go-rwx /home/vagrant/.ssh/authorized_keys"
        config.vm.provision "shell", inline: "cp -r /home/vagrant/.ssh /root/"
        config.vm.provision "shell", inline: "chown -R root:root /root/.ssh/"
        config.vm.provision "shell", inline: "sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/g' /etc/ssh/sshd_config"
        # sudo is already there
        config.vm.provision "shell", inline: "apt-get --allow-unauthenticated -q -y install build-essential ruby-highline ruby-termios ntp linux-headers-amd64 dpkg screen htop wget curl openjdk-7-jre open-vm-tools rsync libpam-systemd python2.7 fabric resolvconf linux-image-amd64 openssh-server"
        config.vm.provision "shell", inline: "echo 'blacklist ipv6' >> /etc/modprobe.d/blacklist.conf"
        config.vm.provision "shell", inline: "echo 'fs.file-max = 404358' >> /etc/sysctl.conf"
        config.vm.provision "shell", inline: "echo 'fs.file-max = 404358' >> /etc/sysctl.d/99-sysctl.conf"
        config.vm.provision "shell", inline: "sysctl -p /etc/sysctl.conf"
        config.vm.provision "shell", inline: "sysctl -p /etc/sysctl.d/99-sysctl.conf"
        config.vm.provision "shell", inline: "echo '* - nofile 404358' >> /etc/security/limits.conf"
        config.vm.provision "shell", inline: "echo 'root - nofile 404358' >> /etc/security/limits.conf"
        config.vm.provision "shell", inline: "echo '#!/bin/bash' >> /home/vagrant/change_hostname.sh"; \
        config.vm.provision "shell", inline: "echo 'get_ip=\$(sudo ifconfig | grep -E -o \"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\" | head -n1)' >> /home/vagrant/change_hostname.sh"
        config.vm.provision "shell", inline: "echo 'sudo -s bash -c \"echo \\\"\$get_ip \$1\\\" >> /etc/hosts\"' >> /home/vagrant/change_hostname.sh"
        config.vm.provision "shell", inline: "echo 'sudo -s bash -c \"sudo hostname \$1\"' >> /home/vagrant/change_hostname.sh"
        config.vm.provision "shell", inline: "echo 'sudo -s bash -c \"echo \\\"\$1\\\" > /etc/hostname\"' >> /home/vagrant/change_hostname.sh"
        config.vm.provision "shell", inline: "echo 'sudo -s bash -c \"sudo sed -i \\\"s/127.0.1.1.*$//g\\\" /etc/hosts\"' >> /home/vagrant/change_hostname.sh"
        config.vm.provision "shell", inline: "echo 'sudo hostnamectl set-hostname \$1' >> /home/vagrant/change_hostname.sh"
        config.vm.provision "shell", inline: "cp /home/vagrant/change_hostname.sh /root/change_hostname.sh"
        config.vm.provision "shell", inline: "chmod 775 /home/vagrant/change_hostname.sh /root/change_hostname.sh"
        config.vm.provision "shell", inline: "chown vagrant:vagrant /home/vagrant/change_hostname.sh"
        config.vm.provision "shell", inline: "chown root:root /root/change_hostname.sh"
        config.vm.provision "shell", inline: "apt-get clean"
    end
end
