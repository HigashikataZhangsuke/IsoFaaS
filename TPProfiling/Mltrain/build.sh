#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t mltex:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag mltex:latest yzzhangllm/mltex:latest
sudo docker push yzzhangllm/mltex:latest
#echo 'finished, please trasfer the tar file to Vms and load them'