import asyncio
import aiohttp
import numpy as np
import time
import logging
import subprocess
import docker
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 设置日志记录
logging.basicConfig(filename='requests.log', level=logging.INFO, format='%(asctime)s %(message)s')
services = ["mls", "che"]
service_urls = []  # 存储服务的URL

# 启动Docker容器并获取IP地址
def setup_containers():
    client = docker.DockerClient()
    for service in services:
        output = subprocess.check_output(f"sudo docker run -d --name {service} --cpu-shares=0 --privileged yzzhangllm/{service}mx",
                                         shell=True).decode('utf-8').strip()
        container = client.containers.get(output)
        ip_add = container.attrs['NetworkSettings']['IPAddress']
        print(ip_add,flush=True)
        url = f"http://{ip_add}:9999"
        #print(url,flush=True)
        if 'che'== service:
            service_urls.append(url)
        elif 'mls' == service:
            service_urls.extend([url] * 16)  # 重复16次对应于 'mls'
        #print(service_urls, flush=True)

async def send_request(service_url):
    service_name = service_url.split("/")[2]
    t1 = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.post(service_url, json={"name": "test"}) as response:
            response_text = await response.text()
            t2 = time.time()
            logging.info(f"Sent to {service_name} at {t1}, Received at {t2}")
            return t2 - t1

async def scheduled_requests(service_urls, inter_arrival_times):
    index = 0
    num_services = len(service_urls)
    for delay in inter_arrival_times:
        await asyncio.sleep(delay)  # 等待直到下一个请求的时间
        service_url = service_urls[index % num_services]
        index += 1
        asyncio.create_task(send_request(service_url))

def generate_poisson_arrival_times(rate, duration):
    np.random.seed(100)  # 设置随机种子以保持结果的一致性
    times = []
    current_time = 0
    while current_time < duration:
        interval = np.random.exponential(1 / rate)
        current_time += interval
        if current_time < duration:
            times.append(current_time)
    return times

def EnforceActivityWindow(start_time, end_time, instance_events):
    event_times = [e for e in instance_events if (e > start_time) and (e < end_time)]
    events_iit = []
    try:
        events_iit = [event_times[0]] + [event_times[i] - event_times[i - 1]
                                         for i in range(1, len(event_times))]
    except IndexError:
        pass
    return events_iit

async def main():
    setup_containers()  # 启动容器并获取IP地址
    scheduler = AsyncIOScheduler()
    duration = 5  # 测试的持续时间（秒）
    rate = 5  # 每秒请求数 5,15,30

    inter_arrival_times = generate_poisson_arrival_times(rate, duration)
    inter_arrival_times = EnforceActivityWindow(0, duration, inter_arrival_times)

    scheduler.add_job(scheduled_requests, args=[service_urls, inter_arrival_times])

    scheduler.start()
    try:
        while True:
            await asyncio.sleep(1)  # 保持主循环运行
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        # 在脚本结束时清理容器
        for service in services:
            subprocess.run(f"docker stop {service}", shell=True)
            subprocess.run(f"docker rm {service}", shell=True)

if __name__ == '__main__':
    asyncio.run(main())
