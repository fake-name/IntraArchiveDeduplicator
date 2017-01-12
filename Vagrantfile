# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  config.vm.define "ubuntu-14" do |web|

    # Every Vagrant development environment requires a box. You can search for
    # boxes at https://atlas.hashicorp.com/search.
    config.vm.box = "ubuntu/trusty64"

    # Enable provisioning with a shell script. Additional provisioners such as
    # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
    # documentation for more information about their specific syntax and use.
    # config.vm.provi sion "shell", inline: <<-SHELL
    #   sudo apt-get update
    #   sudo apt-get install -y apache2
    # SHELL

    config.vm.provision :shell, path: "bootstrap.sh"

  end
  config.vm.define "ubuntu-16" do |web|

    # Every Vagrant development environment requires a box. You can search for
    # boxes at https://atlas.hashicorp.com/search.
    config.vm.box = "ubuntu/xenial64"

    # Enable provisioning with a shell script. Additional provisioners such as
    # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
    # documentation for more information about their specific syntax and use.
    # config.vm.provi sion "shell", inline: <<-SHELL
    #   sudo apt-get update
    #   sudo apt-get install -y apache2
    # SHELL

    config.vm.provision :shell, path: "bootstrap.sh"

  end

  # config.vm.define "debian" do |db|

  #   # Every Vagrant development environment requires a box. You can search for
  #   # boxes at https://atlas.hashicorp.com/search.
  #   config.vm.box = "debian/wheezy64"

  #   # Enable provisioning with a shell script. Additional provisioners such as
  #   # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  #   # documentation for more information about their specific syntax and use.
  #   # config.vm.provi sion "shell", inline: <<-SHELL
  #   #   sudo apt-get update
  #   #   sudo apt-get install -y apache2
  #   # SHELL

  #   config.vm.provision :shell, path: "bootstrap.sh"

  # end

end
