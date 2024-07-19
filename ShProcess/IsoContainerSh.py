#According to the slides, now it's simpler, since the core are set, all you will tune is MBA and CAT
#Which is bind on the CPU, so no worrys about manage. You just need the worker
#Use exec to run the function(This solution is more realistic). Here, you assume the input of each request would be
#Input and their code in string
#You even do not need to have the updator right? Nothing need to be updated
#Just need to give a perform monitor, and send data to isoinvoker
#You will get #23 CPU. Only need to listen when to shut down.

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
def workerprocess(RedisShareClient,Signal,PerfCnter,):
    #It's nearly the same. But remember we only work on CPU 23
    psutil.Process(os.getpid()).cpu_affinity([23])
    while Signal.local_sign:
        #Note modify the name to 'Share'
        _, Task = RedisShareClient.blpop('ShChannel',5)
        if Task:
            strTask = json.loads(Task).get('FuncString')
            #execute here:
            exec(strTask)
            et = time.time()
            FuncName = json.loads(Task).get('FuncName')
            PerfCnter[FuncName].all += 1
            if et > json.loads(Task).get('SLO'):
                PerfCnter[FuncName].vio += 1
        else:
            #Maybe sleep shorter, or do not sleep at all.
            time.sleep(0.1)

def perfmonitor(RedisMetricClient,Perf_Cnter,AliveList):
    #Collect data from all live workers
    ReportList = {}
    with lock:
        for key in Perf_Cnter:
           if key not in AliveList:
               Perf_Cnter[key].clean()
        for key in Perf_Cnter:
            if Perf_Cnter[key].all !=0:
                ReportList[key] = Perf_Cnter[key].vio/Perf_Cnter[key].all
    RedisMetricClient.rpush('ShareVio',json.dumps(ReportList))
    #Besides SLO violation, you'd like to report your CPU and other resource's util
    #Explanation on why only CPU usage is engouth: Here you only have one CPU, so it means at most of the cases, the CPU but not BW and cache are
    #The key factor to prevent you from being fully utilized.
    #Maybe no need for CPU util.

def listener(RedisShDataClient,RedisMessageClient,Perf_Cnter,AliveFunctionList,lock):
    #This is also needs since you will check when to shut down.
    # Init the connection to the IsoInvoker
    pubsub = RedisMessageClient.pubsub()
    pubsub.subscribe('UpdateChannel')
    # Init Workerlist and Controlist here
    Control_Sign = []
    Control_Sign.append(ControlSign())
    Listening = True
    np = mp.Process(target=workerprocess, args=(RedisShDataClient,Control_Sign,Perf_Cnter,))
    np.start()
    while Listening:
        message = pubsub.listen()
        if message:
            # You got a message
            if message['type'] == 'message':
                # You got a message passing data
                Instruction = json.loads(message['data'].decode('utf-8'))
                action = Instruction['action']
                if action == "shutdown":
                        # IF you will shutdown
                    for item in Control_Sign:
                        item.signstop()
                    Listening = False
                #Update AliveList here， but modification happens at perf function
                with lock:
                    AliveFunctionList[:] = Instruction['AliveList']
                #Update perfconter here
                #for key in Perf_Cnter:
                #    if key not in AliveList:
                #        Perf_Cnter[key].clean()
    pubsub.close()
    np.join()

#Check overall logic tomorrow.
if __name__ == '__main__':
    #Since we only have at most 7 diff functions and little req to Sh part, so it may be OK to use One DB here.
    RedisShDataClient = redis.Redis(host='ShDataSvc.default.svc.cluster.local', port=6379, db=0,decode_responses=True)
    RedisMessageClient = redis.Redis(host='InvokerShMessageSvc.default.svc.cluster.local', port=6379)
    RedisMetricClient = redis.Redis(host='InvokerMetricsService.default.svc.cluster.local', port=6379, db=0)
    # Different as different IsoContainer goes, need to change here.
    # This is just a kind of simple test
    scheduler = BackgroundScheduler()
    #Remember Init Perf_Cnter with many possible functions
    Perf_Cnter = {'Alu':PerfCnter(),'MLServe':PerfCnter()}
    AliveFunctionList = []
    #Need Exclusive to tell you who are alive now. Modify later.
    lock = threading.Lock()
    L = threading.Thread(target=listener, args=(RedisShDataClient,RedisMessageClient,Perf_Cnter,AliveFunctionList,lock,))
    L.start()
    scheduler.add_job(perfmonitor, 'interval', seconds=3, args=(RedisMetricClient,Perf_Cnter,AliveFunctionList,lock,))
    scheduler.start()
    # Join will only finish when you shutdown the container.
    L.join()
    scheduler.shutdown()

#About the request split: According to Exclusive SLO violation rate to disp at flask. Slo vio means the parts you'd like to let the
#Shareable to serve, since they are not handled by the exclusive part correctly.
#And the shareable SLO violation will be used for the isoinvoker to scale up and down.
