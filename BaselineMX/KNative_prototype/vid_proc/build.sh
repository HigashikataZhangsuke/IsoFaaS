#!/bin/bash

# 构建镜像
sudo docker build -t yzzhangllm/vidmx:latest .

# 推送镜像
sudo docker push yzzhangllm/vidmx:latest
