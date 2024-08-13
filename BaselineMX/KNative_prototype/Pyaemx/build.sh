#!/bin/bash

# 构建镜像
sudo docker build -t yzzhangllm/pyaemx:latest .

# 推送镜像
sudo docker push yzzhangllm/pyaemx:latest
