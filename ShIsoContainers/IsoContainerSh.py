#According to the slides, now it's simpler, since the core are set, all you will tune is MBA and CAT
#Which is bind on the CPU, so no worrys about manage. You just need the worker
#Use exec to run the function(This solution is more realistic). Here, you assume the input of each request would be
#Input and their code in string
#You even do not need to have the updator right? Nothing need to be updated
#Just need to give a perform monitor, and send data to isoinvoker
#You will get #23 CPU. Only need to listen when to shut down.
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


import pandas as pd
from sklearn.linear_model import LogisticRegression
import joblib
import torch
from torchvision import models, transforms
import six
from chameleon import PageTemplate
import logging
import random
import redis
import time
import multiprocessing as mp
import os
import json
import threading
from PIL import Image
from cython_omp import xtriad
import numpy as np
import pyaes
import cv2
import collections
import uuid
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
    log_filename = f'Shprocess_{process_id}+{currtime}.log'
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    # 创建一个日志记录器
    logger = logging.getLogger(str(process_id))
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    return logger

def alu():
    #It's OK since we think run locally and also use same data.
    a = 506678
    b = 765467
    temp = 0
    for i in range(100000):
        if i % 4 == 0:
            temp = a + b
        elif i % 4 == 1:
            temp = a - b
        elif i % 4 == 2:
            temp = a * b
        else:
            temp = a / b
    return temp

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

def imgres():
    input_dir = './Res/'  # Modify this to your image directory
    image_list = os.listdir(input_dir)
    generation_count = 100

    total_time = 0.0
    list = []
    for i in range(generation_count):
        input_image_name = image_list[i % len(image_list)]
        input_image_path = os.path.join(input_dir, input_image_name)
        start_time = time.time()
        # Open and process the image
        image = Image.open(input_image_path)
        width, height = image.size
        # Set the crop area
        left = 4
        top = height / 5
        right = left + width / 2
        bottom = 3 * height / 5
        im1 = image.crop((left, top, right, bottom))
        # Perform multiple resize operations to increase memory bandwidth usage
        for j in range(10):
            new_width = width * (j + 1)
            new_height = height * (j + 1)
            im1 = im1.resize((new_width, new_height), Image.Resampling.LANCZOS)
        # Save the processed mage to a specified path
        list.append(im1)
        end_time = time.time()
        # Calculate elapsed time
        elapsed_time = end_time - start_time
        total_time += elapsed_time

    average_time = total_time / generation_count
    for i in range(len(list)):
        output_image_path = f"./results/output_{os.getpid()}_{i}.jpg"
        list[i].save(output_image_path)

    return {"AverageExecutionTime": average_time}

def imgrot():
    input_dir = './Res/'  # Modify this to your image directory
    image_list = os.listdir(input_dir)
    generation_count = 100

    total_time = 0.0
    list = []
    for i in range(generation_count):
        input_image_name = image_list[i % len(image_list)]
        input_image_path = os.path.join(input_dir, input_image_name)

        start_time = time.time()

        # Open and process the image
        image = Image.open(input_image_path)

        im1 = image.transpose(Image.ROTATE_90)
        im2 = im1.transpose(Image.ROTATE_90)
        im3 = im2.transpose(Image.ROTATE_90)
        list.append(im3)
        # im3.save(proc_image_path)
        # Save the processed image to a specified path
        # output_image_path = f"/home/ubuntu/Resultsbin/output_{os.getpid()}_{i}.jpg"
        # im3.save(proc_image_path)
        end_time = time.time()

        # Calculate elapsed time
        elapsed_time = end_time - start_time
        total_time += elapsed_time

    average_time = total_time / generation_count
    # output_image_path = f"/home/ubuntu/Resultsbin/output_{os.getpid()}_{i}.jpg"
    # im3.save(output_image_path)
    # Check if running on CPU 0-3 before writing to the file

    for i in range(len(list)):
        output_image_path = f"./results/output_{os.getpid()}_{i}.jpg"
        list[i].save(output_image_path)
    return {"AverageExecutionTime": average_time}

def MLserve():
    model = models.resnet50(pretrained=True)
    model.eval()  # 设置为评估模式
    # 下载ImageNet标签文件
    labels_url = 'https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json'
    labels_path = 'imagenet_labels.json'
    if not os.path.exists(labels_path):
        import urllib.request
        urllib.request.urlretrieve(labels_url, labels_path)
    with open(labels_path, 'r') as f:
        labels = json.load(f)
    input_dir = '/usr/src/app/Res/'  # 修改为包含图片的目录路径
    image_list = os.listdir(input_dir)
    generation_count = 1
    total_time = 0.0
    for i in range(generation_count):
        input_image_name = image_list[i % len(image_list)]
        image_path = os.path.join(input_dir, input_image_name)
        start_time = time.time()
        # 定义图像预处理过程
        preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        # 读取并处理图像
        image = Image.open(image_path)
        img_tensor = preprocess(image)
        img_tensor = img_tensor.unsqueeze(0)  # 批量化
        # 进行推断
        with torch.no_grad():
            outputs = model(img_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            top5_prob, top5_catid = torch.topk(probabilities, 5)
        inference = ''
        for j in range(top5_prob.size(0)):
            inference += 'With prob = %.5f, it contains %s. ' % (top5_prob[j].item(), labels[top5_catid[j].item()])
        exec_time = time.time() - start_time
        total_time += exec_time
    average_time = total_time / generation_count
    return {"result": inference, "average_execution_time": average_time}

def MLtrain():
    input_dir = './MLT/'
    csv_list = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    generation_count = 100

    total_time = 0.0

    for i in range(generation_count):
        input_csv_name = csv_list[i % len(csv_list)]
        input_csv_path = os.path.join(input_dir, input_csv_name)

        # 读取CSV文件
        df = pd.read_csv(input_csv_path)
        X = df[['X']].values
        Y = df['Y'].values

        start_time = time.time()

        # 训练逻辑回归模型
        model = LogisticRegression()
        model.fit(X, Y)

        end_time = time.time()

        # 保存模型到本地
        model_filename = f"./results/logistic_regression_model_{os.getpid()}.pkl"
        joblib.dump(model, model_filename)
        execution_time = end_time - start_time
        total_time += execution_time

    average_time = total_time / generation_count

    return {"AverageExecutionTime": average_time}

def omp():
    #It's OK since we think run locally and also use same data.
    STREAM_ARRAY_SIZE = 20000000
    NTIMES = 10
    OFFSET = 0
    STREAM_TYPE = 'double'

    a = np.empty((STREAM_ARRAY_SIZE + OFFSET,), dtype=STREAM_TYPE)
    b = np.empty((STREAM_ARRAY_SIZE + OFFSET,), dtype=STREAM_TYPE)
    c = np.empty((STREAM_ARRAY_SIZE + OFFSET,), dtype=STREAM_TYPE)
    scalar = 3.0
    for k in range(NTIMES):
        # xcopy(a, c)
        # xscale(b, c, scalar)
        # xadd(a, b, c)
        xtriad(a, b, c, scalar)
        b += np.random.random(b.shape) * 1e-6
        c += np.random.random(c.shape) * 1e-6
    return {"Ok": "done"}

def pyae():
    input_file = './generated_strings_500.txt'
    with open(input_file, 'r') as f:
        data = f.read().splitlines()

    # 128-bit key (16 bytes)
    KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'

    generation_count = 100

    start = time.time()
    for j in range(generation_count):
        message = data[j % len(data)]
        aes = pyaes.AESModeOfOperationCTR(KEY)
        ciphertext = aes.encrypt(message)
        aes = pyaes.AESModeOfOperationCTR(KEY)
        plaintext = aes.decrypt(ciphertext)
    end = time.time()

    average_time = (end - start) / generation_count
    return {"average_execution_time": average_time}

def vid():
    #It's OK since we think run locally and also use same data.
    video_list = [f for f in os.listdir(f'./vid') if f.endswith('.mp4')]
    generation_count = 1

    total_time = 0.0

    for i in range(generation_count):
        video_name = video_list[i]
        video_path = os.path.join(f'./vid', video_name)

        st = time.time()
        video = cv2.VideoCapture(video_path)

        width = int(video.get(3))
        height = int(video.get(4))
        fourcc = cv2.VideoWriter_fourcc(*'MPEG')
        out = cv2.VideoWriter('./output_' + str(os.getpid()) + str(random.randint(1, 1000)) + '.avi', fourcc,
                              120.0, (width, height))

        # 用于存储所有灰度帧的列表
        frames = []

        while video.isOpened():
            ret, frame = video.read()
            if ret:
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # frames.append(gray_frame)
                out.write(gray_frame)
            else:
                break

        # for gray_frame in frames:
        #     # 增加内存访问频率
        #     out.write(gray_frame)

        video.release()
        out.release()
        et = time.time()

        elapsed_time = et - st
        total_time += elapsed_time

    average_time = total_time / generation_count
    return average_time

def webserve():
    input_dir = './MLT/'
    csv_list = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    generation_count = 100

    total_time = 0.0

    for i in range(generation_count):
        input_csv_name = csv_list[i % len(csv_list)]
        input_csv_path = os.path.join(input_dir, input_csv_name)

        # 开始计时
        start_time = time.time()

        # 读取CSV文件
        df = pd.read_csv(input_csv_path)

        # 遍历奇数行并更新值
        for j in range(len(df)):
            if j % 2 != 0:  # 奇数行
                df.at[j, 'X'] += 1  # 更新X列的值
                df.at[j, 'Y'] += 1  # 更新Y列的值

        # 保存更新后的CSV文件
        updated_csv_path = os.path.join('./results/', f'updated_{input_csv_name}')
        df.to_csv(updated_csv_path, index=False)

        # 结束计时
        end_time = time.time()
        execution_time = end_time - start_time
        total_time += execution_time

    average_time = total_time / generation_count

    return {"average_execution_time": average_time}

#Basic execution unit, process. Thinking maybe just use exec for everyone? maybe
def workerprocess(RedisDataClient,Signal,ID,RedisMetricUpdateClient):
    #Once Init, it should always try to fetch and execute code. So currently I'm thinking the input is the string like func
    #Like everything here are already assigned to the string. no need for other requests.
    #You could modify scale here
    #Assuming Data has SLO also.
    os.sched_setaffinity(0, {23})
    # Do everything locally and then aggregation.
    # You need to tell the TP and your execution latency to us.
    # For TP, we keep the local print way. This could at least save 5% Peak Throughput.
    # Also to see if it's possible to use time.time() less.
    logger = setup_logging(os.getpid())
    lctime = time.time()
    logger.info(f"P+ {os.getpid()}+{lctime}+ starts logging")
    Totalcnt = [0]*10
    DQs = [collections.deque(maxlen=20) for _ in range(10)]
    PerfDict = {}
    FuncList = ["alu", "omp", "pyae", "che", "res", "rot", "mls", "mlt", "vid", "web"]
    while Signal.local_sign:
        result = RedisDataClient.blpop('ShChannel', 5)
        if result:
            _,data = json.loads(result)
            FuncName = data['FuncName']
            arrtime = data['ArrivalTime']
            match FuncName:
                case "alu":
                    st = time.time()
                    result = alu()
                    et = time.time()
                    Totalcnt[0] += 1
                    DQs[0].append(st-arrtime)
                    logger.info(f"P+ {os.getpid()}+ process alu request number + {Totalcnt[0]} + starts at + {st} + end at {et} + duration {et - st}")
                case "omp":
                    st = time.time()
                    result = omp()
                    et = time.time()
                    Totalcnt[1] += 1
                    DQs[1].append(st - arrtime)
                    logger.info(
                        f"P+ {os.getpid()}+ process omp request number + {Totalcnt[1]} + starts at + {st} + end at {et} + duration {et - st}")
                case "pyae":
                    st = time.time()
                    result = pyae()
                    et = time.time()
                    Totalcnt[2] += 1
                    DQs[2].append(st - arrtime)
                    logger.info(
                        f"P+ {os.getpid()}+ process pyae request number + {Totalcnt[2]} + starts at + {st} + end at {et} + duration {et - st}")
                case "che":
                    st = time.time()
                    result = che()
                    et = time.time()
                    Totalcnt[3] += 1
                    DQs[3].append(st - arrtime)
                    logger.info(
                        f"P+ {os.getpid()}+ process che request number + {Totalcnt[3]} + starts at + {st} + end at {et} + duration {et - st}")
                case "res":
                    st = time.time()
                    result = imgres()
                    et = time.time()
                    Totalcnt[4] += 1
                    DQs[4].append(st - arrtime)
                    logger.info(
                        f"P+ {os.getpid()}+ process res request number + {Totalcnt[4]} + starts at + {st} + end at {et} + duration {et - st}")
                case "rot":
                    st = time.time()
                    result = imgrot()
                    et = time.time()
                    Totalcnt[5] += 1
                    DQs[5].append(st - arrtime)
                    logger.info(
                        f"P+ {os.getpid()}+ process rot request number + {Totalcnt[5]} + starts at + {st} + end at {et} + duration {et - st}")
                case "mls":
                    st = time.time()
                    result = MLserve()
                    et = time.time()
                    Totalcnt[6] += 1
                    DQs[6].append(st - arrtime)
                    logger.info(
                        f"P+ {os.getpid()}+ process Mlserve request number + {Totalcnt[6]} + starts at + {st} + end at {et} + duration {et - st}")
                case "mlt":
                    st = time.time()
                    result = MLtrain()
                    et = time.time()
                    DQs[7].append(st - arrtime)
                    Totalcnt[7] += 1
                    logger.info(
                        f"P+ {os.getpid()}+ process Mltrain request number + {Totalcnt[7]} + starts at + {st} + end at {et} + duration {et - st}")
                case "vid":
                    st = time.time()
                    result = vid()
                    et = time.time()
                    DQs[8].append(st - arrtime)
                    Totalcnt[8] += 1
                    logger.info(
                        f"P+ {os.getpid()}+ process vid request number + {Totalcnt[8]} + starts at + {st} + end at {et} + duration {et - st}")
                case "web":
                    st = time.time()
                    result = webserve()
                    et = time.time()
                    DQs[9].append(st - arrtime)
                    Totalcnt[9] += 1
                    logger.info(
                        f"P+ {os.getpid()}+ process web request number + {Totalcnt[9]} + starts at + {st} + end at {et} + duration {et - st}")
            #Report to the isoinvoker every certain batches(running 100 reqs for all).
            if sum(Totalcnt) % 100 ==0:
                #Update E-E latencies.
                for i in range(10):
                    PerfDict[FuncList[i]] = sum(DQs[i])/len(DQs[i])
                PerfDict["ID"] = ID
                RedisMetricUpdateClient.publish("Metrics",json.dumps(PerfDict))

#The controller to tune worker and resource
def controller(RedisDataClient,ControlList,NewMask,RunningProcessesDict,ID,RedisMetricUpdateClient):
    #Controller is responsible for Tunning resource avaliablity based on the instruction from listener.
    #Ecerything is based on the CPUList the IsoInvoker given(Scale Up/Down)
    #Updateing here
    if NewMask ==1:
        np = mp.Process(target=workerprocess, args=(RedisDataClient, ControlList[0],ID,RedisMetricUpdateClient,))
        np.start()
        RunningProcessesDict[0] = np
    elif NewMask == 0:
        ControlList[0].signstop()
        RunningProcessesDict[0].terminate()
        RunningProcessesDict[0].join()

#The listener who are subscribe and trigger manager to tune workers
def listener(RedisDataClient,RedisMessageClient,RunningProcessesDict,ID,RedisMetricUpdateClient):
    #Init the connection to the IsoInvoker
    pubsub = RedisMessageClient.pubsub()
    pubsub.subscribe('UpdateChannel')
    #Init Workerlist and Controlist here
    #max_worker = 23
    Control_Sign = []
    #for i in range(max_worker):
    Control_Sign.append(ControlSign())
    #Simply Init here.
    NewMask = 1
    #NewMask[22] = 1
    #Inithere
    controller(RedisDataClient,  Control_Sign,
               NewMask, RunningProcessesDict,ID,RedisMetricUpdateClient)
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
                    if "Share" in CPUMASKDict:
                        #If you got a message for you, then it must be shutdown or start
                        NewMask = CPUMASKDict["Share"]
                        #print(NewMask,flush=True)
                        if NewMask == 1:
                            #start
                            controller(RedisDataClient, Control_Sign,
                                       NewMask, RunningProcessesDict,ID,RedisMetricUpdateClient )
                        elif NewMask == 0:
                           #Scale to zero, shutdown now. The other just keep the same.
                           #Call the controller function to stop.
                           controller(RedisDataClient,  Control_Sign,
                                      NewMask, RunningProcessesDict,ID,RedisMetricUpdateClient )
                           #Soft stop. Still listenining. But just not update perf metrics.
    pubsub.close()


if __name__ == '__main__':
    #As you are the IsoContainer for some function so you'd give the RedisClient here.
    #Note for Data Svc You need to provide such db
    #SLO
    AffinityId = random.randint(24, 47)
    os.sched_setaffinity(0, {AffinityId})
    manager = mp.Manager()
    ID = uuid.uuid4()
    RedisDataClient = redis.Redis(host='shdatasvc.default.svc.cluster.local', port=6379, db=0,decode_responses=True)
    #This shall be the same
    RedisMessageClient = redis.Redis(host='invokermessagesvc.default.svc.cluster.local', port=6379,decode_responses=True)
    RedisMetricUpdateClient = redis.Redis(host='shmessagesvc.default.svc.cluster.local', port=6379,decode_responses=True)
    #Different as different IsoContainer goes, need to change here.
    #LocalCPUMASK[3] = 1
    RunningProcessesDict = {}
    L =threading.Thread(target=listener,args=(RedisDataClient,RedisMessageClient,RunningProcessesDict,ID,RedisMetricUpdateClient,))
    L.start()
    #Join will only finish when you shutdown the container.
    L.join()
