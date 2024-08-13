# 使用官方 Python 运行时作为父镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /usr/src/app

# 将当前目录内容复制到位于 /usr/src/app 的容器中
COPY . .

# 安装任何需要的包
RUN pip install psutil numpy redis chameleon six

# 运行 Python 脚本时的命令
CMD ["python", "./IsoContainerExProcess.py"]
