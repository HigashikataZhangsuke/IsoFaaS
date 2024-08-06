#Flask frontend for IsoContainer. Note it will responsible for both Ex and She. So will split the traffic based on the
#Exclusive SLO violation rate.
#Could use the previous code.
import threading
import time
import redis
from flask import Flask, request, jsonify
import json
from multiprocessing import Process,Manager
import logging
import uuid
import random
import os

FuncName = 'mls'
RedisDataClient = redis.Redis(host=FuncName+'datasvc.default.svc.cluster.local', port=6379, db=0,decode_responses=True)
RedisShDataClient = redis.Redis(host='shdatasvc.default.svc.cluster.local', port=6379, db=0,decode_responses=True)
RedisMessageClient = redis.Redis(host='invokermessagesvc.default.svc.cluster.local', port=6379,decode_responses=True)

#So one possible problem is that SLO is really tight then how would you like to split. Current one may not good. Discuss tomorrow.
def Listener(Ratio,MsgClient):
    global FuncName
    pubsub = MsgClient.pubsub()
    pubsub.subscribe(['RatioChannel'])
    Listening = True
    while Listening:
        # Add shutdown here.
        messagelist = pubsub.listen()
        if messagelist:
            # You got a message
            for message in messagelist:
                if message['type'] == 'message':
                    # You got a message passing data
                    RateDict = json.loads(message['data'])
                    # For the shutdown message, we simply set the CPUMASK to all zero(If we still keep the container alive could live later, Currently shut down)
                    if FuncName in RateDict:
                        # If you got a message for you
                        Ratio.value = RateDict[FuncName]
    pubsub.close()

app = Flask(__name__)
@app.route('/', methods=['POST'])
def receive_event():
    data = request.get_json()
    if random.random() > counter.value:
        RedisShDataClient.rpush('ShChannel', json.dumps(data))
    else:
        #PUt to Ex
        RedisDataClient.rpush(FuncName, json.dumps(data))
    return 'OK', 200

if __name__ == "__main__":
    AffinityId = random.randint(24, 47)
    os.sched_setaffinity(0, {AffinityId})
    manager = Manager()
    # 使用 Manager 创建一个共享的 Value
    counter = manager.Value('f', 1.000)
    L = threading.Thread(target=Listener, args=(counter,RedisMessageClient,))
    L.start()
    app.run(host='0.0.0.0', port=12346)

