#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t flaskrot:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag flaskrot:latest yzzhangllm/flaskrot:latest
sudo docker push yzzhangllm/flaskrot:latest
#echo 'finished, please trasfer the tar file to Vms and load them'