#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t flaskmls:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag flaskmls:latest yzzhangllm/flaskmls:latest
sudo docker push yzzhangllm/flaskmls:latest
#echo 'finished, please trasfer the tar file to Vms and load them'