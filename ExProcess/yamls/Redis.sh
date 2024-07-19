#!/bin/bash

files=("RedisData.yaml" "RedisSh.yaml" "RedisMessage.yaml")

# 顺序启动每个Redis实例
for file in "${files[@]}"; do
    echo "Starting $file..."
    kubectl apply -f $file
done
Svcs=("SvcData.yaml" "SvcSh.yaml" "SvcMessage.yaml" )

for file in "${Svcs[@]}"; do
    echo "Starting $file..."
    kubectl apply -f $file
done
echo "All services started successfully."