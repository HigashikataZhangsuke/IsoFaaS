#!/bin/bash

# 构建镜像
sudo docker build -t yzzhangllm/webmx:latest .

# 推送镜像
sudo docker push yzzhangllm/webmx:latest
