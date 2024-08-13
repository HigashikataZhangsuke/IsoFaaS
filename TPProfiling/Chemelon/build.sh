#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t cheex:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag cheex:latest yzzhangllm/cheex:latest
sudo docker push yzzhangllm/cheex:latest
#echo 'finished, please trasfer the tar file to Vms and load them'