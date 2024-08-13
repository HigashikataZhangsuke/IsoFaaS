#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t flaskpyae:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag flaskpyae:latest yzzhangllm/flaskpyae:latest
sudo docker push yzzhangllm/flaskpyae:latest
#echo 'finished, please trasfer the tar file to Vms and load them'