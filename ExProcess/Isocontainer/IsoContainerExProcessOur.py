#The Exclusive IsoContainer Impl
#Since MBA and CAT can directly be applied, no need for stall so just like tunning CPU masks.
#So here's how we would like to solve this problem, we first will use Redis's pub-sub model to let the controller
#Thread to keep listening if it's time to update/shutdown(Note here just scale up is fine, since invoker will give you range and do it first)
#For scale down, it's a little bit different: we get the new number of CPU first
#Then the thread just update. And after that, we let the controller tell invoker the new range and invoker reclaim the resources.
#For execution, we just start several workers who keeps asking for data from the redis queue(atomic so it's fine), and then, each worker works on a cpu.
#To close them, use a signal sign here, which is controlled by the manager.
#We still could use the MXFaaS's way of tunning resource amount. two Slo bounds for shareable to get the results.
#Assuming All worker are on CPU 0-22. CPU 23 is assign to the Shareable part.

#The last effort here is to align all redis lib, and check intermediate data type, and so on. Logic should be fine. You check later

import redis
import time
import psutil
import multiprocessing as mp
import os
import json
import threading
from apscheduler.schedulers.background import BackgroundScheduler

#Class
class ControlSign:
    def __init__(self):
        self.local_sign = True
    def signstop(self):
        self.local_sign = False
    def signstart(self):
        self.local_sign = True

class PerfCnter:
    def __init__(self):
        self.all = 0
        self.vio = 0
    def clean(self):
        self.all = 0
        self.vio = 0

#Basic execution unit, process. Thinking maybe just use exec for everyone? maybe
def workerprocess(RedisDataClient,FuncName,Signal,AffinityId,PerfCnter):
    #Once Init, it should always try to fetch and execute code. So currently I'm thinking the input is the string like func
    #Like everything here are already assigned to the string. no need for other requests.
    #You could modify scale here
    #Assuming Data has SLO also.
    #psutil.Process(os.getpid()).cpu_affinity([AffinityId])
    #print(AffinityId,flush=True)
    os.sched_setaffinity(0,{AffinityId})
    print(os.sched_getaffinity(0),flush=True)
    #print(os.getpid(),flush=True)
    while Signal.local_sign:
        #here we define the blpop's queue are queue that each element only contains strings.
        #Auto decoding enabled.
        result = RedisDataClient.blpop(FuncName,5)
        if result:
            _,Task = result
            if Task:
                #decode Task
                strTask = json.loads(Task).get('FuncString')
                #execute here:
                #print(strTask,flush=True)
                exec(strTask)
                et = time.time()
                PerfCnter[AffinityId] += 1
                #print(PerfCnter.all)
                #if et > json.loads(Task).get('SLO'):
                    #PerfCnter.vio += 1
        #else:
            #Maybe sleep shorter, or do not sleep at all.
            #time.sleep(0.1)

#The controller to tune worker and resource
def controller(RedisDataClient,FuncName,ControlList,PerfCnter,NewMask,CPUMASK):
    #Controller is responsible for Tunning resource avaliablity based on the instruction from listener.
    #Ecerything is based on the CPUList the IsoInvoker given(Scale Up/Down)
    #Updateing here
    for i in range(23):
            #Start new processes on these CPUs
        if CPUMASK[i] != NewMask[i]:
                #Either start or stop
            if NewMask[i] == 1:
                    #Start
                np = mp.Process(target=workerprocess,args=(RedisDataClient, FuncName, ControlList[i], i, PerfCnter,))
                np.start()
                CPUMASK[i] = 1
            else:
                #Need to stop
                ControlList[i].signstop()
                CPUMASK[i] = 0
                PerfCnter[i] = 0

#The listener who are subscribe and trigger manager to tune workers
def listener(RedisDataClient,FuncName,RedisMessageClient,Perf_Cnter,CPUMASK):
    #Init the connection to the IsoInvoker
    pubsub = RedisMessageClient.pubsub()
    pubsub.subscribe('UpdateChannel')
    #Init Workerlist and Controlist here
    max_worker = 23
    Control_Sign = []
    for i in range(max_worker):
        Control_Sign.append(ControlSign())
        #Perf_Cnter.append(PerfCnter())
        Perf_Cnter.append(0)
    NewMask = [0]*23
    NewMask[4] = 1
    NewMask[5] = 1
    NewMask[6] = 1
    NewMask[7] = 1
    NewMask[8] = 1
    NewMask[9] = 1
    NewMask[10] = 1
    NewMask[11] = 1
    # NewMask[12] = 1
    # NewMask[13] = 1
    # NewMask[14] = 1
    # NewMask[15] = 1
    # NewMask[16] = 1
    # NewMask[17] = 1
    # NewMask[18] = 1
    # NewMask[19] = 1
    # NewMask[0] = 1
    # NewMask[20] = 1
    # NewMask[21] = 1
    # NewMask[22] = 1
    #Inithere
    controller(RedisDataClient, FuncName, Control_Sign, Perf_Cnter,
               NewMask, CPUMASK)
    Listening = True
    while Listening:
        messagelist = pubsub.listen()
        if messagelist:
            #You got a message
            #print(message)
            #Maybe wrap and decode here first
            #message =
            for message in messagelist:
                if message['type'] == 'message':
                    #You got a message passing data
                    CPUMASKDict = json.loads(message['data'])
                    if FuncName in CPUMASKDict:
                        #If you got a message for you
                        NewMask = CPUMASKDict[FuncName]
                        if len(NewMask) != 0 and len(NewMask)!= len(CPUMASK):
                            #Update
                            controller(RedisDataClient, FuncName,Control_Sign, Perf_Cnter,
                                       NewMask,CPUMASK)
                        else:
                            #Scale to zero, shutdown now
                            for item in Control_Sign:
                                item.signstop()
                            Listening = False
    pubsub.close()
Previous=0
#Perf Monitor which tracks the SLO violation of exclusive. This is useful for traffic split.
def perfmonitor(RedisFlaskClient,CPUMASK,PerfList):
    #Collect data from all live workers
    #global All
    #violate = 0
    global Previous
    All = 0
    #print(PerfList,flush=True)
    #print(sum(CPUMASK),flush=True)
    if sum(CPUMASK)!=0:
        for i in range(23):
            if CPUMASK[i]!= 0:
                #print(i)
                #print(PerfList[i].all,flush=True)
                All += PerfList[i]
                #if All!=0:
                #    All = PerfList[i] -All
                #else:
                #    All = PerfList[i]
                #violate+= PerfList[i].vio
        #print(All,flush=True)
        #if All!=0:
            #rate = violate/All
        #Send to Flask. Not related to shareable.
            #RedisFlaskClient.set('ExSLOVio',rate)
        if Previous ==0:
            print('Pktp of current Func is ' + str(All / 10), flush=True)
        else:
            print('Pktp of current Func is ' + str((All-Previous) / 10), flush=True)
        Previous = All




if __name__ == '__main__':
    #As you are the IsoContainer for some function so you'd give the RedisClient here.
    #Note for Data Svc You need to provide such db
    #SLO
    manager = mp.Manager()
    RedisDataClient = redis.Redis(host='aludatasvc.default.svc.cluster.local', port=6379, db=0,decode_responses=True)
    RedisMessageClient = redis.Redis(host='invokermessagesvc.default.svc.cluster.local', port=6379,decode_responses=True)
    RedisFlaskClient = redis.Redis(host='aludatasvc.default.svc.cluster.local', port=6379, db=1,decode_responses=True)
    #Different as different IsoContainer goes, need to change here.
    #This is just a kind of simple test
    FuncName = 'Alu'
    scheduler = BackgroundScheduler()
    Perf_Cnter_All = manager.list()
    LocalCPUMASK = [0]*23
    LocalCPUMASK[3] = 1
    L =threading.Thread(target=listener,args=(RedisDataClient,FuncName,RedisMessageClient,Perf_Cnter_All,LocalCPUMASK,))
    L.start()
    scheduler.add_job(perfmonitor, 'interval', seconds=10,args=(RedisFlaskClient,LocalCPUMASK,Perf_Cnter_All,))
    scheduler.start()
    #Join will only finish when you shutdown the container.
    L.join()
    scheduler.shutdown()
