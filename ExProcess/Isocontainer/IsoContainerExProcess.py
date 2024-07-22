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
import ctypes

#The last effort here is to align all redis lib, and check intermediate data type, and so on. Logic should be fine. You check later
#All func name should be the same as defined name.

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

#Global variable
Previous=0
Previolate = 0
#Basic execution unit, process. Thinking maybe just use exec for everyone? maybe
def workerprocess(RedisDataClient,FuncName,Signal,AffinityId,PerfCnter,PerfCnterVio):
    #Once Init, it should always try to fetch and execute code. So currently I'm thinking the input is the string like func
    #Like everything here are already assigned to the string. no need for other requests.
    #You could modify scale here
    #Assuming Data has SLO also.
    os.sched_setaffinity(0,{AffinityId})
    while Signal.local_sign:
        #here we define the blpop's queue are queue that each element only contains strings.
        #Auto decoding enabled.
        result = RedisDataClient.blpop(FuncName,5)
        if result:
            _,Task = result
            if Task:
                #decode Task
                strTask = json.loads(Task).get('FuncString')
                #Assuming they are the same here.
                if 'alu' not in globals():
                    exec(strTask)
                final = eval('alu()')
                et = time.time()
                PerfCnter[AffinityId] += 1
                if et > json.loads(Task).get('SLO'):
                    PerfCnterVio[AffinityId] += 1

#The controller to tune worker and resource
def controller(RedisDataClient,FuncName,ControlList,PerfCnter,NewMask,CPUMASK,RunningProcessesDict,PerfCnterVio):
    #Controller is responsible for Tunning resource avaliablity based on the instruction from listener.
    #Ecerything is based on the CPUList the IsoInvoker given(Scale Up/Down)
    #Updateing here
    for i in range(23):
            #Start new processes on these CPUs
        if CPUMASK[i] != NewMask[i]:
            #Either start or stop
            if NewMask[i] == 1:
                #Start
                np = mp.Process(target=workerprocess,args=(RedisDataClient, FuncName, ControlList[i], i, PerfCnter,PerfCnterVio,))
                np.start()
                RunningProcessesDict[i] = np
                CPUMASK[i] = 1
            else:
                #Need to stop and reset
                ControlList[i].signstop()
                RunningProcessesDict[i].terminate()
                RunningProcessesDict[i].join()
                CPUMASK[i] = 0
                PerfCnter[i] = 0
                PerfCnterVio[i] =0

#The listener who are subscribe and trigger manager to tune workers
def listener(RedisDataClient,FuncName,RedisMessageClient,Perf_Cnter,CPUMASK,RunningProcessesDict,PerfCnterVio):
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
        PerfCnterVio.append(0)
    #Simply Init here.
    NewMask = [0]*23
    NewMask[4] = 1
    #Inithere
    controller(RedisDataClient, FuncName, Control_Sign, Perf_Cnter,
               NewMask, CPUMASK,RunningProcessesDict,PerfCnterVio)
    Listening = True
    while Listening:
        #Add shutdown here.
        messagelist = pubsub.listen()
        if messagelist:
            #You got a message
            for message in messagelist:
                if message['type'] == 'message':
                    #You got a message passing data
                    CPUMASKDict = json.loads(message['data'])
                    #For the shutdown message, we simply set the CPUMASK to all zero(If we still keep the container alive could live later, Currently shut down)
                    if FuncName in CPUMASKDict:
                        #If you got a message for you
                        NewMask = CPUMASKDict[FuncName]
                        #print(NewMask,flush=True)
                        if sum(NewMask) != 0 and sum(NewMask)!= sum(CPUMASK):
                            #Update
                            controller(RedisDataClient, FuncName,Control_Sign, Perf_Cnter,
                                       NewMask,CPUMASK,RunningProcessesDict,PerfCnterVio)
                        elif sum(NewMask) == 0:
                           #Scale to zero, shutdown now. The other just keep the same.
                           #Call the controller function to stop.
                           controller(RedisDataClient, FuncName, Control_Sign, Perf_Cnter,
                                      NewMask, CPUMASK, RunningProcessesDict, PerfCnterVio)
                           #Soft stop. Still listenining. But just not update perf metrics.
                           #Listening = False
                           #Here cpu mask is the one we want. Remember let Invoker discard its result if the func is not alive.
                           #break
    pubsub.close()

#Perf Monitor which tracks the SLO violation of exclusive. This is useful for traffic split.
def perfmonitor(RedisFlaskClient,CPUMASK,PerfList,PerfCnterVio):
    #Collect data from all live workers
    global Previous
    global Previolate
    All = 0
    violate = 0
    if sum(CPUMASK)!=0:
        for i in range(23):
            if CPUMASK[i]!= 0:
                All += PerfList[i]
                violate += PerfCnterVio[i]
        if Previous ==0:
           print('Pktp of current Func is ' + str(All / 10), flush=True)
           ExVioRate = violate/All
           #Send to Flask Redis
           RedisFlaskClient.set('ExSLOVio',ExVioRate)
        else:
           print('Pktp of current Func is ' + str((All-Previous) / 10), flush=True)
           ExVioRate = (violate-Previolate) / (All-Previous)
           RedisFlaskClient.set('ExSLOVio', ExVioRate)
        #Update
        Previous = All
        Previolate = violate

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
    FuncName = 'alu'
    RedisFlaskClient.set('Shutdown', 0)
    scheduler = BackgroundScheduler()
    Perf_Cnter_All = manager.list()
    Per_Cnter_Vio = manager.list()
    LocalCPUMASK = [0]*23
    #LocalCPUMASK[3] = 1
    RunningProcessesDict = {}

    L =threading.Thread(target=listener,args=(RedisDataClient,FuncName,RedisMessageClient,Perf_Cnter_All,LocalCPUMASK,RunningProcessesDict,Per_Cnter_Vio,))
    L.start()
    scheduler.add_job(perfmonitor, 'interval', seconds=10,args=(RedisFlaskClient,LocalCPUMASK,Perf_Cnter_All,Per_Cnter_Vio,))
    scheduler.start()
    #Join will only finish when you shutdown the container.
    L.join()
    scheduler.shutdown()
    RedisFlaskClient.set('Shutdown',1)
