# 使用官方 Python 运行时作为基础镜像
FROM python:3.10-slim AS builder

# 设置工作目录
WORKDIR /usr/src/app

# 安装系统依赖
RUN apt-get update && apt-get install -y \ 
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*  # 清理缓存文件以减少镜像体积

# 复制 requirements.txt 并安装 Python 依赖
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码到容器中
COPY . .

# 创建结果目录
RUN mkdir results

# 使用更小的基础镜像进行最终构建
FROM python:3.10-slim AS final

WORKDIR /usr/src/app

# 从构建镜像复制已安装的 Python 依赖和代码
COPY --from=builder /usr/src/app /usr/src/app
COPY --from=builder /usr/local/lib/python3.10 /usr/local/lib/python3.10

# 运行 Python 脚本时的命令
CMD ["python", "./IsoContainerExProcess.py"]
