#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t isoshimage:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag isoshimage:latest yzzhangllm/isoshimage:latest
sudo docker push yzzhangllm/isoshimage:latest
#echo 'finished, please trasfer the tar file to Vms and load them'