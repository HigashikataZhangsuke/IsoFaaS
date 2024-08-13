#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t rotex:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag rotex:latest yzzhangllm/rotex:latest
sudo docker push yzzhangllm/rotex:latest
#echo 'finished, please trasfer the tar file to Vms and load them'