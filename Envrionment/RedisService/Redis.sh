#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 假设有一个包含函数名称的数组
functionNames=("alu" "omp" "pyae" "che" "res" "rot" "mls" "mlt" "vid" "web")

# 基本文件
files=("RedisSh.yaml" "RedisMessage.yaml")
svcs=("SvcSh.yaml" "SvcMessage.yaml")

# 为每个函数名称添加特定的文件和服务
for name in "${functionNames[@]}"; do
    files+=("RedisEx${name}.yaml")
    svcs+=("Svc${name}.yaml")
done

# 顺序启动每个Redis实例
for file in "${files[@]}"; do
    echo "Starting $file..."
    kubectl apply -f "$DIR/$file"
done

# 顺序启动每个服务
for file in "${svcs[@]}"; do
    echo "Starting $file..."
    kubectl apply -f "$DIR/$file"
done

echo "All services started successfully."
