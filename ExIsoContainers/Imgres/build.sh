#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t resex:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag resex:latest yzzhangllm/resex:latest
sudo docker push yzzhangllm/resex:latest
#echo 'finished, please trasfer the tar file to Vms and load them'