# import numpy as np
# import time
# from collections import Counter
#
#
# def generate_poisson_arrival_times(rate, duration, seed=100):
#     np.random.seed(seed)  # 设置随机种子以保持结果的一致性
#     times = []
#     current_time = 0
#     while current_time < duration:
#         # 生成下一个事件的时间间隔
#         interval = np.random.exponential(1 / rate)
#         current_time += interval
#         if current_time < duration:
#             times.append(current_time)
#     return times
#
#
# def calculate_rates_per_tenth_second(times, start_time, duration):
#     # 将时间戳转换为从开始时间算起的相对十分之一秒数
#     relative_tenths = [int((time - start_time)) for time in times]
#     # 计算每十分之一秒的事件数量
#     count_per_tenth = Counter(relative_tenths)
#     # 创建结果列表，包含每十分之一秒的事件数量
#     rates_per_tenth_second = [count_per_tenth.get(tenth, 0) for tenth in range(int(duration))]
#     return rates_per_tenth_second
#
#
# if __name__ == '__main__':
#     load = 400  # 事件/秒
#     duration = 20  # 持续时间为20秒
#     start_time = time.time()
#     # 生成事件到达时间
#     function_times = generate_poisson_arrival_times(load, duration)
#     # 计算这些事件时间相对于起始时间的绝对时间
#     function_times_adjusted = [start_time + t for t in function_times]
#
#     # 计算每0.1秒的事件速率
#     rates_per_tenth_second = calculate_rates_per_tenth_second(function_times_adjusted, start_time, duration)
#     #rates_per_second = [rate * 10 for rate in rates_per_tenth_second]
#     # 打印每0.1秒的速率
#     print("Rates per 0.1 second:", rates_per_tenth_second)
import time

# stack = []
# for i in range(1,23):
#     stack.append(6.7937 + 85.1613*i)
# print(len(stack))

import redis

if __name__ == '__main__':
    RPS = [399, 390, 405, 455, 418, 423, 393, 380, 388, 380, 398, 381, 414, 417, 384, 358, 404, 411, 417, 417]
    redis_host = '172.31.22.224'  # 替换为实际的节点IP,after starting all node and services.
    RedisClusterRateClient = redis.Redis(host=redis_host, port=32526,decode_responses=True)
    for i in range(len(RPS)):
        RedisClusterRateClient.publish('RateChannel',RPS[i])
        time.sleep(1)
