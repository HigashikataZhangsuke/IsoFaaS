#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t matex:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag matex:latest yzzhangllm/matex:latest
sudo docker push yzzhangllm/matex:latest
#echo 'finished, please trasfer the tar file to Vms and load them'