#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t isoeximage:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag isoeximage:latest yzzhangllm/isoeximage:latest
sudo docker push yzzhangllm/isoeximage:latest
#echo 'finished, please trasfer the tar file to Vms and load them'