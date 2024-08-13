#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t flaskche:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag flaskche:latest yzzhangllm/flaskche:latest
sudo docker push yzzhangllm/flaskche:latest
#echo 'finished, please trasfer the tar file to Vms and load them'