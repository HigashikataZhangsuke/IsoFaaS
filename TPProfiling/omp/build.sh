#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t ompex:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag ompex:latest yzzhangllm/ompex:latest
sudo docker push yzzhangllm/ompex:latest
#echo 'finished, please trasfer the tar file to Vms and load them'