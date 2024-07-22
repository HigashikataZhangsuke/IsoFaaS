#The Fake Invoker which will working on give instructions for testing. This is the main control logic parts.
#Also, Testing applying the MBA/CAT here.

import json
import redis
import logging
import time
import random

RedisMessageClient = redis.Redis(host='invokermessagesvc.default.svc.cluster.local', port=6379, decode_responses=True)
RedisMetricClient = redis.Redis(host='aludatasvc.default.svc.cluster.local', port=6379, db=1,decode_responses=True)

ChName = 'ShareVio'
#Give the correct function List
time.sleep(2)
CPUMASK = {
    'AliveList': ['alu']
}
RedisMessageClient.publish('UpdateChannel',json.dumps(CPUMASK))

time.sleep(5)
#Print the Perf metrics Then.
# for i in range(10):
#     Perf =RedisMetricClient.blpop(ChName,5)
#     print(Perf)
#     if Perf:
#         _, dict = Perf
#         if dict:
#             dictjs = json.loads(dict)
#             print(dictjs,flush=True)
#     time.sleep(3)
#Shutdown the sh part finally
print('Shutting down',flush=True)
CPUMASK = {
    'shutdown': 1
}
RedisMessageClient.publish('UpdateChannel',json.dumps(CPUMASK))