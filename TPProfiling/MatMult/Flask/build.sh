#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t flaskmat:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag flaskmat:latest yzzhangllm/flaskmat:latest
sudo docker push yzzhangllm/flaskmat:latest
#echo 'finished, please trasfer the tar file to Vms and load them'