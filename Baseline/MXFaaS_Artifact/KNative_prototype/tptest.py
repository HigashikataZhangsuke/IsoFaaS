import subprocess
import time
import requests
import threading
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

def print_http_response(response):
    print("Status Code:", response.status_code,flush=True)
    print("Headers:", response.headers,flush=True)
    print("Body:", response.text,flush=True)

def send_request(service_url, service_name):
    t1 = time.time()
    response = requests.post(service_url, json={"name": "test"})
    #print_http_response(response)
    t2 = time.time()
    times[service_name].append(t2 - t1)
    timesend[service_name].append(t2)
    timestart[service_name].append(t1)

def request_scheduler(duration, interval=0.2):
    current_time = time.time()
    end_time = current_time + duration
    while current_time < end_time:
        next_time = current_time + interval
        yield next_time
        current_time = next_time

def handle_request(next_time, service_name):
    sleep_time = next_time - time.time()
    if sleep_time > 0:
        time.sleep(sleep_time)
    if service_name in service_urls:
        send_request(service_urls[service_name], service_name)

def main_handler():
    duration = 5  # ?????5?
    service_name = "vid"  # ????????????
    threads = []
    for next_time in request_scheduler(duration):
        thread = threading.Thread(target=handle_request, args=(next_time, service_name,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

logging.basicConfig(filename='requests.log', level=logging.INFO, format='%(asctime)s %(message)s')
output = subprocess.check_output("kn service list", shell=True).decode("utf-8")
lines = output.splitlines()
service_urls = {}
serviceNames = []
for line in lines[1:]:  # ???????
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
