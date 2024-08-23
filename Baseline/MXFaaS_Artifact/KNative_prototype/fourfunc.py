import subprocess
import numpy as np
import time
import requests
import threading
from statistics import mean, median
import logging

def getUrlByFuncName(funcName):
    try:
        output = subprocess.check_output(f"kn service describe {funcName} -vvv", shell=True).decode("utf-8")
    except Exception as e:
        print(f"Error in kn service describe == {e}")
        return None
    lines = output.splitlines()
    for line in lines:
        if "URL:" in line:
            return line.split()[1]

def send_request(service_url, service_name):
    t1 = time.time()
    response = requests.post(service_url, json={"name": "test"})
    t2 = time.time()
    times[service_name].append(t2 - t1)
    timesend[service_name].append(t2)
    timestart[service_name].append(t1)

def request_scheduler(duration, pattern, repeat):
    np.random.seed(100)
    current_time = 0
    while True:
        for service_name, repetitions in pattern:
            for _ in range(repetitions):
                yield service_name, current_time
                current_time += np.random.exponential(scale=1.0 / repeat)
                if current_time >= duration:
                    return

def handle_request(service_name, next_time):
    sleep_time = next_time - time.time()
    if sleep_time > 0:
        time.sleep(sleep_time)
    if service_name in service_urls:
        send_request(service_urls[service_name], service_name)

def main_handler():
    duration = 5  # Run for 5 seconds
    service_pattern = [("alu", 29), ("pyae", 1), ("web", 1), ("mls", 1)]
    rate = 320  # Approximate requests per second
    threads = []
    for service_name, next_time in request_scheduler(duration, service_pattern, rate):
        thread = threading.Thread(target=handle_request, args=(service_name, next_time))
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
        if times[service]:
            logging.info(f"====================={service}=====================")
            logging.info(f"Start at {timestart[service]}, End at {timesend[service]}, and deal with them used {times[service]}")
