#for shareable resource, you need to send the ratio to flask, so that it can allocate reqs.
import json

def sendratio(ArrivalRate,ProfilingDataTp,CurrMask,Redisflaskclient,FuncList):
    # Arrivalrate: a dict stores function's arrival rate. If it is zero means not an alive funtion
    #FuncList = ["alu", "omp", "pyae", "che", "res", "rot", "mls", "mlt", "vid", "web"]
    #FuncList = ["alu", "mlt"]
    Ratio = {}
    for FuncName in FuncList:
        Ratio[FuncName] = ProfilingDataTp[FuncName][sum(CurrMask[FuncName])]/ArrivalRate[FuncName]
        if Ratio[FuncName]>1:
            #Since above 0.5 we give one more core
            Ratio[FuncName] = 1
    Redisflaskclient.publish('RatioChannel',json.dumps(Ratio))

#The second task is to collect sh's data, and do analysis.
def policymaker(Redisshmsgclient,ProfilingLatency,Clusterpolicy):
    #Proflinglatency is the list stores the stand alone function running execution latency.
    #When we find out that the scaling is reach the limit, i.e the perf of share part is too bad, we need to scale up it at cluster level.
    pubsub = Redisshmsgclient.pubsub()
    pubsub.subscribe("Metrics")
    while True:
        messagelist = pubsub.listen()
        if messagelist:
            # You got a message
            for message in messagelist:
                if message['type'] == 'message':
                    # You got a message passing data
                    PerfDict = json.loads(message['data'])
                    for Func in PerfDict:
                        if PerfDict[Func] > 1.2*ProfilingLatency[Func]:
                            Clusterpolicy[Func] = "ClusterScaleup"
                        else:
                            Clusterpolicy[Func] = "KeeporGC"