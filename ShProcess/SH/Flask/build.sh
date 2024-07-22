#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t flaskshimg:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag flaskshimg:latest yzzhangllm/flaskshimg:latest
sudo docker push yzzhangllm/flaskshimg:latest
#echo 'finished, please trasfer the tar file to Vms and load them'