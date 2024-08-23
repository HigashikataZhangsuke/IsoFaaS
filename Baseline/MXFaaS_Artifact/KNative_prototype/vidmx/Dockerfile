FROM python:3.10-slim


RUN apt-get update && apt-get install -y libpython3.10
RUN apt-get update && apt-get install -y libnuma1 libnuma-dev
RUN apt-get update && apt-get install -y numactl
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx
RUN pip install psutil redis numpy opencv-python py-libnuma

RUN mkdir -p /pythonAction
COPY ./vid /pythonAction/vid
ADD runner.py /pythonAction/
ADD app.py /pythonAction/
ADD dnld_blob.py /pythonAction/
ENV LD_LIBRARY_PATH /usr/lib/x86_64-linux-gnu/:/pythonAction:$LD_LIBRARY_PATH

WORKDIR /pythonAction

CMD ["numactl", "--cpunodebind=0", "--membind=0", "python3", "-u", "runner.py"]
