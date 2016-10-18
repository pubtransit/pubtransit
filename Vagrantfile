# -*- mode: ruby -*-

Vagrant.require_version ">= 1.7.0"

# Takes proxy configuratiom from host environment
http_proxy = ENV["http_proxy"]
https_proxy = ENV["https_proxy"]
no_proxy = ENV["no_proxy"]
if http_proxy or https_proxy
  require 'vagrant-proxyconf'
end


control_ip = "192.168.0.10"

tenant_ip = "192.168.1.10"


# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "ubuntu/xenial64"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Collectd will fail to install if it is not able to resolve the ip from its
  # hostname. Setting the host name here will make Vagrant configuring
  # /etc/hosts fixing this problem
  config.vm.hostname = "www.transit.org"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Virtual box specific configuration
  config.vm.provider "virtualbox" do |vb|
    # Display the VirtualBox GUI when booting the machine
    vb.gui = false

    # Customize the amount of memory on the VM. This ammout is recommended
    # to make OpenStack working.
    vb.memory = "8192"

    # Set machine hostname
    vb.name = "transit"
  end

  # Use the same Proxy servers as the host machine
  if Vagrant.has_plugin?("vagrant-proxyconf")
    require 'resolv'
    Resolv.getaddresses("http_proxy")
    if http_proxy
      config.proxy.http = http_proxy
    end
    if https_proxy
      config.proxy.https = https_proxy
    end
    if no_proxy
      config.proxy.no_proxy = no_proxy
    end
  end

  # Use the same DNS server as the host machine
  config.vm.provision "file", source: "/etc/resolv.conf",
    destination: "~/resolv.conf"
  config.vm.provision "shell", privileged: false,
    inline: "sudo mv ~/resolv.conf /etc/resolv.conf"

  # assure python is installed
  config.vm.provision "shell", privileged: true,
    inline: "python --version || DEBIAN_FRONTEND=noninteractive apt-get install -y python-minimal"

  # Run ansible playbook
  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "provision.yml"
    ansible.limit = "all"
  end

end
