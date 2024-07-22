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

#Always rethink data type.

#The first part to Impl is about the connect level to scheduler and garbage collector. You will have one listener for two channels
#One from the scheduler, and the other is from the garbage collector.
#Then you need to update your metrics to the GC periodically. But not Scheduler. Scheduler only responsible for scale up
#Check all data types after you finished.
#For PrefCurve, you currently use virtual function like y=lnx,x^2 to do the test since they are easy to check.
#It should be a curve of log like or piecewise linear. Currently plan is to use log like to see what will happen
#The format here is Function-> Resource Type -> Curve type : Coefficients
#For PLiner, it should be turning point and the slope. 1-4 means CPU,MBW,Mem,Cache respectively
#Think about this
#Everyone must be a Plinear!
PerfCurve = {'Alu':{'1':['log',2], '2':['log',2], '3':['Log',0.1], '4':['Log',1]}}
#the tuning point aligns to a throughput
Tuningpoint = {'Alu':{'1':2, '2':3, '3':4, '4':4}}
UnitThroughput = {'Alu':{'1':2, '2':3, '3':4, '4':4}}
#Profiling Data
ProfilingData = {'Alu':[2,2,2,2]}

class LListenerSign:
    def __init__(self):
        self.local_sign = True
    def signstop(self):
        self.local_sign = False
    def signstart(self):
        self.local_sign = True

#Related functions
def ComputeBound(FuncName,AliveList,ArrivalRateDict):
    #Assuming all rate containd in the Arrival Rate dict.
    #FuncName is the new func added here
    #CurrFuncList is the curr alive func in this node
    #ArrivalRate is the Rate vector, contains all rate of related alive function you need. This could be attained before computation through
    #Redis Reading
    NewBounds = {}
    global ProfilingData #A dictioinary contains all DataConsumption you need.
    #Then all the needed data will be reachable from the Dic and Rate Ratio. Solve the equation,pick the smallest one to get bounds.
    #For each func you have one bound, so will have len(CurrFuncList) bounds to return
    smallest = 1000
    #boundindex = 5 No need for this?
    for i in range(4):
        #Get the rate of one function for 4 types of resources for a function, we simply choose the given new Func here:
        Coeff = ProfilingData[FuncName][i]
        for item in range(len(AliveList)):
            Coeff += ProfilingData[AliveList[item]][i] *ArrivalRateDict[item]/ArrivalRateDict[FuncName]
        if 1/Coeff<smallest:
            smallest = 1/Coeff
            #boundindex = i
    #Ok we know the best bound index. Now just derive bounds for every function.
    #New bound first, a tuple. And the CPU/MBA/CAT should be integer. Here to put the system's one numa node's maximuim BW, and maximum allocable cache line(To check later)
    for key in AliveList:
        NewBounds[key] = (math.floor(smallest*ProfilingData[key][0]*23),math.floor(smallest*ProfilingData[key][1]*102400),smallest*ProfilingData[key][2],math.floor(smallest*ProfilingData[key][3]*11))
    return NewBounds

def ComputeCost(FuncName, NewBounds, ArrivalRateDict):
    # Assuming all rate containd in the Arrival Rate.
    #To get the cost, find out the unused resources amount, then apply the cost function
    global PerfCurve
    Cost = 0
    LeftedResource = [24,102400,102400,11]
    RateRatio = []
    for i in range(4):
        for key in NewBounds:
            LeftedResource[i] -= NewBounds[key][i]
            RateRatio.append(ArrivalRateDict[key]/sum(ArrivalRateDict.values()))
    #The get the Cost:
    for key in NewBounds:
        for i in range(4):
            Cost -= PerfCurve[FuncName][i][1] * math.log(RateRatio[key]*LeftedResource[i],2)
    return Cost

def Merge(CPUNUM,RedisMessageClientEx,AllList,FuncName,ResourceAllocation,CurrMaskList,FunctionLLCMapping,FunctionMBAMapping):
    #According to the merge amount and curr resource amount, we tried to get the best Mask and related MBA/CAT allocation
    old = len(CurrMaskList[FuncName])
    for i in range(old,CPUNUM):
        #Add this much resource
        for j in range(len(AllList)):
            if AllList[j] ==1:
                #Take the resources
                CurrMaskList[FuncName][j] = 1
                AllList[j] = 0
                break
    #Scale related resources
    Ratio = len(CurrMaskList[FuncName])/old
    ResourceAllocation[FuncName] = [math.floor(x*Ratio) for x in ResourceAllocation[FuncName]]
    SetMBAandCAT(ResourceAllocation,FuncName,CurrMaskList,FunctionLLCMapping,FunctionMBAMapping)
    #Then do publish here
    RedisMessageClientEx.publish('UpdateChannel',json.dumps(CurrMaskList))

def binary_to_hex(binary_str):
    # 将二进制字符串转换为整数
    decimal_value = int(binary_str, 2)
    # 将整数转换为十六进制字符串
    hex_value = hex(decimal_value)
    return hex_value

def SetMBAandCAT(AllocatedResource,FuncName,CurrMaskList,FunctionLLCMapping,FunctionMBAMapping):
    #Remember that MBA and CAT have limit. usually MBA has upper bound 8 and CAT 16. Need to add this check at the first part.
    #First you need to know which Container you are working on, and then you need to know the new bound. Thirdly you need to know CPU affinity
    try:
        #Remember to add a transfer here. Transfer to hex. Or to hex once you make sure how to do this. Transfered
        subprocess.run(['sudo', 'pqos', '-e', 'llc:'+FunctionLLCMapping.index(FuncName)+'='+str(binary_to_hex(AllocatedResource[FuncName][3]))], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to set CAT: {e}")
    try:
        subprocess.run(['sudo', 'pqos', '-e', 'mba:'+FunctionMBAMapping.index(FuncName)+'='+str(AllocatedResource[FuncName][1]), '-r'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to set MBA: {e}")
    #Then bind CPU to LLC and MBA here
    try:
        subprocess.run(['sudo', 'pqos', '-a', 'llc:'+FunctionLLCMapping.index(FuncName)+'='+CurrMaskList[FuncName]], check=True)
        subprocess.run(['sudo', 'pqos', '-a', 'core:' + FunctionMBAMapping.index(FuncName) + '=' + CurrMaskList[FuncName]],
                       check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to bind CPUs to COS: {e}")

def GetExAmount(ArrivalRate,FuncName):
    global UnitThroughput
    global Tuningpoint
    #Firstly, you need to find the tune point in the curve, and mark them as the best resource unit allocation(smaller or bigger both not good)
    #Then at this setting you could get a throughput
    #And decide the resource amount needed by using the ratio.
    resource = []
    for i in range(4):
        resource.append(ArrivalRate/UnitThroughput[FuncName][i]*Tuningpoint[FuncName][i])
    return resource

def GetNewMask(CurrMask,FuncName,NewResourceAmount,Instruction,AllList):
    #Then after you get the new ex resource amount needed, and you know which one you need to update, then
    if Instruction =='ScaleUp':
        old = len(CurrMask[FuncName])
        for i in range(old, NewResourceAmount):
            # Add this much resource
            for j in range(len(AllList)):
                if AllList[j] == 1:
                    # Take the resources
                    CurrMask[FuncName][j] = 1
                    AllList[j] = 0
                    break
    else:
        old = len(CurrMask[FuncName])
        for i in range(NewResourceAmount,old):
            # Add this much resource
            for j in range(old):
                if CurrMask[FuncName][j] == 1:
                    # Take the resources
                    CurrMask[FuncName][j] = 0
                    AllList[j] = 1
                    break

#Two listeners
def Glistener(RedisClusterSvc,RedisClusterMetricSvc,RedisMessageClientEx,ListenerSign,AliveList,ID,ResourceAllocation,CurrMaskList,
              AllCPUList,FunctionLLCMapping,FunctionMBAMapping,ArrivalRateDict):
    #Listen to two channels at the same time. then send scale up or scale down according to the signal
    #Scheduler give you scale up and garbage collector give you shutdown.
    pubsub = RedisClusterSvc.pubsub()
    #For Redis connection you could make it into a naive way. If you want dynamic way maybe need to connection.
    pubsub.subscribe('Scheduler','GarbageCollector')
    #Since it will process the message as order so I think it's OK to leave it here.
    Listening = True
    while Listening:
        message = pubsub.listen()
        if message:
            # You got a message
            if message['type'] == 'message':
                # You got a message passing data
                Instruction = json.loads(message['data'].decode('utf-8'))
                Sourcename = Instruction['Name']
                if Sourcename == 'Scheduler':
                    # If you got a message for you from scheduler
                    action = Instruction['action']
                    if action == "ComputeCost":
                        FuncName = Instruction['Function']
                        #Have problem here, rethink carefully. when to update. When to just use is different.
                        ArrivalRateDicttemp = Instruction['Rate']
                        #Call compute bound function
                        NewBounds = ComputeBound(FuncName,AliveList,ArrivalRateDicttemp)
                        Cost = ComputeCost(FuncName,NewBounds,ArrivalRateDicttemp)
                        #Set the Cost to the scheduler
                        UpdateData = {
                            "ID": ID,
                            "Cost": Cost
                        }
                        RedisClusterMetricSvc.rpush('Metrics',json.dumps(UpdateData))
                    elif action == "SetFunction":
                        #Set new function here.
                        #Update related resources
                        FuncName = Instruction['Function']
                        ArrivalRateDict = Instruction['Rate']
                        AliveList.append(FuncName)
                elif Sourcename == 'GarbageCollector':
                    action = Instruction['action']
                    if action == "shutdown":
                        #Shutdown
                        Listening = False
                        ListenerSign.signstop()
                    else:
                        #Call merge here. Merge means you get a number from gc, you need to decide the new CPU MASK
                        #This is more like a kind of scale up.
                        CPUNUM = Instruction['CPUNUM']
                        FuncName = Instruction['FuncName']
                        #CurrMask is a list/dict that maintains the Mask for the whole system
                        Merge(CPUNUM,RedisMessageClientEx,AllCPUList,FuncName,ResourceAllocation,CurrMaskList,FunctionLLCMapping,FunctionMBAMapping)
    pubsub.close()

def LListener(LListenerSign,RedisMetricClient,ResourceAllocation,ArrivalRateDict,CurrMaskDict,FunctionLLCMapping,FunctionMBAMapping,AllCPUList):
    #For Local listener it's more like a process for local scaling up and down. You only need to use the
    #Function Perf Curve, and the arrival rate to determine the exclusive amount. Also, your shareable SLO is for sending the global scaling request
    #If you send a global scaling request, should you block here? no. after get the results, you have at least 3 seconds for scaling
    #so it may not be a problem for you.
    UpperBound = 0.6
    LowerBound = 0.1
    while LListenerSign.sign:
        #Check every 5 sec
        #Keep monitoring the staticstics you get from containers, if anyone needs an update, then update.:
        #Assuming you will get SLO vio on shared resource from each alive func, then you need to pickup the
        #Not satisfied one, and update exclusive resource, and update your CPUMASK,MBA，CAT allocationhere. Mem is not the key here
        #Though we put it here.
        #And for scale up/down remember to execute first, and then send signal. They are the same I think actually
        data = RedisMetricClient.blpop('ShareVio',0.2)
        if data:
            PerfDict = json.loads(data)
            for key in PerfDict:
                slovio = PerfDict[key]
                if slovio > UpperBound:
                    #need to scale up
                    ResourceAllocation[key] = GetExAmount(ArrivalRateDict[key],key)
                    GetNewMask(CurrMaskDict,key,ResourceAllocation[key],'ScaleUp',AllCPUList)
                    SetMBAandCAT(ResourceAllocation,key,CurrMaskDict,FunctionLLCMapping,FunctionMBAMapping)
                    #Publishhere
                    RedisMessageClientEx.publish('UpdateChannel', json.dumps(CurrMaskDict))
                elif slovio < LowerBound:
                    #Need to scale down
                    ResourceAllocation[key] = GetExAmount(ArrivalRateDict[key], key)
                    GetNewMask(CurrMaskDict, key, ResourceAllocation[key], 'ScaleDown',AllCPUList)
                    SetMBAandCAT(ResourceAllocation,key,CurrMaskDict,FunctionLLCMapping,FunctionMBAMapping)
                    #publish here
                    RedisMessageClientEx.publish('UpdateChannel', json.dumps(CurrMaskDict))
        time.sleep(5)
        #Do you need any other?
        #It will be fine now.
        #Looks like finished.

if __name__ == '__main__':
    RedisClusterSvc = redis.Redis(host='ClusterSvc.default.svc.cluster.local', port=6379)
    RedisClusterMetricSvc = redis.Redis(host='ClusterSvc.default.svc.cluster.local',db=1, port=6379)
    RedisMessageClientSh = redis.Redis(host='InvokerShMessageSvc.default.svc.cluster.local', port=6379)
    RedisMessageClientEx = redis.Redis(host='InvokerMessageSvc.default.svc.cluster.local', port=6379)
    RedisMetricClient = redis.Redis(host='InvokerMetricsService.default.svc.cluster.local', port=6379, db=0,decode_responses=True)
    #Init variables and then Start The thread and the subprocess.
    ListenerSign = LListenerSign()
    manager = mp.Manager()
    AliveList = manager.list()
    CurrMaskDict = manager.dict()
    ID = uuid.uuid4()
    #A dict, stores the resource allocation results for alive functions in this node.
    ResourceAllocation = manager.dict()
    AllCPUList = manager.list()
    FunctionLLCMapping = manager.list()
    FunctionMBAMapping = manager.list()
    ArrivalRateDict = manager.dict()
    for i in range(23):
        AllCPUList.append(1)
    ngp = mp.Process(target=Glistener, args=(RedisClusterSvc,RedisClusterMetricSvc,
                                             RedisMessageClientEx,ListenerSign,AliveList,ID,ResourceAllocation,
                                             CurrMaskDict,AllCPUList,FunctionLLCMapping,FunctionMBAMapping,ArrivalRateDict,))
    nlp = mp.Process(target=LListener,args = (ListenerSign,RedisMetricClient,ResourceAllocation,ArrivalRateDict,CurrMaskDict,
                                              FunctionLLCMapping,FunctionMBAMapping,AllCPUList,))
    ngp.start()
    nlp.start()
    ngp.join()
    nlp.join()