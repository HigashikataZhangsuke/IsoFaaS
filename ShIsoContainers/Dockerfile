# 使用官方 Python 运行时作为父镜像
FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx

RUN cp cython_omp.cpython-310-x86_64-linux-gnu.so $(python -c "import site; print(site.getsitepackages()[0])")

RUN pip install redis psutil numpy chameleon six pillow torch torchvision pandas scikit-learn joblib pyaes opencv
# 设置工作目录
WORKDIR /usr/src/app
RUN mkdir results
# 将当前目录内容复制到位于 /usr/src/app 的容器中
COPY . .

# 运行 Python 脚本时的命令
CMD ["python", "./IsoContainerSh.py"]
