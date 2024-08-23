#!/bin/bash

kubectl delete ksvc --all
kubectl delete pods --all --force
#services=("che" "mls")
#for service in "${services[@]}"; do
#    sudo docker stop "$service"
#    sudo docker rm "$service"
#done
rm -rf *.log
