#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t fakeivkimg:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag fakeivkimg:latest yzzhangllm/fakeivkimg:latest
sudo docker push yzzhangllm/fakeivkimg:latest
#echo 'finished, please trasfer the tar file to Vms and load them'