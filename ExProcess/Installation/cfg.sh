#!/bin/bash

# delete containerd then copy， then restart
sudo rm -rf /etc/containerd/config.toml
sudo mv config.toml /etc/containerd/config.toml
sudo systemctl restart containerd

echo 'finished cfg'

