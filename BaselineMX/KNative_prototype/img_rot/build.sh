#!/bin/bash

# 构建镜像
sudo docker build -t yzzhangllm/rotmx:latest .

# 推送镜像
sudo docker push yzzhangllm/rotmx:latest
