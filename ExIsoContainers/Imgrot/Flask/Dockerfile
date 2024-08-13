# 使用官方 Python 运行时作为父镜像
FROM python:3.10-slim
RUN apt-get update && apt-get install -y numactl util-linux
RUN pip install Flask redis requests gunicorn gevent
# 设置工作目录
WORKDIR /usr/src/app

# 将当前目录内容复制到位于 /usr/src/app 的容器中
COPY . .

# 安装任何需要的包

# 运行 Python 脚本时的命令
#CMD ["gunicorn", "-w", "6", "-b", "0.0.0.0:12346", "Flask:app"]
#CMD ["sh", "-c", "numactl --cpunodebind=1 --membind=1 taskset -c 24-47 gunicorn -w 6 -b 0.0.0.0:12346 Flask:app"]
CMD ["python3", "Flask.py"]