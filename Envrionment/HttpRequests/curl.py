import time
import uuid
import asyncio
from multiprocessing import Process
import aiohttp

# 有多少个model就define多少个send。
broker_url = "http://broker-ingress.knative-eventing.svc.cluster.local/default/default"

function_list = ["alu", "omp", "pyae", "che", "res", "rot", "mls", "mlt", "vid", "web"]

async def fetch(session, url, json_data, headers):
    async with session.post(url, json=json_data, headers=headers) as response:
        return await response.text()

async def continuous_request(url, function_times, headers_template):
    async with aiohttp.ClientSession() as session:
        tasks = []  # 用于收集所有任务
        for idx, func_time in enumerate(function_times):
            func_name = function_list[idx % len(function_list)]
            json_data = {
                "FunctionName": func_name,
                "ArrivalTime": time.time()
            }
            headers = headers_template.copy()
            headers["Ce-Type"] = f"{func_name}msg"
            while time.time() < func_time:
                await asyncio.sleep(0.01)  # 等待直到指定时间
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

if __name__ == '__main__':
    processes = []
    #interval = 2000  # Assume this is some meaningful interval
    # Sample request times for demonstration, in real scenario replace with actual times
    function_times = [time.time() + i for i in range(0, 20, 20)]
    for i in range(6):
        p = Process(target=run_in_process, args=(function_times,))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()
