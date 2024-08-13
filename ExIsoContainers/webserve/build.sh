#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t webex:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag webex:latest yzzhangllm/webex:latest
sudo docker push yzzhangllm/webex:latest
#echo 'finished, please trasfer the tar file to Vms and load them'