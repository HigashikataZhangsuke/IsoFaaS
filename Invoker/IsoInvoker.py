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
    #AllCPUList[6] = 0
    #FuncList = ["alu", "omp", "pyae", "che", "res", "rot", "mls", "mlt", "vid", "web"]
    FuncList = ["vid","mls"]
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
                    Rate = json.loads(message['data'])
                    #print("Rate is " + str(Rate),flush = True)
                    #NewArrDict = copy.deepcopy(ArrivalRateDict)
                    for func in FuncList:
                        NewArrDict[func] = Rate[func]
                    #print(NewArrDict)
                    # For the shutdown message, we simply set the CPUMASK to all zero(If we still keep the container alive could live later, Currently shut down)
                    #if ID in RateDict:
                        #Only deal with ID align our.when init, we send the ID to the cluster at first.
                        #Just do the new mask assign all the time? should so. only do this for functions with rate changed.
                    #    NewArrDict = RateDict[ID]
                    #    loghld.info(f"This interval ends at {time.time()} and with Mask {CurrMaskDict}")
                    #print(NewArrDict,flush=True)
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
                            #if (sum(CurrMaskDict[func])==0):
                              #Still Init
                                #for i in range(23):
                                    
                            #else:
                            Exmanage.GetNewMask(CurrMaskDict, func, "ScaleDown", AllCPUList, NewArrDict,ProfilingDataTp, ProflingDataConsum, Bound, Clusterpolicy)
                        else:
                            pass
                    #ArrivalRateDict['alu'] = NewArrDict['alu']
                    normal_dict = copy.deepcopy(CurrMaskDict)
                    #print("Now "+str(CurrMaskDict)+" "+ str(time.time()),flush=True)
                    RedisMessageClient.publish('UpdateChannel',json.dumps(normal_dict))
                    if "omp" in FuncList or "vid" in FuncList or "rot" in FuncList or "mls" in FuncList or "mlt" in FuncList:
                        #Add function check to these two function later.
                        Applymba.DynamicAllocation(ProflingDataConsum,CurrMaskDict,FuncList)
                        Applymba.DynamicLinkcore(CurrMaskDict,FuncList)
                    Shmanage.sendratio(NewArrDict,ProfilingDataTp,CurrMaskDict,RedisMessageClient,FuncList)
        pubsub.close()

if __name__ == '__main__':
    AffinityId = random.randint(24, 47)
    os.sched_setaffinity(0, {AffinityId})
    ProfilingDataTp = {'alu': [78.2, 155.54, 232.62, 310.84, 387.9, 462.84000000000003, 540.19, 608.96, 689.76, 752.2, 792.6600000000001, 928.92, 978.64, 1043.98, 1137.45, 1171.84, 1200.03, 1311.1326, 1377.5437000000002, 1443.278, 1508.3355000000001, 1572.7161999999998, 1636.4201],
                       'omp': [0.22984568876716, 0.445914890649266, 0.671036120239653, 0.899807724018036, 1.123050609858095, 1.341709005667566, 1.546701550183559, 1.764327241577776, 1.987277366482398, 2.18092529344844, 2.26208601219216, 2.409915099359412, 2.559457727070972, 2.811715772878614, 2.908208235360015, 3.005325126809312, 3.09236152549781, 3.1456760089659483, 3.174241290654615, 3.21698415890748, 3.243448986424752, 3.261553396095324, 3.284613229090782],
                       'vid': [0.68, 1.12, 1.59, 2.092, 2.585, 3.09, 3.535, 3.952, 4.3623, 4.582, 4.8774, 5.178, 5.369, 5.5468, 5.7, 5.8128, 5.949999999999999, 6.102, 6.1655, 6.24, 6.283200000000001, 6.344799999999999, 6.4952],
                       'pyae': [2.728, 5.478, 8.2167, 10.9484, 13.671100000000001, 16.4202, 19.194, 21.92, 24.597, 27.399, 30.15265, 32.88, 35.6018, 38.318, 41.0655, 43.7968, 46.5647, 49.2624, 51.9612, 54.772800000000004, 57.500519999999995, 60.19112, 61.7964],
                       'res': [1.1500279957414, 2.30145988165038, 3.4611640720056003, 4.73120643129724, 5.97408384139075, 7.177215105938879, 8.03014353955751, 9.22904248633408, 10.635850312933322, 11.8550602055053, 12.70092874120576, 13.858386502140359, 14.922511576090692, 16.76436052953382, 17.25661551649785, 18.47223438453648, 19.615609278091842, 21.263851692201417, 22.42693724042566, 23.043452333629403, 24.85032954121515, 26.03154075175896, 26.44357827721542],
                       'rot': [1.19861349274061, 2.37764770664538, 3.5411438526228602, 4.65101217537916, 5.7259307296328, 6.84772152803448, 7.938084651625171, 8.98441991407416, 10.14687095189571, 11.209972820770599, 12.29140376075821, 13.41749500442592, 14.4588003754051, 15.0568854868383, 16.71198688691535, 17.67082056032528, 17.79672590189168, 19.98868911199488, 20.613182021776023, 21.828474660775, 23.221592823483387, 24.199544969213683, 25.36937740564691],
                       'mls': [2.32389673463722, 4.6, 6.84, 9.04, 11.200000000000001, 13.32, 14.105, 17.36851117334072, 19.633093354761392, 22.0543457036864, 24.795937028873233, 26.10032969544468, 27.698145977983263, 29.28081463908972, 30.88770483938925, 33.02304559315264, 34.79454546709352, 36.92871627011892, 36.93368023987401, 38.7046383879366, 39.600088365794875, 40.94007859326066, 42.349909242479626],
                       'mlt': [0.132867239863517, 0.267744610645826, 0.400013307378327, 0.518888350532788, 0.662399809222465, 0.782558080723548, 0.9193852489695161, 1.054178199439432, 1.176002355946491, 1.33757759675902, 1.4703079097287899, 1.590247643023992, 1.735832878424658, 1.8617503271484042, 1.9661968965498597, 2.068661839655952, 2.1353401404533088, 2.308601174310072, 2.418554099852511, 2.47318161172974, 2.591940935079216, 2.69402566148771, 2.823044459786126],
                       'web': [2.9163835941556, 5.82302184321796, 8.75222684973552, 11.63225652933488, 14.65030025466525, 17.53308522683832, 20.51588275978787, 23.41929277075264, 26.39878389492975, 29.2153434772557, 32.11549510096807, 35.159181422141884, 38.051598625416226, 41.06311608391608, 43.998386493089704, 46.91594221054928, 49.73530530598644, 52.57892500192782, 55.581964866899135, 58.561583779160806, 61.28284444297659, 64.01699521974746, 65.11201383587999],
                       'che': [0.147435121516629, 0.29417800863147, 0.439861735699275, 0.584248684826196, 0.73008273601669, 0.8760912161250061, 1.02171621197303, 1.171930737668576, 1.317174383153556, 1.45964718666697, 1.606214730825694, 1.7513366422641599, 1.895039249218193, 2.0424875915593517, 2.186834065005885, 2.32985989930952, 2.475659386277264, 2.6224408071844203, 2.766434760892711, 2.9037482585653, 3.0502915668463557, 3.1558408021960602, 3.2800005630494087]}
    ProflingDataConsum = {'alu':[1,5,1000,1],
                        'omp':[1,24473,1000,1],
                        "pyae":[1,15,1000,1],
                        "che":[1,12000,1000,1],
                          "res":[1,1000,1000,1],
                          "rot":[1,500,1000,1],
                          "mls":[1,6000,1000,1],
                          "mlt":[1,5,1000,1],
                          "vid":[1,8000,1000,1],
                          "web":[1,1300,1000,1]}
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
