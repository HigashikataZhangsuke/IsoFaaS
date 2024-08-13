#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t flaskres:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag flaskres:latest yzzhangllm/flaskres:latest
sudo docker push yzzhangllm/flaskres:latest
#echo 'finished, please trasfer the tar file to Vms and load them'