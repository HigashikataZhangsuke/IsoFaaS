#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t flaskimg:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag flaskimg:latest yzzhangllm/flaskimg:latest
sudo docker push yzzhangllm/flaskimg:latest
#echo 'finished, please trasfer the tar file to Vms and load them'