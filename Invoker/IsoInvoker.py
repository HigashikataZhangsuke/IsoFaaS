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
def setup_logging(process_id):
    # 设置日志格式
    # Later just need to use the kubectl cp to get them.
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    currtime = time.time()
    # 创建一个日志处理器，将日志输出到文件. Add time since there is a possibility that the process with same ID spawns.
    log_filename = f'aluprocess_{process_id}+{currtime}.log'
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


def updator(ID,AliveList,LeftedResource,RedisPublishCannel,UsedResource):
    #also write resource usage here()
    Data = {
        "ID":ID,
        "AliveList":copy.deepcopy(AliveList),
        "LeftedResource":LeftedResource,
        "UsedResource": UsedResource
    }
    RedisPublishCannel.publish('Scheduler',json.dumps(Data))
    RedisPublishCannel.publish('GC', json.dumps(Data))
    #You also need to update your Function's usage here.
    time.sleep(5)

def LListener(RedisClusterRateClient,ArrivalRateDict, CurrMaskDict, AllCPUList,ID,Bound,Clusterpolicy,ProfilingDataTp,ProflingDataConsum):
    pubsub = RedisClusterRateClient.pubsub()
    pubsub.subscribe('RateChannel')
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
                        for func in NewArrDict:
                            #Only change when have significant difference.
                            if NewArrDict[func] > 1.2*ArrivalRateDict[func]:
                                Exmanage.GetNewMask(CurrMaskDict,func,"ScaleUp",AllCPUList,NewArrDict,ProfilingDataTp,ProflingDataConsum,Bound,Clusterpolicy)
                            elif NewArrDict[func] < 0.8*ArrivalRateDict[func]:
                                Exmanage.GetNewMask(CurrMaskDict, func, "ScaleDown", AllCPUList, NewArrDict,ProfilingDataTp, ProflingDataConsum, Bound, Clusterpolicy)
                            else:
                                pass
                            ArrivalRateDict[func] = NewArrDict[func]
                        Applymba.DynamicAllocation(ProflingDataConsum,CurrMaskDict)
                        Applymba.DynamicLinkcore(CurrMaskDict)
        pubsub.close()


if __name__ == '__main__':
    import redis

    # 假设集群节点的一个可达IP是192.168.1.100，NodePort是30007
    # 用节点IP+服务IP。这里你应该先创建他们，然后再invoker里面去查看和连接。但是这个确定能做了。
    redis_host = '172.31.16.166'  # 替换为实际的节点IP
    redis_port = 31849  # NodePort

    r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    # 测试连接
    r.set('test', 'hello')
    print(r.get('test'))

    ProfilingDataTp
    ProflingDataConsum
    ProfilingLatency
    TotalResource

    RedisClusterSvc = redis.Redis(host='clustersvc.default.svc.cluster.local', port=6379,decode_responses=True)
    RedisClusterMetricSvc = redis.Redis(host='clustersvc.default.svc.cluster.local',db=1, port=6379,decode_responses=True)
    RedisMessageClientSh = redis.Redis(host='invokershmessagesvc.default.svc.cluster.local', port=6379,decode_responses=True)
    RedisMessageClientEx = redis.Redis(host='invokermessagesvc.default.svc.cluster.local', port=6379,decode_responses=True)
    RedisMetricClient = redis.Redis(host='invokermetricsservice.default.svc.cluster.local', port=6379, db=0,decode_responses=True)
    RedisPublishChannel = redis.Redis(host='clusterchn.default.svc.cluster.local', port=6379,decode_responses=True)
    #Init variables and then Start The thread and the subprocess.
    ListenerSign = LListenerSign()
    manager = mp.Manager()
    AliveList = manager.list()
    CurrMaskDict = manager.dict()
    ID = uuid.uuid4()
    #A dict, stores the resource allocation results for alive functions in this node.
    ResourceAllocation = manager.dict()
    AllCPUList = manager.list()
    Bound = manager.dict()
    #How to init these mapping lists is a problem. Also need a dict here.
    FunctionLLCMapping = manager.list()
    FunctionMBAMapping = manager.list()
    ArrivalRateDict = manager.dict()
    LeftedResource = manager.dict()
    for i in range(23):
        AllCPUList.append(1)
    ngp = mp.Process(target=Glistener, args=(RedisClusterSvc,RedisClusterMetricSvc,
                                             RedisMessageClientEx,ListenerSign,AliveList,ID,ResourceAllocation,
                                             CurrMaskDict,AllCPUList,FunctionLLCMapping,FunctionMBAMapping,ArrivalRateDict,Bound,LeftedResource,))

    nlp = mp.Process(target=LListener,args = (ListenerSign,RedisMetricClient,ResourceAllocation,ArrivalRateDict,CurrMaskDict,
                                              FunctionLLCMapping,FunctionMBAMapping,AllCPUList,Bound,LeftedResource,))

    nup = mp.Process(target=updator,args=(ID,AliveList,LeftedResource,RedisPublishChannel,))
    ngp.start()
    nlp.start()
    nup.start()
    ngp.join()
    nlp.join()
    nup.join()