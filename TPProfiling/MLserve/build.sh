#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t mlsex:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag mlsex:latest yzzhangllm/mlsex:latest
sudo docker push yzzhangllm/mlsex:latest
#echo 'finished, please trasfer the tar file to Vms and load them'