
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
import logging
import random
import redis
import time
import multiprocessing as mp
import os
import json
import threading
import subprocess
import numpy as np
#Class

class ControlSign:
    def __init__(self):
        self.local_sign = True
    def signstop(self):
        self.local_sign = False
    def signstart(self):
        self.local_sign = True

def setup_logging(process_id):
    # 设置日志格式
    # Later just need to use the kubectl cp to get them.
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    currtime = time.time()
    # 创建一个日志处理器，将日志输出到文件. Add time since there is a possibility that the process with same ID spawns.
    log_filename = f'matprocess_{process_id}+{currtime}.log'
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    # 创建一个日志记录器
    logger = logging.getLogger(str(process_id))
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    return logger


def Matmul():
    filename_A='matrix_A.npy'
    filename_B='matrix_B.npy'
    start = time.time()
    A = np.load(filename_A)
    B = np.load(filename_B)
    col_idx = 259
    B_col = B[:, col_idx]  # B ?? col_idx ?, ?? (n,)
    C = A.dot(B_col) 
    latency = time.time() - start
    return C


#Basic execution unit, process. Thinking maybe just use exec for everyone? maybe
def workerprocess(RedisDataClient,FuncName,Signal,AffinityId,number):
    #Once Init, it should always try to fetch and execute code. So currently I'm thinking the input is the string like func
    #Like everything here are already assigned to the string. no need for other requests.
    #You could modify scale here
    #Assuming Data has SLO also.
    os.sched_setaffinity(0, {AffinityId})
    # Do everything locally and then aggregation.
    # You need to tell the TP and your execution latency to us.
    # For TP, we keep the local print way. This could at least save 5% Peak Throughput.
    # Also to see if it's possible to use time.time() less.
    logger = setup_logging(os.getpid())
    lctime = time.time()
    #logger.info(f"P+ {os.getpid()}+{lctime}+ starts logging")
    Totalcnt = 0
    Totalprev = 0
    while Signal.local_sign:
        result = RedisDataClient.blpop(FuncName, 5)
        #print(result,flush=True)
        if result:
            _, datastr = result
           # print(data,flush=True)
            data = json.loads(datastr)
            arrtime = data['ArrivalTime']
            st = time.time()
            result = Matmul()
            et = time.time()
            Totalcnt += 1
            #print("processing",flush=True)
            #if et-lctime > 15:
            #    logger.info("PKTP of CPU num" +" "+ str(number) + " in past around 15 sec is"  + " "+str((Totalcnt-Totalprev)/(et-lctime)) +" " + "The latest standalone latency is " + str(et-st))
                #logger.info("PKTP of CPU num in past around 10 sec is" + str(number) + " "+str((Totalcnt-Totalprev)/(et-lctime)))
                #print("PKTP of CPU num in past around 5 sec is" + str(number) + " "+str((Totalcnt-Totalprev)/(et-lctime)),flush=True)
            #    lctime = time.time()
            #    Totalprev = Totalcnt
            logger.info(f"P+ {os.getpid()}+ process request number + {Totalcnt} + recived at {arrtime} + starts at + {st} + end at {et} + duration {et - st} + E-E latency {et - arrtime}")

#The controller to tune worker and resource
def controller(RedisDataClient,FuncName,ControlList,NewMask,CPUMASK,RunningProcessesDict):
    #Controller is responsible for Tunning resource avaliablity based on the instruction from listener.
    #Ecerything is based on the CPUList the IsoInvoker given(Scale Up/Down)
    #Updateing here
    for i in range(23):
            #Start new processes on these CPUs
        if CPUMASK[i] != NewMask[i]:
            #Either start or stop
            if NewMask[i] == 1:
                #Start
                np = mp.Process(target=workerprocess,args=(RedisDataClient, FuncName, ControlList[i], i,sum(NewMask),))
                np.start()
                RunningProcessesDict[i] = np
                CPUMASK[i] = 1
            else:
                #Need to stop and reset
                ControlList[i].signstop()
                RunningProcessesDict[i].terminate()
                RunningProcessesDict[i].join()
                CPUMASK[i] = 0
        else:
            if NewMask[i] == 1:
                ControlList[i].signstop()
                RunningProcessesDict[i].terminate()
                RunningProcessesDict[i].join()
                ControlList[i].signstart()
                np = mp.Process(target=workerprocess, args=(RedisDataClient, FuncName, ControlList[i], i, sum(NewMask),))
                np.start()
                RunningProcessesDict[i] = np
                #just Change the num
            else:
                pass
#The listener who are subscribe and trigger manager to tune workers
def listener(RedisDataClient,FuncName,RedisMessageClient,CPUMASK,RunningProcessesDict):
    #Init the connection to the IsoInvoker
    pubsub = RedisMessageClient.pubsub()
    pubsub.subscribe('UpdateChannel')
    #Init Workerlist and Controlist here
    max_worker = 23
    Control_Sign = []
    for i in range(max_worker):
        Control_Sign.append(ControlSign())
    #subprocess.run(['sudo', 'pqos', '-e', 'mba_max:2' + '=' + '922', '-r'], check=True)
    #for timercnt in [20,16,12,8,4,1]:
    #    NewMask = [0]*23
    #    start_index = 23 - timercnt
    #    end_index = 23   # 计算结束索引位置
    #for timercnt in range(1,23):
    NewMask = [0] * 23
    for index in range(9,11):
        NewMask[index] = 1

    # 从第23个CPU（索引为22）开始，向前数timercnt个位置，将其设置为1
    #    for index in range(start_index, end_index):
    #        NewMask[index] = 1
    #NewMask = [0]*23
    #for i in range(3,23):
    #    NewMask[i] = 1
    #print(NewMask, flush=True)
    #controller(RedisDataClient, FuncName, Control_Sign,NewMask, CPUMASK,RunningProcessesDict,)
        #cpu_list = ','.join(str(cpu) for cpu, val in enumerate(NewMask) if val == 1)
        #subprocess.run(['sudo', 'pqos', '-a', f'core:2={cpu_list}'], check=True)
    controller(RedisDataClient, FuncName, Control_Sign,
                    NewMask, CPUMASK,RunningProcessesDict,)
        
        #print(CPUMASK, flush=True)
    time.sleep(60)
    time.sleep(50)
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
                            controller(RedisDataClient, FuncName, Control_Sign,
                                       NewMask, CPUMASK, RunningProcessesDict, )
                        elif sum(NewMask) == 0:
                           #Scale to zero, shutdown now. The other just keep the same.
                           #Call the controller function to stop.
                           controller(RedisDataClient, FuncName, Control_Sign,
                                      NewMask, CPUMASK, RunningProcessesDict, )
                           #Soft stop. Still listenining. But just not update perf metrics.
    pubsub.close()


if __name__ == '__main__':
    #As you are the IsoContainer for some function so you'd give the RedisClient here.
    #Note for Data Svc You need to provide such db
    #SLO
    AffinityId = random.randint(24, 47)
    os.sched_setaffinity(0, {AffinityId})
    FuncName = 'mat'
    manager = mp.Manager()
    RedisDataClient = redis.Redis(host=FuncName+'datasvc.default.svc.cluster.local', port=6379, db=0,decode_responses=True)
    #This shall be the same
    RedisMessageClient = redis.Redis(host='invokermessagesvc.default.svc.cluster.local', port=6379,decode_responses=True)
    #Different as different IsoContainer goes, need to change here.
    LocalCPUMASK = [0]*23
    #LocalCPUMASK[3] = 1
    RunningProcessesDict = {}
    L =threading.Thread(target=listener,args=(RedisDataClient,FuncName,RedisMessageClient,LocalCPUMASK,RunningProcessesDict,))
    L.start()
    #Join will only finish when you shutdown the container.
    L.join()