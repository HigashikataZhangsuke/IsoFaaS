import time
import uuid
import asyncio
from multiprocessing import Process
import aiohttp
import numpy as np
import json
import redis
from apscheduler.schedulers.background import BackgroundScheduler
# ????model?define???send?
broker_url = "http://broker-ingress.knative-eventing.svc.cluster.local/default/default"
def enforce_activity_window(start_time, end_time, function_times):
    """Filter function times to ensure they are within the activity window."""
    return [t for t in function_times if start_time <= t <= end_time]

#function_list = ["alu", "omp", "pyae", "che", "res", "rot", "mls", "mlt", "vid", "web"]
function_list = ["rot","pyae"]
async def fetch(session, url, json_data, headers):
    async with session.post(url, json=json_data, headers=headers) as response:
        return await response.text()

async def continuous_request(url, function_times, headers_template):
    async with aiohttp.ClientSession() as session:
        tasks = []
        che_counter = 0
        mls_counter = 0
        for idx, func_time in enumerate(function_times):
            if che_counter == 0:
                func_name = "rot"
                che_counter += 1
                mls_counter = 0  # Reset mls counter
            else:
                func_name = "pyae"
                mls_counter += 1
                if mls_counter == 5:
                    che_counter = 0  # Reset che counter

            json_data = {
                "FuncName": func_name,
                "ArrivalTime": time.time()
            }
            headers = headers_template.copy()
            headers["Ce-Type"] = f"{func_name}msg"
            wait_time = func_time - time.time()  # ??????????????
            if wait_time > 0:
                await asyncio.sleep(wait_time)  # ????????
            task = asyncio.create_task(fetch(session, url, json_data, headers))
            tasks.append(task)
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses



async def run_async_tasks(function_times):
    headers_template = {
        "Ce-Id": str(uuid.uuid4()),
        "Ce-Specversion": "1.0",
        "Ce-Source": "/source/curlpod",
        "Content-Type": "application/json"
    }
    responses = await continuous_request(broker_url, function_times, headers_template)
    #print(responses)

def run_in_process(function_times):
    asyncio.run(run_async_tasks(function_times))

def generate_poisson_arrival_times(rate, duration):
    np.random.seed(100)  # ???????????????
    times = []
    current_time = 0
    while current_time < duration:
            # ????????????
        interval = np.random.exponential(1 / rate)
        current_time += interval
        if current_time < duration:
            times.append(current_time)
    return times
clock = 0
#Low Setting 5
RPS =[7, 5, 4, 5,7]
#Medium Setting 30
#RPS = [35, 29, 30, 25, 25,0]
#High Setting 10
#RPS = [12,9,14,6,9]
#High Setting 15
#RPS = [16,19,14,15,12]
#High Setting 60
#RPS = [64,55,56,51,54]
#High Setting 20
#RPS = [21,20,23,19,22]
def sendrate(RedisClusterRateClient):
    global clock
    Ratedict = {"vid":0,"mls":0}
    if clock<len(RPS):
        #Change to dict, since no round robin?
        Ratedict["vid"] = RPS[clock]/5
        Ratedict["mls"] = RPS[clock]/5*4
        RedisClusterRateClient.publish('RateChannel', json.dumps(Ratedict))
        clock +=1

if __name__ == '__main__':
    load = 5  # ??/?, 30, 80 are the next two parts.
    duration = 5  # ?????20?
    # ???????????????????
    function_times = generate_poisson_arrival_times(load, duration)
    processes = []
    scheduler = BackgroundScheduler()
    RedisClusterRateClient = redis.Redis(host='clsrt.default.svc.cluster.local', port=6379, decode_responses=True)
    #interval = 2000  # Assume this is some meaningful interval
    # Sample request times for demonstration, in real scenario replace with actual times
    start_time = time.time()
    end_time = start_time + duration
    abs_times = [start_time + t for t in function_times]
    abs_times = enforce_activity_window(start_time, end_time, abs_times)
    scheduler.add_job(sendrate,'interval',seconds=1,args = (RedisClusterRateClient,))
    scheduler.start()

    for i in range(1):
        p = Process(target=run_in_process, args=(abs_times,))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()
    scheduler.shutdown()