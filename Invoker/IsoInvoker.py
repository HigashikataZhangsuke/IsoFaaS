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

def LListener(RedisClusterRateClient,ArrivalRateDict, CurrMaskDict, AllCPUList,ID,Bound,Clusterpolicy,ProfilingDataTp,ProflingDataConsum,RedisMessageClient,loghld):
    pubsub = RedisClusterRateClient.pubsub()
    pubsub.subscribe('RateChannel')
    #Init related parts:
    for i in range(23):
        AllCPUList.append(1)
    AllCPUList[6] = 0
    #FuncList = ["alu", "omp", "pyae", "che", "res", "rot", "mls", "mlt", "vid", "web"]
    FuncList = ["alu", "mlt"]
    for func in FuncList:
        #ArrivalRateDict[func] = 0.00
        CurrMaskDict[func] = [0]*23
        templist = CurrMaskDict[func]
        #templist[6] = 1
        CurrMaskDict[func] = templist
        Bound[func] = 23
        Clusterpolicy[func] = "KeepOrGC"
        Applymba.StaticAllocation(ProflingDataConsum,FuncList)
        print("start "+str(CurrMaskDict)+" "+ str(time.time()),flush=True)
    NewArrDict = {}
    while True:
        #everytime, you received the new rate dict for the global part, you need to do another round of profiling and get new mask
        messagelist = pubsub.listen()
        if messagelist:
            # You got a message
            #print("got msg",flush=True)
            for message in messagelist:
                if message['type'] == 'message':
                    # You got a message passing data
                    #print(message, flush=True)
                    #RateDict = json.loads(message['data'])
                    Rate = float(message['data'])
                    #print("Rate is " + str(Rate),flush = True)
                    #NewArrDict = copy.deepcopy(ArrivalRateDict)
                    for func in FuncList:
                        NewArrDict[func] = Rate
                    #print(NewArrDict)
                    # For the shutdown message, we simply set the CPUMASK to all zero(If we still keep the container alive could live later, Currently shut down)
                    #if ID in RateDict:
                        #Only deal with ID align our.when init, we send the ID to the cluster at first.
                        #Just do the new mask assign all the time? should so. only do this for functions with rate changed.
                    #    NewArrDict = RateDict[ID]
                    #    loghld.info(f"This interval ends at {time.time()} and with Mask {CurrMaskDict}")
                    for func in NewArrDict:
                        #print(NewArrDict[func],flush=True)
                        #print(ProfilingDataTp[func][sum(CurrMaskDict[func])],flush=True)
                    #        #Only change when have significant difference.
                            #Here not correct. should change if level change.
                        loghld.info(f"This interval ends at {time.time()} and with Mask {CurrMaskDict}")
                        if NewArrDict[func] > ProfilingDataTp[func][sum(CurrMaskDict[func])]:
                            #print("trigger up",flush = True)
                            Exmanage.GetNewMask(CurrMaskDict,func,"ScaleUp",AllCPUList,NewArrDict,ProfilingDataTp,ProflingDataConsum,Bound,Clusterpolicy)
                        elif NewArrDict[func] < ProfilingDataTp[func][sum(CurrMaskDict[func])]:
                            #print("trigger down", flush=True)
                            Exmanage.GetNewMask(CurrMaskDict, func, "ScaleDown", AllCPUList, NewArrDict,ProfilingDataTp, ProflingDataConsum, Bound, Clusterpolicy)
                        else:
                            pass
                    #ArrivalRateDict['alu'] = NewArrDict['alu']
                    normal_dict = copy.deepcopy(CurrMaskDict)
                    print("Now "+str(CurrMaskDict)+" "+ str(time.time()),flush=True)
                    RedisMessageClient.publish('UpdateChannel',json.dumps(normal_dict))
                    if "omp" in FuncList or "vid" in FuncList or "rot" in FuncList or "mls" in FuncList or "mlt" in FuncList:
                        #Add function check to these two function later.
                        Applymba.DynamicAllocation(ProflingDataConsum,CurrMaskDict)
                        Applymba.DynamicLinkcore(CurrMaskDict,FuncList)
                    Shmanage.sendratio(NewArrDict,ProfilingDataTp,CurrMaskDict,RedisMessageClient,FuncList)
        pubsub.close()

if __name__ == '__main__':
    AffinityId = random.randint(24, 47)
    os.sched_setaffinity(0, {AffinityId})
    ProfilingDataTp = {'alu':[0,91.955, 177.1163, 262.2776, 347.4389, 432.6002, 517.7615, 602.9227999999999, 688.0840999999999, 773.2453999999999, 858.4066999999999, 943.5679999999999, 1028.7293, 1113.8906, 1199.0519, 1284.2132, 1369.3745, 1454.5357999999999, 1539.6970999999999, 1624.8583999999998, 1710.0196999999998, 1795.1809999999998, 1880.3422999999998]
                       ,'mlt':[0,91.955, 177.1163, 262.2776, 347.4389, 432.6002, 517.7615, 602.9227999999999, 688.0840999999999, 773.2453999999999, 858.4066999999999, 943.5679999999999, 1028.7293, 1113.8906, 1199.0519, 1284.2132, 1369.3745, 1454.5357999999999, 1539.6970999999999, 1624.8583999999998, 1710.0196999999998, 1795.1809999999998, 1880.3422999999998]
                       }
    ProflingDataConsum = {'alu':[1,5,1],
                        'omp':[1,6200,1],
                        "pyae":[1,15,1],
    "che":[1,2600,1], "res":[1,1000,1], "rot":[1,500,1], "mls":[1,4000,1], "mlt":[1,5,1], "vid":[1,2000,1], "web":[1,30,1]}

    ProfilingLatency = {'alu':0.0111907,"pyae":0.28206,"che":5.42909, "res":0.8005, "rot":0.7840, "mls":0.437876, "mlt":7.0979 , "vid":1.348898, "web":0.30621425,"omp":4.141488}
    #This will be the same
    redis_host = '172.31.22.224'  # 替换为实际的节点IP,after starting all node and services.
    RedisClusterRateClient = redis.Redis(host=redis_host, port=32526,decode_responses=True)
    RedisMessageClient = redis.Redis(host=redis_host, port=30527,decode_responses=True)
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
    nlp = mp.Process(target=LListener,args = (RedisClusterRateClient,ArrivalRateDict, CurrMaskDict, AllCPUList,ID,Bound,Clusterpolicy,ProfilingDataTp,ProflingDataConsum,RedisMessageClient,Loghld,))
    nlp.start()
    nlp.join()
