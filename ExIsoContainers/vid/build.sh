#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t videx:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag videx:latest yzzhangllm/videx:latest
sudo docker push yzzhangllm/videx:latest
#echo 'finished, please trasfer the tar file to Vms and load them'