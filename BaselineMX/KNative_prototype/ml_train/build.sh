#!/bin/bash

# 构建镜像
sudo docker build -t yzzhangllm/mltmx:latest .

# 推送镜像
sudo docker push yzzhangllm/mltmx:latest
