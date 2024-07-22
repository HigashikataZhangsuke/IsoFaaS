import threading
import time
import csv
import subprocess
import datetime
import requests
import json
import uuid
from datetime import datetime
#import torch
import random
import os
import base64
import io
from multiprocessing import Process
import random
import string
import aiohttp
import numpy as np
import asyncio
import inspect
#有多少个model就define多少个send。
broker_url = "http://broker-ingress.knative-eventing.svc.cluster.local/default/default"

async def fetch(session, url, json_data, headers):
    async with session.post(url, json=json_data, headers=headers) as response:
        return response.status

async def continuous_request(url, json_data, headers, interval, duration):
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        end_time = start_time + duration
        tasks = []  # 用于收集所有任务
        while time.time() < end_time:
            #print('start send one', flush=True)
            task = asyncio.create_task(fetch(session, url, json_data, headers))
            tasks.append(task)
            await asyncio.sleep(np.random.exponential(1 / interval))  # 控制发送请求的速率

        # 等待所有稳定期间的任务完成
        responses = await asyncio.gather(*tasks, return_exceptions=True)

def alu():
    a = 506678
    b = 765467
    temp = 0
    for i in range(100000):
        if i % 4 == 0:
            temp = a + b
        elif i % 4 == 1:
            temp = a - b
        elif i % 4 == 2:
            temp = a * b
        else:
            temp = a / b
    return temp

async def run_async_tasks(interval):
    input = inspect.getsource(alu)
    random_SLO = 100000000
    json_data = {
        "FuncName": "Alu",
        "FuncString": input,
        "SLO": random_SLO
    }
    headers = {
        "Ce-Id": str(uuid.uuid4()),
        "Ce-Specversion": "1.0",
        "Ce-Type": "your-event-type",
        "Ce-Source": "/source/curlpod",
        "Content-Type": "application/json"
    }
    #interval =1.5 #Lambda = 5
    duration = 200  # 测试持续时间，例如60秒
    requests_sent = await continuous_request(broker_url, json_data, headers, interval, duration)

def run_in_process(interval):
    asyncio.run(run_async_tasks(interval))

if __name__ == '__main__':
    processes = []
    interval = 0.002 #2500 in total
    p0 = Process(target=run_in_process, args=(interval,))
    p1 = Process(target=run_in_process, args=(interval,))
    p2 = Process(target=run_in_process, args=(interval,))
    p3 = Process(target=run_in_process, args=(interval,))
    p4 = Process(target=run_in_process, args=(interval,))
    p5 = Process(target=run_in_process, args=(interval,))
    p0.start()
    p1.start()
    p2.start()
    p3.start()
    p4.start()
    p5.start()


