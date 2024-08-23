#!/bin/bash
n=$1

for ((i=0; i<n; i++))
do
  # 使用 taskset 指定 CPU 运行 Python 脚本
  numactl --membind=0 --cpunodebind=0 taskset -c $i python3 ./ROT.py &
  echo "Started on CPU $i"
done

# 等待所有后台任务完成
wait
echo "All instances of MAT.py have completed."