import time
import uuid
import asyncio
from multiprocessing import Process
import aiohttp
import numpy as np
import redis
from apscheduler.schedulers.background import BackgroundScheduler

broker_url = "http://broker-ingress.knative-eventing.svc.cluster.local/default/default"

#function_list = ["alu","mlt","mat","vid","rot","mls","web","pyae"]
function_list = ["alu","mlt","mat","vid"]

async def fetch(session, url, json_data, headers):
    async with session.post(url, json=json_data, headers=headers) as response:
        return await response.text()


async def continuous_request(url, function_times, headers_template,funcname):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for idx, func_time in enumerate(function_times):
            #func_name = function_list[idx % len(function_list)]#"web" 
            func_name = funcname
            json_data = {
                "FuncName": func_name,
                "ArrivalTime": time.time()
            }
            headers = headers_template.copy()
            headers["Ce-Type"] = f"{func_name}msg"
            while time.time() < func_time:
                await asyncio.sleep(0.01)
            task = asyncio.create_task(fetch(session, url, json_data, headers))
            tasks.append(task)
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses


async def run_async_tasks(function_times,funcname):
    headers_template = {
        "Ce-Id": str(uuid.uuid4()),
        "Ce-Specversion": "1.0",
        "Ce-Source": "/source/curlpod",
        "Content-Type": "application/json"
    }
    responses = await continuous_request(broker_url, function_times, headers_template,funcname)


def run_in_process(function_times,funcname):
    asyncio.run(run_async_tasks(function_times,funcname))


def generate_even_arrival_times(rate, duration):
    interval = 1 / rate
    times = [i * interval for i in range(int(duration * rate))]
    return times


if __name__ == '__main__':
    #load = 200 # 事件/秒
    duration = 900  # 持续时间为20秒
    loadalu = 70
    loadmlt = 1
    loadmat = 40
    loadvid = 5
    loadmls = 80
    loadpyae= 5
    loadrot = 6
    loadweb = 5
    function_timesalu = generate_even_arrival_times(loadalu, duration)
    function_timesmlt = generate_even_arrival_times(loadmlt, duration)
    function_timesmat = generate_even_arrival_times(loadmat, duration)
    function_timesvid = generate_even_arrival_times(loadvid, duration)
    function_timesmls = generate_even_arrival_times(loadmls, duration)
    function_timespyae = generate_even_arrival_times(loadpyae, duration)
    function_timesrot= generate_even_arrival_times(loadrot, duration)
    function_timesweb = generate_even_arrival_times(loadweb, duration)
    processes = []
    scheduler = BackgroundScheduler()
    RedisClusterRateClient = redis.Redis(host='clsrt.default.svc.cluster.local', port=6379, decode_responses=True)

    start_time = time.time()
    abs_times = {}
    for funcs in function_list:
        abs_times[funcs] = []
    abs_times['alu'] = [start_time + t for t in function_timesalu]
    abs_times['mlt'] = [start_time + t for t in function_timesmlt]
    abs_times['mat'] = [start_time + t for t in function_timesmat]
    abs_times['vid'] = [start_time + t for t in function_timesvid]
    abs_times['mls'] = [start_time + t for t in function_timesmls]
    abs_times['pyae'] = [start_time + t for t in function_timespyae]
    abs_times['rot'] = [start_time + t for t in function_timesrot]
    abs_times['web'] = [start_time + t for t in function_timesweb]
    #for i in range(2):
    #    p = Process(target=run_in_process, args=(abs_times,))
    #    processes.append(p)
    #    p.start()
    for funcs in function_list:
        p = Process(target=run_in_process, args=(abs_times[funcs],funcs,))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()
