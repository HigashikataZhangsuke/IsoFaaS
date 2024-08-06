#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
sudo docker build -t flaskalu:latest .
#sudo docker save -o curlpod.tar curlpod:latest
sudo docker tag flaskalu:latest yzzhangllm/flaskalu:latest
sudo docker push yzzhangllm/flaskalu:latest
