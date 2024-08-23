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
import time
from PIL import Image
import numpy as np
import random
import json
import numpy as np
Image.MAX_IMAGE_PIXELS = None
import multiprocessing as mp
np.seterr(all='warn')
import logging
import redis
import threading
from PIL import Image, ImageFilter
Image.MAX_IMAGE_PIXELS = None

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

def rotate_image(image_array, angle):
    angle_rad = np.deg2rad(angle)  # ????????
    rotation_matrix = np.array([[np.cos(angle_rad), -np.sin(angle_rad)], 
                                [np.sin(angle_rad),  np.cos(angle_rad)]])
    
    rows, cols = image_array.shape[:2]
    
    # ??????????,?????????
    coords = np.indices((rows, cols)).reshape(2, -1)
    coords_centered = coords - np.array([[rows // 2], [cols // 2]])

    # ????????????
    new_coords = np.dot(rotation_matrix, coords_centered)
    new_coords = new_coords + np.array([[rows // 2], [cols // 2]])
    new_coords = new_coords.astype(int)

    # ?????????
    rotated_image_array = np.zeros_like(image_array)

    # ???????????
    for channel in range(image_array.shape[2]):  # ????????
        valid_coords = (new_coords[0] >= 0) & (new_coords[0] < rows) & (new_coords[1] >= 0) & (new_coords[1] < cols)
        rotated_image_array[coords[0, valid_coords], coords[1, valid_coords], channel] = image_array[new_coords[0, valid_coords], new_coords[1, valid_coords], channel]
    return rotated_image_array

def imgrot():
   # os.sched_setaffinity(0, {6})
    generation_count = 1
    ls = []
    total_time = 0.0
    inputlist = []
    for i in range(generation_count):
        input_image_path ='./Res/large_image_'+str(i)+'.png'
        image = Image.open(input_image_path)
        image_array = np.array(image)
        flipped_image_array = rotate_image(image_array, 180)
        flipped_image = Image.fromarray(flipped_image_array.astype(np.uint8))
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
    logger.info(f"P+ {os.getpid()}+{lctime}+ starts logging")
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
            result = imgrot()
            et = time.time()
            Totalcnt += 10
            #print(et-st,flush=True)
            #print("processing",flush=True)
            #if et-lctime > 10:
            #    logger.info("PKTP of CPU num" +" "+ str(number) + " in past around 5 sec is"  + " "+str((Totalcnt-Totalprev)/(et-lctime)) +" " + "The latest standalone latency is " + str(et-st))
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

    #for timercnt in range(1,23):#[1,4,8,12,16,20]:#range(1,23):#[1,4,8,12,16,20]:##[1,4,8,12,16,20]:#
    #    NewMask = [0] * 23
    #    for index in range(timercnt):
    #        NewMask[index] = 1

    # for timercnt in range(23):
    NewMask = [0]*23
    for index in range(18,20):
        NewMask[index] = 1
    #NewMask[5] = 1
        #cpu_list = ','.join(str(cpu) for cpu, val in enumerate(NewMask) if val == 1)
        #subprocess.run(['sudo', 'pqos', '-a', f'core:1={cpu_list}'], check=True)
    #NewMask = [0]*23
    #NewMask[8] = 1
    controller(RedisDataClient, FuncName, Control_Sign,
                    NewMask, CPUMASK,RunningProcessesDict,)
        #print(NewMask, flush=True)
        #print(CPUMASK, flush=True)
    time.sleep(40)
    #time.sleep(1000000)
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
    FuncName = 'rot'
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

