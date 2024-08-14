from collections import defaultdict
import math
import time
import uuid
import asyncio
from multiprocessing import Process
import numpy as np

# 有多少个model就define多少个send。
broker_url = "http://broker-ingress.knative-eventing.svc.cluster.local/default/default"
def enforce_activity_window(start_time, end_time, function_times):
    """Filter function times to ensure they are within the activity window."""
    return [t for t in function_times if start_time <= t <= end_time]

#function_list = ["alu", "omp", "pyae", "che", "res", "rot", "mls", "mlt", "vid", "web"]
function_list = ["che","mls"]
async def fetch(session, url, json_data, headers):
    async with session.post(url, json=json_data, headers=headers) as response:
        return await response.text()

#async def continuous_request(url, function_times, headers_template):
    # async with aiohttp.ClientSession() as session:
    #     tasks = []
    #     for idx, func_time in enumerate(function_times):
    #         func_name = function_list[idx % len(function_list)]
    #         json_data = {
    #             "FuncName": func_name,
    #             "ArrivalTime": time.time()
    #         }
    #         headers = headers_template.copy()
    #         headers["Ce-Type"] = f"{func_name}msg"
    #         wait_time = func_time - time.time()  # 计算当前时间到目标时间的差值
    #         if wait_time > 0:
    #             await asyncio.sleep(wait_time)  # 等待直到指定时间
    #         task = asyncio.create_task(fetch(session, url, json_data, headers))
    #         tasks.append(task)
    #     responses = await asyncio.gather(*tasks, return_exceptions=True)
        #return responses


# async def run_async_tasks(function_times):
#     headers_template = {
#         "Ce-Id": str(uuid.uuid4()),
#         "Ce-Specversion": "1.0",
#         "Ce-Source": "/source/curlpod",
#         "Content-Type": "application/json"
#     }
#     responses = await continuous_request(broker_url, function_times, headers_template)
#     #print(responses)

# def run_in_process(function_times):
#     asyncio.run(run_async_tasks(function_times))

def generate_poisson_arrival_times(rate, duration):
    np.random.seed(100)  # 设置随机种子以保持结果的一致性
    times = []
    current_time = 0
    while current_time < duration:
            # 生成下一个事件的时间间隔
        interval = np.random.exponential(1 / rate)
        current_time += interval
        if current_time < duration:
            times.append(current_time)
    return times
clock = 0

# def sendrate(RedisClusterRateClient):
#     global clock
#     if clock<len(RPS):
#         #Change to dict, since no round robin?
#         RedisClusterRateClient.publish('RateChannel', RPS[clock])
#         clock +=1
def count_requests_by_second(function_times):
    counts = defaultdict(int)
    for time_stamp in function_times:
        # 因为时间戳是绝对时间，我们将其转换为相对于开始时间的秒数
        second = math.floor(time_stamp - start_time)
        counts[second] += 1
    return dict(counts)

if __name__ == '__main__':
    load = 5  # 事件/秒
    duration = 5  # 持续时间为20秒
    # 函数用于生成符合泊松过程的事件到达时间
    function_times = generate_poisson_arrival_times(load, duration)
    processes = []
    #scheduler = BackgroundScheduler()
    #RedisClusterRateClient = redis.Redis(host='clsrt.default.svc.cluster.local', port=6379, decode_responses=True)
    #interval = 2000  # Assume this is some meaningful interval
    # Sample request times for demonstration, in real scenario replace with actual times
    start_time = time.time()
    end_time = start_time + duration
    abs_times = [start_time + t for t in function_times]
    abs_times = enforce_activity_window(start_time, end_time, abs_times)
    #scheduler.add_job(sendrate,'interval',seconds=1,args = (RedisClusterRateClient,))
    #scheduler.start()
    request_counts = count_requests_by_second(abs_times)
    print("Requests per second:", request_counts)
    # for i in range(1):
    #     p = Process(target=run_in_process, args=(abs_times,))
    #     processes.append(p)
    #     p.start()
    #
    # for p in processes:
    #     p.join()
    #scheduler.shutdown()


