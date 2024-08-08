#Still use the pub-sub method to finish.
#The thing is that, here we shall use async way to update. since the subscriber will be busy.
#Also, the last thing is to remember to provide some sign(lock) for ya since you never want to tune resource allocation
#when you are already working on this!!!.
#Another thing is to think about when and where to do the second level of pubsub. Like in your worker process, or ?
#This is pretty important since you are trying to use a sync mech for sec level pubsub
import uuid
#Alright I think we got it.
#Assume Redis DB could provide more than 16 DB. How to do this please check the GPT.
#Put your performance curve here.
import redis
import time
import psutil
import multiprocessing as mp
import os
import json
import threading
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
import math
import copy
import Exmanage
import Applymba
import Boundcomp
import Shmanage
import logging
import random
def setup_logging(process_id):
    # 设置日志格式
    # Later just need to use the kubectl cp to get them.
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    currtime = time.time()
    # 创建一个日志处理器，将日志输出到文件. Add time since there is a possibility that the process with same ID spawns.
    log_filename = f'invokerprocess_{process_id}+{currtime}.log'
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    # 创建一个日志记录器
    logger = logging.getLogger(str(process_id))
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    return logger

class LListenerSign:
    def __init__(self):
        self.local_sign = True
    def signstop(self):
        self.local_sign = False
    def signstart(self):
        self.local_sign = True
#Updating/Sh globlo policy maker are all background tasks.

def LListener(RedisClusterRateClient,ArrivalRateDict, CurrMaskDict, AllCPUList,ID,Bound,Clusterpolicy,ProfilingDataTp,ProflingDataConsum,Redisflaskclient,RedisExclient,loghld):
    pubsub = RedisClusterRateClient.pubsub()
    pubsub.subscribe('RateChannel')
    #Init related parts:
    for i in range(23):
        AllCPUList.append(1)
    FuncList = ["alu", "omp", "pyae", "che", "res", "rot", "mls", "mlt", "vid", "web"]
    for func in FuncList:
        ArrivalRateDict[func] = 0
        CurrMaskDict[func] = [0]*23
        Bound[func] = 23
        Clusterpolicy[func] = "KeepOrGC"

    while True:
        #everytime, you received the new rate dict for the global part, you need to do another round of profiling and get new mask
        messagelist = pubsub.listen()
        if messagelist:
            # You got a message
            for message in messagelist:
                if message['type'] == 'message':
                    # You got a message passing data
                    RateDict = json.loads(message['data'])
                    # For the shutdown message, we simply set the CPUMASK to all zero(If we still keep the container alive could live later, Currently shut down)
                    if ID in RateDict:
                        #Only deal with ID align our.when init, we send the ID to the cluster at first.
                        #Just do the new mask assign all the time? should so. only do this for functions with rate changed.
                        NewArrDict = RateDict[ID]
                        loghld.info(f"This interval ends at {time.time()} and with Mask {CurrMaskDict}")
                        for func in NewArrDict:
                            #Only change when have significant difference.
                            if NewArrDict[func] > 1.2*ArrivalRateDict[func]:
                                Exmanage.GetNewMask(CurrMaskDict,func,"ScaleUp",AllCPUList,NewArrDict,ProfilingDataTp,ProflingDataConsum,Bound,Clusterpolicy)

                            elif NewArrDict[func] < 0.8*ArrivalRateDict[func]:
                                Exmanage.GetNewMask(CurrMaskDict, func, "ScaleDown", AllCPUList, NewArrDict,ProfilingDataTp, ProflingDataConsum, Bound, Clusterpolicy)
                            else:
                                pass
                            ArrivalRateDict[func] = NewArrDict[func]
                        normal_dict = copy.deepcopy(CurrMaskDict)
                        RedisExclient.publish('UpdateChannel',json.dumps(normal_dict))
                        Applymba.DynamicAllocation(ProflingDataConsum,CurrMaskDict)
                        Applymba.DynamicLinkcore(CurrMaskDict)
                        Shmanage.sendratio(NewArrDict,ProfilingDataTp,CurrMaskDict,Redisflaskclient)
        pubsub.close()

if __name__ == '__main__':
    AffinityId = random.randint(24, 47)
    os.sched_setaffinity(0, {AffinityId})
    ProfilingDataTp = {}
    ProflingDataConsum = {}
    ProfilingLatency = {}
    #This will be the same
    redis_host = ''  # 替换为实际的节点IP,after starting all node and services.
    RedisClusterRateClient = redis.Redis(host=redis_host, port=,decode_responses=True)
    Redisflaskclient = redis.Redis(host=redis_host, port=,decode_responses=True)
    RedisMessageClient = redis.Redis(host=redis_host, port=,decode_responses=True)
    #Init variables and then Start The thread and the subprocess.
    manager = mp.Manager()
    CurrMaskDict = manager.dict()
    ID = uuid.uuid4()
    #A dict, stores the resource allocation results for alive functions in this node.
    AllCPUList = manager.list()
    Bound = manager.dict()
    Clusterpolicy = manager.dict()
    ArrivalRateDict = manager.dict()
    Loghld = setup_logging(os.getpid())
    nlp = mp.Process(target=LListener,args = (RedisClusterRateClient,ArrivalRateDict, CurrMaskDict, AllCPUList,ID,Bound,Clusterpolicy,ProfilingDataTp,ProflingDataConsum,Redisflaskclient,RedisMessageClient,Loghld,))
    nlp.start()
    nlp.join()
