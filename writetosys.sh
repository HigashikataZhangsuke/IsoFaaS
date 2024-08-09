#!/bin/bash

# delete containerd then copy， then restart
sudo modprobe br_netfilter
sudo sysctl net.bridge.bridge-nf-call-iptables=1
echo "net.bridge.bridge-nf-call-iptables=1" | sudo tee -a /etc/sysctl.conf
echo "br_netfilter" | sudo tee /etc/modules-load.d/br_netfilter.conf
sudo sysctl -p /etc/sysctl.conf
sudo systemctl restart containerd
#sudo groupadd docker
sudo systemctl restart docker
echo 'finished patch'


