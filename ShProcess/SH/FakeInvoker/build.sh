#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t fakeivkshimg:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag fakeivkshimg:latest yzzhangllm/fakeivkshimg:latest
sudo docker push yzzhangllm/fakeivkshimg:latest
#echo 'finished, please trasfer the tar file to Vms and load them'