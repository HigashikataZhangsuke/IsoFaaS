#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t flaskmlt:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag flaskmlt:latest yzzhangllm/flaskmlt:latest
sudo docker push yzzhangllm/flaskmlt:latest
#echo 'finished, please trasfer the tar file to Vms and load them'