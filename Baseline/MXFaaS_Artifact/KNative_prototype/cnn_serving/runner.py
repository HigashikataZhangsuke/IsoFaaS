import json
import os
import sys
import signal
import threading
import socket
import numpy as np
import time
import signal
import numa
import torch
from torchvision import models, transforms
from PIL import Image
import os
import json
import time
#from azure.storage.blob import BlobServiceClient, BlobClient
torch.set_num_threads(1)

# 限制 MKL 和 OpenMP 使用的线程数
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
#connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
#blob_service_client = BlobServiceClient.from_connection_string(connection_string)
#container_client = blob_service_client.get_container_client("artifacteval")

def signal_handler(sig, frame):
    serverSocket_.close()
    sys.exit(0)


class PrintHook:
    def __init__(self,out=1):
        self.func = None
        self.origOut = None
        self.out = out

    def TestHook(self,text):
        f = open('hook_log.txt','a')
        f.write(text)
        f.close()
        return 0,0,text

    def Start(self,func=None):
        if self.out:
            sys.stdout = self
            self.origOut = sys.__stdout__
        else:
            sys.stderr= self
            self.origOut = sys.__stderr__
            
        if func:
            self.func = func
        else:
            self.func = self.TestHook

    def Stop(self):
        self.origOut.flush()
        if self.out:
            sys.stdout = sys.__stdout__
        else:
            sys.stderr = sys.__stderr__
        self.func = None

    def flush(self):
        self.origOut.flush()
  
    def write(self,text):
        proceed = 1
        lineNo = 0
        addText = ''
        if self.func != None:
            proceed,lineNo,newText = self.func(text)
        if proceed:
            if text.split() == []:
                self.origOut.write(text)
            else:
                if self.out:
                    if lineNo:
                        try:
                            raise "Dummy"
                        except:
                            codeObject = sys.exc_info()[2].tb_frame.f_back.f_code
                            fileName = codeObject.co_filename
                            funcName = codeObject.co_name     
                self.origOut.write(newText)

def MyHookOut(text):
    return 1,1,' -- pid -- '+ str(os.getpid()) + ' ' + text

# Global variables
serverSocket_ = None # serverSocket
actionModule = None # action module

checkTable = {}
mapPIDtoLeader = {}
checkTableShadow = {}
valueTable = {}
mapPIDtoIO = {}
lockCache = threading.Lock()

lockPIDMap = threading.Lock()
requestQueue = [] # queue of child processes
mapPIDtoStatus = {} # map from pid to status (running, waiting)

responseMapWindows = [] # map from pid to response

affinity_mask = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,16,17,18,19,20,21,22,23}


def lambda_handler(model,labels_path):
    torch.set_num_threads(1)

    # 限制 MKL 和 OpenMP 使用的线程数
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['NUMEXPR_NUM_THREADS'] = '1'
    
    model.eval()  # 设置为评估模式
    # 下载ImageNet标签文件

    with open(labels_path, 'r') as f:
        labels = json.load(f)
    input_dir = './Res/'  # 修改为包含图片的目录路径
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

# The function to update the core nums by request. 
def updateThread():
    # Shared vaiable: numCores
    global numCores

    # Bind to 0.0.0.0:5500
    myHost = '0.0.0.0'
    myPort = 5500 

    # Create a socket
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    # Handle request
    while True:
        # Accept a connection
        (clientSocket, _) = serverSocket.accept()
        data_ = clientSocket.recv(1024)
        dataStr = data_.decode('UTF-8')
        dataStrList = dataStr.splitlines()
        message = json.loads(dataStrList[-1])
        
        # Get the numCores and update the global variable
        numCores = message["numCores"]
        result = {"Response": "Ok"}
        msg = json.dumps(result)

        # Send the result and close the socket
        response_headers = {
            'Content-Type': 'text/html; encoding=utf8',
            'Content-Length': len(msg),
            'Connection': 'close',
        }

        response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())

        response_proto = 'HTTP/1.1'
        response_status = '200'
        response_status_text = 'OK'

        r = '%s %s %s\r\n' % (response_proto, response_status, response_status_text)

        clientSocket.send(r.encode(encoding="utf-8"))
        clientSocket.send(response_headers_raw.encode(encoding="utf-8"))
        clientSocket.send('\r\n'.encode(encoding="utf-8"))
        clientSocket.send(msg.encode(encoding="utf-8"))

        clientSocket.close()

def myFunction(data_, clientSocket_,model,labels_path):
    global actionModule
    global numCores
    
    dataStr = data_.decode('UTF-8')
    dataStrList = dataStr.splitlines()
    numCoreFlag = False
    try:
        message = json.loads(dataStrList[-1])
        numCores = int(message["numCores"])
        numCoreFlag = True
        result = {"Response": "Ok"}
        msg = json.dumps(result)
    except:
        pass
    torch.set_num_threads(1)

# 限制 MKL 和 OpenMP 使用的线程数
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['NUMEXPR_NUM_THREADS'] = '1'
    # Set the main function
    if numCoreFlag == False:
        st = time.time()
        #result = actionModule.lambda_handler()
        result = lambda_handler(model,labels_path)
        et = time.time()
        print("LTS "+ str(et-st),flush=True)
        # Send the result (Test Pid)
        result["myPID"] = os.getpid()
        msg = json.dumps(result)

        
    response_headers = {
        'Content-Type': 'text/html; encoding=utf8',
        'Content-Length': len(msg),
        'Connection': 'close',
    }

    response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())

    response_proto = 'HTTP/1.1'
    response_status = '200'
    response_status_text = 'OK' # this can be random

    # sending all this stuff
    r = '%s %s %s\r\n' % (response_proto, response_status, response_status_text)
    try:
        clientSocket_.send(r.encode(encoding="utf-8"))
        clientSocket_.send(response_headers_raw.encode(encoding="utf-8"))
        clientSocket_.send('\r\n'.encode(encoding="utf-8")) # to separate headers from body
        clientSocket_.send(msg.encode(encoding="utf-8"))
    except:
        clientSocket_.close()
    clientSocket_.close()



def waitTermination(childPid):
    # wait for the running child process to exit
    os.waitpid(childPid, 0)
    for responseTime in responseMapWindows:
        if responseTime[0] == childPid:
            responseTime[1][1] = time.time()
            break
    lockPIDMap.acquire()
    requestQueue.remove(childPid)
    try:
        mapPIDtoStatus.pop(childPid)
    except:
        pass
    for index in range(len(requestQueue)):
        # Find the first waiting child process and run it.
        if(mapPIDtoStatus[requestQueue[index]] == "waiting"):
            mapPIDtoStatus[requestQueue[index]] = "running"
            try:
                os.kill(requestQueue[index], signal.SIGCONT)
                break
            except:
                pass
    lockPIDMap.release()
#We do not have any IO
# def performIO(clientSocket_):
#     global mapPIDtoStatus
#     global numCores
#     global checkTable
#     global mapPIDtoIO
#     global valueTable
#     global checkTableShadow
#     global mapPIDtoLeader
#
#     data_ = b''
#     data_ += clientSocket_.recv(1024)
#     dataStr = data_.decode('UTF-8')
#
#     while True:
#         dataStrList = dataStr.splitlines()
#
#         message = None
#         try:
#             message = json.loads(dataStrList[-1])
#             break
#         except:
#             data_ += clientSocket_.recv(1024)
#             dataStr = data_.decode('UTF-8')
#
#     operation = message["operation"]
#     blobName = message["blobName"]
#     blockedID = message["pid"]
#
#     my_id = threading.get_native_id()
#
#     #blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
#
#     lockPIDMap.acquire()
#     mapPIDtoStatus[blockedID] = "blocked"
#     for child in mapPIDtoStatus.copy():
#         if child in mapPIDtoStatus:
#             if mapPIDtoStatus[child] == "waiting":
#                 mapPIDtoStatus[child] = "running"
#                 try:
#                     os.kill(child, signal.SIGCONT)
#                     break
#                 except:
#                     pass
#     lockPIDMap.release()
#
#     if operation == "get":
#         lockCache.acquire()
#         if blobName in checkTable:
#             myLeader = mapPIDtoLeader[blobName]
#             myEvent = threading.Event()
#             mapPIDtoIO[my_id] = myEvent
#             checkTable[blobName].append(my_id)
#             checkTableShadow[myLeader].append(my_id)
#             lockCache.release()
#             myEvent.wait()
#             lockCache.acquire()
#             blob_val = valueTable[myLeader]
#             mapPIDtoIO.pop(my_id)
#             checkTableShadow[myLeader].remove(my_id)
#             if len(checkTableShadow[myLeader]) == 0:
#                 checkTableShadow.pop(myLeader)
#                 valueTable.pop(myLeader)
#             lockCache.release()
#         else:
#             mapPIDtoLeader[blobName] = my_id
#             checkTable[blobName] = []
#             checkTableShadow[my_id] = []
#             checkTable[blobName].append(my_id)
#             #lockCache.release()
#             #blob_val = (blob_client.download_blob()).readall()
#             #lockCache.acquire()
#             #valueTable[my_id] = blob_val
#             checkTable[blobName].remove(my_id)
#             for elem in checkTable[blobName]:
#                 mapPIDtoIO[elem].set()
#             checkTable.pop(blobName)
#             lockCache.release()
#
#         full_blob_name = blobName.split(".")
#         proc_blob_name = full_blob_name[0] + "_" + str(blockedID) + "." + full_blob_name[1]
#         #with open(proc_blob_name, "wb") as my_blob:
#         #    my_blob.write(blob_val)
#     else:
#         fReadname = message["value"]
#         fRead = open(fReadname,"rb")
#         value = fRead.read()
#         #blob_client.upload_blob(value, overwrite=True)
#         #blob_val = "none"
#
#     lockPIDMap.acquire()
#     numRunning = 0 # number of running processes
#     for child in mapPIDtoStatus.copy():
#         if mapPIDtoStatus[child] == "running":
#             numRunning += 1
#     if numRunning < numCores:
#         mapPIDtoStatus[blockedID] = "running"
#         os.kill(blockedID, signal.SIGCONT)
#     else:
#         mapPIDtoStatus[blockedID] = "waiting"
#         os.kill(blockedID, signal.SIGSTOP)
#     lockPIDMap.release()
#
#     messageToRet = json.dumps({"value":"OK"})
#     try:
#         os.kill(blockedID, signal.SIGCONT)
#     except:
#         pass
#     clientSocket_.send(messageToRet.encode(encoding="utf-8"))
#     try:
#         os.kill(blockedID, signal.SIGCONT)
#     except:
#         pass
#     # clientSocket_.close()

def performIO(clientSocket_):
    global mapPIDtoStatus
    global numCores
    global checkTable
    global mapPIDtoIO
    global valueTable
    global checkTableShadow
    global mapPIDtoLeader

    data_ = b''
    while True:
        try:
            data_ += clientSocket_.recv(1024)
            dataStr = data_.decode('UTF-8')
            dataStrList = dataStr.splitlines()
            message = json.loads(dataStrList[-1])
            break  # 成功解析到消息后退出循环
        except json.JSONDecodeError:
            # 如果数据不完整，继续接收
            continue
        except socket.error:
            # 如果出现接收错误，退出循环
            break

    # 这里只保留对消息的简单响应和解锁逻辑
    operation = message.get("operation", "default_operation")
    blobName = message.get("blobName", "default_blob")
    blockedID = message.get("pid", -1)

    if blockedID != -1:
        lockPIDMap.acquire()
        mapPIDtoStatus[blockedID] = "blocked"
        for child in mapPIDtoStatus.copy():
            if child in mapPIDtoStatus and mapPIDtoStatus[child] == "waiting":
                mapPIDtoStatus[child] = "running"
                try:
                    os.kill(child, signal.SIGCONT)
                    break
                except:
                    pass
        lockPIDMap.release()

    # 这里是你需要保留的代码，做一些简单的处理即可
    messageToRet = json.dumps({"value": "OK"})
    clientSocket_.send(messageToRet.encode(encoding="utf-8"))
    clientSocket_.close()

    lockPIDMap.acquire()
    numRunning = sum(1 for status in mapPIDtoStatus.values() if status == "running")
    if numRunning < numCores and blockedID != -1:
        mapPIDtoStatus[blockedID] = "running"
        os.kill(blockedID, signal.SIGCONT)
    elif blockedID != -1:
        mapPIDtoStatus[blockedID] = "waiting"
        os.kill(blockedID, signal.SIGSTOP)
    lockPIDMap.release()


def IOThread():
    myHost = '0.0.0.0'
    myPort = 3333

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, _) = serverSocket.accept()
        threading.Thread(target=performIO, args=(clientSocket,)).start()

def run():
    # serverSocket_: socket 
    # actionModule:  the module to execute
    # requestQueue: 
    # mapPIDtoStatus: store status for each process (waiting / running)
    global serverSocket_
    global actionModule
    global requestQueue
    global mapPIDtoStatus
    global numCores
    global responseMapWindows
    global affinity_mask
    # Set the core of mxcontainer
    numCores = 24
    os.sched_setaffinity(0, affinity_mask)
    numa.memory.set_membind_nodes(0)
    print("Welcome... ", numCores)
    model = models.resnet50(pretrained=True)
    labels_url = 'https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json'
    labels_path = 'imagenet_labels.json'
    if not os.path.exists(labels_path):
        import urllib.request
        urllib.request.urlretrieve(labels_url, labels_path)
    # Set the address and port, the port can be acquired from environment variable
    myHost = '0.0.0.0'
    myPort = int(os.environ.get('PORT', 9999))

    # Bind the address and port
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    # serverSocket_ = serverSocket
    
    # Set actionModule
    import app
    actionModule = app

    # Set the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Redirect the stdOut and stdErr
    phOut = PrintHook()
    phOut.Start(MyHookOut)


    # Monitor numCore update
    threadUpdate = threading.Thread(target=updateThread)
    threadUpdate.start()

    # Monitor I/O Block
    #threadIntercept = threading.Thread(target=IOThread)
    #threadIntercept.start()

    # If a request come, then fork.
    while(True):
        
        (clientSocket, address) = serverSocket.accept()
        print("Accept a new connection from %s" % str(address), flush=True)
        
        data_ = b''

        data_ += clientSocket.recv(1024)

        dataStr = data_.decode('UTF-8')

        if 'Host' not in dataStr:
            msg = 'OK'
            response_headers = {
                'Content-Type': 'text/html; encoding=utf8',
                'Content-Length': len(msg),
                'Connection': 'close',
            }
            response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())

            response_proto = 'HTTP/1.1'
            response_status = '200'
            response_status_text = 'OK' # this can be random

            # sending all this stuff
            r = '%s %s %s\r\n' % (response_proto, response_status, response_status_text)
            try:
                clientSocket.send(r.encode(encoding="utf-8"))
                clientSocket.send(response_headers_raw.encode(encoding="utf-8"))
                clientSocket.send('\r\n'.encode(encoding="utf-8")) # to separate headers from body
                clientSocket.send(msg.encode(encoding="utf-8"))
                clientSocket.close()
                continue
            except:
                clientSocket.close()
                continue

        while True:
            dataStrList = dataStr.splitlines()
            
            message = None   
            try:
                message = json.loads(dataStrList[-1])
                break
            except:
                data_ += clientSocket.recv(1024)
                dataStr = data_.decode('UTF-8')
        
        responseFlag = False
        if message != None:

            if "numCores" in message:
                numCores = int(message["numCores"])
                result = {"Response": "Ok"}
                responseMapWindows = []
                if "affinity_mask" in message:
                    affinity_mask = message["affinity_mask"]
                    os.sched_setaffinity(0, affinity_mask)
                    numa.memory.set_membind_nodes(0)
                msg = json.dumps(result)
                responseFlag = True

            if "Q" in message:
                i = []
                for responseTime in responseMapWindows:
                    if responseTime[1][1] != -1:
                        i.append(responseTime[1][1] - responseTime[1][0])
                if len(i) == 0:
                    result={"p95": 0}
                else:
                    result = {"p95": np.percentile(i, 95)}
                result["affinity_mask"] = list(affinity_mask)
                result["numCores"] = numCores
                msg = json.dumps(result)
                responseFlag = True

            if "Clear" in message:
                responseMapWindows = []
                
        if responseFlag == True:
            response_headers = {
                'Content-Type': 'text/html; encoding=utf8',
                'Content-Length': len(msg),
                'Connection': 'close',
            }
            response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())

            response_proto = 'HTTP/1.1'
            response_status = '200'
            response_status_text = 'OK' # this can be random

            # sending all this stuff
            r = '%s %s %s\r\n' % (response_proto, response_status, response_status_text)

            clientSocket.send(r.encode(encoding="utf-8"))
            clientSocket.send(response_headers_raw.encode(encoding="utf-8"))
            clientSocket.send('\r\n'.encode(encoding="utf-8")) # to separate headers from body
            clientSocket.send(msg.encode(encoding="utf-8"))
            clientSocket.close()
            continue



        # a status mark of whether the process can run based on the free resources
        waitForRunning = False

        # The processes are running
        numIsRunning = 0

        lockPIDMap.acquire()
        for child in mapPIDtoStatus.copy():
            if mapPIDtoStatus[child] == "running":
                numIsRunning += 1
        if numIsRunning >= numCores:
            waitForRunning = True # The process need to wait for resources

        # slide windows
        if len(responseMapWindows) >=100:
            responseMapWindows.pop(0)

        childProcess = os.fork()
        if childProcess != 0:
            responseMapWindows.append([childProcess, [time.time(), -1]])

        if childProcess == 0:
            # begin fork
            myFunction(data_, clientSocket,model,labels_path)
            os._exit(os.EX_OK)
        else:
            # Append submit time to the responseMapWindows
            if waitForRunning:
                # If there is no free resources (cpu core) for the process to run, then we set the childprocess to sleep.
                mapPIDtoStatus[childProcess] = "waiting"
                os.kill(childProcess, signal.SIGSTOP)
            else:
                # If there are free resources (cpu core) for the process to run, then we let the childprocess to run.
                mapPIDtoStatus[childProcess] = "running"
            
            requestQueue.append(childProcess)
            lockPIDMap.release()
            # The childprocess is running, when it is finished, let the queue find waiting childprocesses
            threadWait = threading.Thread(target=waitTermination, args=(childProcess,))
            threadWait.start()
        #print("Running num is "+ str(numIsRunning),flush=True)
if __name__ == "__main__":
    # main program
    run()