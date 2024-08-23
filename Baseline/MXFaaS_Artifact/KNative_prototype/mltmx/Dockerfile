FROM python:3.10-slim

RUN pip install psutil numpy redis pandas scikit-learn joblib py-libnuma
RUN apt-get update && apt-get install -y libpython3.10
RUN apt-get update && apt-get install -y libnuma1 libnuma-dev
RUN apt-get update && apt-get install -y numactl

RUN mkdir -p /pythonAction
ADD runner.py /pythonAction/
ADD ./MLT /pythonAction/
ADD app.py /pythonAction/
ADD dnld_blob.py /pythonAction/
ENV LD_LIBRARY_PATH /usr/lib/x86_64-linux-gnu/:/pythonAction:$LD_LIBRARY_PATH

WORKDIR /pythonAction
RUN mkdir results
CMD ["numactl", "--cpunodebind=0", "--membind=0", "python3", "-u", "runner.py"]
