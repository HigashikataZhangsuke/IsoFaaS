#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t share:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag share:latest yzzhangllm/share:latest
sudo docker push yzzhangllm/share:latest
#echo 'finished, please trasfer the tar file to Vms and load them'