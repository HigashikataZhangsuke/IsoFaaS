#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t flaskweb:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag flaskweb:latest yzzhangllm/flaskweb:latest
sudo docker push yzzhangllm/flaskweb:latest
#echo 'finished, please trasfer the tar file to Vms and load them'