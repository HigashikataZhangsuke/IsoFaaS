import subprocess
import numpy as np
import time
import requests
import threading
from statistics import mean, median
import logging

def getUrlByFuncName(funcName):
    try:
        output = subprocess.check_output("kn service describe " + funcName + " -vvv", shell=True).decode("utf-8")
    except Exception as e:
        print("Error in kn service describe == " + str(e))
        return None
    lines = output.splitlines()
    for line in lines:
        if "URL:"  in line:
            url = line.split()[1]
            return url

def send_request(service_url, service_name):
    t1 = time.time()
    response = requests.post(service_url, json={"name": "test"})
    t2 = time.time()
    times[service_name].append(t2 - t1)
    timesend[service_name].append(t2)
    timestart[service_name].append(t1)

def request_scheduler(duration, rate):
    np.random.seed(100)
    beta = 1.0 / rate
    current_time = 0
    request_count = 0
    while current_time < duration:
        interval = np.random.exponential(scale=beta)
        current_time += interval
        if current_time < duration:
            request_count += 1
            yield current_time, request_count

def handle_request(next_time, count):
    sleep_time = next_time - time.time()
    if sleep_time > 0:
        time.sleep(sleep_time)
    selected_service = "vid" if count % 4 == 0 else "mls"
    if selected_service in service_urls:
        send_request(service_urls[selected_service], selected_service)


def main_handler():
    duration = 5
    rate = 5
    threads = []
    for next_time, count in request_scheduler(duration, rate):
        thread = threading.Thread(target=handle_request, args=(next_time, count,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

logging.basicConfig(filename='requests.log', level=logging.INFO, format='%(asctime)s %(message)s')
output = subprocess.check_output("kn service list", shell=True).decode("utf-8")
lines = output.splitlines()
service_urls = {}
serviceNames = []
for line in lines[1:]:  # 忽略第一行表头
    serviceName = line.split()[0]
    service_urls[serviceName] = getUrlByFuncName(serviceName)
times = {service: [] for service in service_urls.keys()}
timesend = {service: [] for service in service_urls.keys()}
timestart = {service: [] for service in service_urls.keys()}
if __name__ == '__main__':
    main_handler()
    for service, service_url in service_urls.items():
        if times.get(service):
            logging.info("=====================" + service+ "=====================")
            logging.info(f"Start at {timestart.get(service)} End at {timesend.get(service)}, and deal with them used {times.get(service)}")