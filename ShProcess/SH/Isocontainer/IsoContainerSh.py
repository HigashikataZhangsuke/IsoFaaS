#According to the slides, now it's simpler, since the core are set, all you will tune is MBA and CAT
#Which is bind on the CPU, so no worrys about manage. You just need the worker
#Use exec to run the function(This solution is more realistic). Here, you assume the input of each request would be
#Input and their code in string
#You even do not need to have the updator right? Nothing need to be updated
#Just need to give a perform monitor, and send data to isoinvoker
#You will get #23 CPU. Only need to listen when to shut down.
import ctypes
from copy import deepcopy
import redis
import time
import psutil
import multiprocessing as mp
import os
import json
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import random
#Class

class ControlSign:
    def __init__(self):
        self.local_sign = True
    def signstop(self):
        self.local_sign = False
    def signstart(self):
        self.local_sign = True

#Basic execution unit, process. Thinking maybe just use exec for everyone? maybe
def workerprocess(RedisShareClient,Signal,PerfCnter,PerfCnterVio,AliveList):
    #It's nearly the same. But remember we only work on CPU 23
    os.sched_setaffinity(0,{23})
    #print('starting',flush=True)
    while Signal[0].local_sign:
        #Note modify the name to 'Share'
        #The diff is store results to the function name but not the CPU and other.
        result = RedisShareClient.blpop('ShChannel',5)
        if result:
            #print('getone',flush=True)
            _, Task = result
            if Task:
                FuncName = json.loads(Task).get('FuncName')
                strTask = json.loads(Task).get('FuncString')
                if FuncName not in globals():
                    exec(strTask)
                result = eval(FuncName+'()')
                et = time.time()
                #Maybe need to turn to .value(). It's OK, the perf looks like not too bad.
                #It will be shareable dict
                # Init after listener thread modify the counter.
                if FuncName not in AliveList:
                    Perf_Cnter[FuncName] = 0
                    PerfCnterVio[FuncName] = 0
                else:
                    PerfCnter[FuncName]+=1
                    if et > json.loads(Task).get('SLO'):
                        PerfCnterVio[FuncName] += 1


Previous = {}
Previolate = {}

def perfmonitor(RedisMetricClient,Perf_Cnter,PerfList,PerfCnterVio,Ifperform):
    #Collect data from all live workers
    global Previous
    global Previolate
    ReportAll = {}
    ReportVio = {}
    Send = {}
    #Only those in alive list func will record their perf metrics.
    #print(PerfList,flush=True)
    if Ifperform.value:
        if len(PerfList)!=0 and Perf_Cnter and PerfCnterVio:
            for key in PerfList:
                if Previous.get(key) ==0 or Previous.get(key) is None:
                    ReportAll[key] = Perf_Cnter.get(key)
                    ReportVio[key] = PerfCnterVio.get(key)
                    Send[key] = (ReportVio.get(key))/(ReportAll.get(key)) + random.uniform(2,5)
                else:
                    ReportAll[key] = Perf_Cnter.get(key) - Previous.get(key)
                    ReportVio[key] = PerfCnterVio.get(key) - Previolate.get(key)
                    Send[key] = (ReportVio.get(key))/(ReportAll.get(key)) + random.uniform(2,5)
            #print(Send,flush=True)
            RedisMetricClient.rpush('ShareVio',json.dumps(Send))
            Previous = deepcopy(ReportAll)
            Previolate = deepcopy(ReportVio)


def listener(RedisShDataClient,RedisMessageClient,Perf_Cnter,AliveFunctionList,PerfVioCnter,Ifperform):
    #This is also needs since you will check when to shut down.
    # Init the connection to the IsoInvoker
    pubsub = RedisMessageClient.pubsub()
    pubsub.subscribe('UpdateChannel')
    # Init Workerlist and Controlist here
    Control_Sign = []
    Control_Sign.append(ControlSign())
    Listening = True
    np = mp.Process(target=workerprocess, args=(RedisShDataClient,Control_Sign,Perf_Cnter,PerfVioCnter,AliveFunctionList,))
    np.start()
    while Listening:
        messagelist = pubsub.listen()
        if messagelist:
            # You got a message
            for message in messagelist:
                if message['type'] == 'message':
                    #check either shutdown or you get the alive function list. If you get the list, OK, call the update function to update the Listdict
                    # You got a message passing data
                    Instruction = json.loads(message['data'])
                    #print(Instruction,flush=True)
                    # For the shutdown message, we simply set the CPUMASK to all zero(If we still keep the container alive could live later, Currently shut down)
                    if "AliveList" in Instruction:
                        #Update the List.
                        #print('Received one',flush=True)
                        #Reborn.
                        Ifperform.value = True
                        #print(AliveFunctionList,flush = True)
                        AliveFunctionList[:] = deepcopy(Instruction["AliveList"])
                        #print(AliveFunctionList, flush=True)
                    elif "shutdown" in Instruction:
                        #Shutdown
                        #print("shutting Down",flush=True)
                        Control_Sign[0].signstop()
                        #Listening = False
                        #Do not send again.
                        Ifperform.value = False
                        #np.terminate()
                        #np.join()
    np.terminate()
    np.join()
    pubsub.close()



#Check overall logic tomorrow.
if __name__ == '__main__':
    #Since we only have at most 7 diff functions and little req to Sh part, so it may be OK to use One DB here.
    RedisShDataClient = redis.Redis(host='shdatasvc.default.svc.cluster.local', port=6379, db=0,decode_responses=True)
    RedisMessageClient = redis.Redis(host='invokermessagesvc.default.svc.cluster.local', port=6379,decode_responses=True)
    RedisMetricClient = redis.Redis(host='aludatasvc.default.svc.cluster.local', port=6379, db=1,decode_responses=True)
    # Different as different IsoContainer goes, need to change here.
    # This is just a kind of simple test
    scheduler = BackgroundScheduler()
    #Remember Init Perf_Cnter with many possible functions
    manager = mp.Manager()
    AliveFunctionList = manager.list()
    Perf_Cnter = manager.dict()
    Vio_Cnter = manager.dict()
    Ifperform = mp.Value(ctypes.c_bool,True)
    #Need Exclusive to tell you who are alive now. Modify later.
    L = threading.Thread(target=listener, args=(RedisShDataClient,RedisMessageClient,Perf_Cnter,AliveFunctionList,Vio_Cnter,Ifperform,))
    L.start()
    scheduler.add_job(perfmonitor, 'interval', seconds=3, args=(RedisMetricClient,Perf_Cnter,AliveFunctionList,Vio_Cnter,Ifperform,))
    scheduler.start()
    # Join will only finish when you shutdown the container.
    L.join()
    scheduler.shutdown()

#About the request split: According to Exclusive SLO violation rate to disp at flask. Slo vio means the parts you'd like to let the
#Shareable to serve, since they are not handled by the exclusive part correctly.
#And the shareable SLO violation will be used for the isoinvoker to scale up and down.
