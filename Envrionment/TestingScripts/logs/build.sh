#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t aluex:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag aluex:latest yzzhangllm/aluex:latest
sudo docker push yzzhangllm/aluex:latest
