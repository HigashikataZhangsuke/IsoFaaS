#!/bin/bash

# delete containerd then copy， then restart
sudo modprobe br_netfilter
sudo sysctl net.bridge.bridge-nf-call-iptables=1
sudo systemctl restart containerd
sudo groupadd docker
sudo systemctl restart docker
echo 'finished patch'


