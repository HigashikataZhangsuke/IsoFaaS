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
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import logging
import random
import redis
import time
import multiprocessing as mp
import numpy as np
import json
import threading
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import multiprocessing
np.seterr(all='warn')
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
    log_filename = f'resprocess_{process_id}+{currtime}.log'
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    # 创建一个日志记录器
    logger = logging.getLogger(str(process_id))
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    return logger

def resize_image(image_array, scale_x, scale_y):
    # ?????????
    rows, cols = image_array.shape[:2]
    
    # ??????
    scaling_matrix = np.array([[scale_x, 0], [0, scale_y]])

    # ??????,????????? (x, y)
    coords = np.indices((rows, cols)).reshape(2, -1)  # 2 x (rows * cols)

    # ????????????
    new_coords = np.dot(scaling_matrix, coords)  # 2 x (rows * cols)
    
    # ?????????,????????????
    new_rows = int(rows * scale_y)
    new_cols = int(cols * scale_x)

    # ????????????
    new_coords[0] = np.clip(new_coords[0], 0, new_rows - 1)
    new_coords[1] = np.clip(new_coords[1], 0, new_cols - 1)

    # ????????
    new_image_array = np.zeros((new_rows, new_cols, image_array.shape[2]), dtype=image_array.dtype)

    # ?? np.dot ????,?????? RGB ??
    for channel in range(1):
        # ??????????????
        new_image_array[new_coords[0].astype(int), new_coords[1].astype(int), channel] = image_array[coords[0], coords[1], channel]
    
    return new_image_array

def imgres():
    #os.sched_setaffinity(0, {6})
    generation_count = 10
    ls = []
    total_time = 0.0
    inputlist = []
    for i in range(generation_count):
        input_image_path ='./ROT/large_image_'+str(i)+'.png'#str(i)#
        image = Image.open(input_image_path)
        image_array = np.array(image)
        resized_image_array = resize_image(image_array, 1.1, 1.1)
        resized_image = Image.fromarray(resized_image_array.astype(np.uint8))
        start_time = time.time()
        output_image_path = f"./results/output_{os.getpid()}_{i}.jpg"
        #flipped_image.save(output_image_path)
        end_time = time.time()
        # Calculate elapsed time
        elapsed_time = end_time - start_time
        total_time += elapsed_time
    average_time = total_time / generation_count
    return {"AverageExecutionTime": average_time}
    
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
            result = imgres()
            et = time.time()
            Totalcnt += 10
            #print(et-st,flush=True)
            #print("processing",flush=True)
            #if et-lctime > 20:
            logger.info("PKTP of CPU num" +" "+ str(number) + " in past around 5 sec is"  + " "+str((Totalcnt-Totalprev)/(et-lctime)) +" " + "The latest standalone latency is " + str(et-st))
            lctime = time.time()
            Totalprev = Totalcnt
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
    NewMask = [0]*23
    for i in range(4,10):
         NewMask[i] = 1
    # #Inithere
    controller(RedisDataClient, FuncName, Control_Sign,
    #            NewMask, CPUMASK,RunningProcessesDict,)
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
    FuncName = 'res'
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

