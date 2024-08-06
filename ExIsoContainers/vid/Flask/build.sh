#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t flaskvid:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag flaskvid:latest yzzhangllm/flaskvid:latest
sudo docker push yzzhangllm/flaskvid:latest
#echo 'finished, please trasfer the tar file to Vms and load them'