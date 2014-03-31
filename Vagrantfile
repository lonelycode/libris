# -*- mode: ruby -*-
# vi: set ft=ruby :
Vagrant::Config.run do |config|
  ## Chose your base box
  config.vm.box = "precise64"

  config.vm.forward_port 80, 8080
  config.vm.forward_port 8000, 8000
  config.vm.forward_port 844, 844
  config.vm.forward_port 27017, 27017


  ## For masterless, mount your salt file root
  config.vm.share_folder "libris", "/libris", "libris"

end
