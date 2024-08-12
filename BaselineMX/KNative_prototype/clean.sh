#!/bin/bash

# Step 1: 删除所有 Knative 服务
echo "删除所有 Knative 服务..."
services=$(kn service list --output json | jq -r '.items[].metadata.name')

if [ -z "$services" ]; then
  echo "没有找到 Knative 服务。"
else
  for service in $services; do
    echo "正在删除服务: $service"
    kubectl delete ksvc $service --force
  done
fi

# Step 2: 强制停止 default 命名空间下的所有运行的 Pods
echo "强制停止 default 命名空间下的所有运行的 Pods..."

pods=$(kubectl get pods -n default --output json | jq -r '.items[].metadata.name')

if [ -z "$pods" ]; then
  echo "default 命名空间中没有运行的 Pods。"
else
  for pod in $pods; do
    echo "正在删除 Pod: $pod"
    kubectl delete pod $pod -n default --force --grace-period=0
  done
fi

echo "操作完成。"

