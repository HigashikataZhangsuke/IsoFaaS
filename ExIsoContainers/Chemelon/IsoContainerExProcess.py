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
import six
import json
from chameleon import PageTemplate
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
    log_filename = f'cheprocess_{process_id}+{currtime}.log'
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    # 创建一个日志记录器
    logger = logging.getLogger(str(process_id))
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    return logger

BIGTABLE_ZPT = """\
<table xmlns="http://www.w3.org/1999/xhtml"
xmlns:tal="http://xml.zope.org/namespaces/tal">
<tr tal:repeat="row python: options['table']">
<td tal:repeat="c python: row.values()">
<span tal:define="d python: c + 1"
tal:attributes="class python: 'column-' + %s(d)"
tal:content="python: d" />
</td>
</tr>
</table>""" % six.text_type.__name__

def che():
    input_file = './Che/tables_data.txt'
    with open(input_file, 'r') as f:
        tables = [json.loads(line) for line in f]
    tmpl = PageTemplate(BIGTABLE_ZPT)
    total_time = 0.0
    generation_count = 1
    start = time.time()
    for i in range(generation_count):
        table = tables[i]
        options = {'table': table}
        data = tmpl.render(options=options)
    end = time.time()
    average_time = (end - start) / generation_count
    return {"average_execution_time": average_time}


#Basic execution unit, process. Thinking maybe just use exec for everyone? maybe
def workerprocess(RedisDataClient,FuncName,Signal,AffinityId):
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
    logger.info(f"P+ {os.getpid()}+{lctime}+ starts logging")
    Totalcnt = 0
    while Signal.local_sign:
        result = RedisDataClient.blpop(FuncName, 5)
        if result:
            _, datastr = result
            # print(data,flush=True)
            data = json.loads(datastr)
            arrtime = data['ArrivalTime']
            st = time.time()
            result = che()
            et = time.time()
            Totalcnt += 1
            logger.info(
                f"P+ {os.getpid()}+ process request number + {Totalcnt} + recived at {arrtime} + starts at + {st} + end at {et} + duration {et - st} + E-E latency {et - arrtime}")
            #print(Totalcnt,flush=True)
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
                np = mp.Process(target=workerprocess,args=(RedisDataClient, FuncName, ControlList[i], i,))
                np.start()
                RunningProcessesDict[i] = np
                CPUMASK[i] = 1
            else:
                #Need to stop and reset
                ControlList[i].signstop()
                RunningProcessesDict[i].terminate()
                RunningProcessesDict[i].join()
                CPUMASK[i] = 0

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

    #Simply Init here.
    #NewMask = [0]*23
    #NewMask[6] = 1
    # for i in range(5):
    #     NewMask[i] = 1
    # #Inithere
    #controller(RedisDataClient, FuncName, Control_Sign,
                #NewMask, CPUMASK,RunningProcessesDict,)
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
    FuncName = 'che'
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

