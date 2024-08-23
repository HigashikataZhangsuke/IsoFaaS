# 第一阶段：构建依赖层
FROM python:3.10-slim as builder

# 创建一个存储依赖的目录
WORKDIR /install

# 安装依赖
RUN pip install --prefix=/install psutil numpy redis

# 第二阶段：构建应用层
FROM python:3.10-slim

# 复制从第一阶段构建的依赖
COPY --from=builder /install /usr/local

# 设置工作目录
WORKDIR /usr/src/app

# 将当前目录内容复制到位于 /usr/src/app 的容器中
COPY . .

# 运行 Python 脚本时的命令
CMD ["python", "./IsoContainerExProcess.py"]
