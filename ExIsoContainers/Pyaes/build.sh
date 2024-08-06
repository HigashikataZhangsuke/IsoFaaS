#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t pyaeex:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag pyaeex:latest yzzhangllm/pyaeex:latest
sudo docker push yzzhangllm/pyaeex:latest
#echo 'finished, please trasfer the tar file to Vms and load them'