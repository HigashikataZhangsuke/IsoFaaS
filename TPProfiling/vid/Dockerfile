# 使用官方 Python 运行时作为父镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /usr/src/app
RUN apt-get update && apt-get install -y \ 
    libglib2.0-0 \    
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx

# 安装任何需要的包
RUN pip install psutil redis numpy opencv-python
# 将当前目录内容复制到位于 /usr/src/app 的容器中
COPY . .

# 安装任何需要的包


# 运行 Python 脚本时的命令
CMD ["python", "./IsoContainerExProcess.py"]
