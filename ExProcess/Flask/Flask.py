#Flask frontend for IsoContainer. Note it will responsible for both Ex and She. So will split the traffic based on the
#Exclusive SLO violation rate.
#Could use the previous code.
import time
import redis
from flask import Flask, request, jsonify
import json
from multiprocessing import Process,Manager
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import uuid

RedisExDataClient = redis.Redis(host='aludatasvc.default.svc.cluster.local', port=6379, db=0,decode_responses=True)
RedisShDataClient = redis.Redis(host='shdatasvc.default.svc.cluster.local', port=6379, db=0,decode_responses=True)
RedisFlaskClient = redis.Redis(host='aludatasvc.default.svc.cluster.local', port=6379, db=1)

#So one possible problem is that SLO is really tight then how would you like to split. Current one may not good. Discuss tomorrow.
manager = Manager()
shared_dict = manager.dict()

app = Flask(__name__)
def fetch_rate(shared_dict):
    rate = RedisFlaskClient.get('ExSLOVio')
    if rate:
        shared_dict['rate'] = 1-float(rate)
    else:
        shared_dict['rate'] = 1.0  # 如果未找到rate，默认值为1.0

Cnt = 0

@app.route('/', methods=['POST'])
def receive_event():
    global Cnt
    global shared_dict
    #if Cnt%100 ==0:
    #    rate = shared_dict.get('rate', 1.0)  # 从共享字典获取rate，默认为1.0
    #Setting here.
    #Ori Data = dict(FuncName,FuncString,'SLO')
    data = request.get_json()
    #SLOscale = 0.1
    #Unpack and add SLO here!
    FuncName = data.get('FuncName')
    FuncString = data.get('FuncString')
    #print(FuncString,flush=True)
    NewSLO = time.time() + data.get('SLO')
    newdata = {"FuncName": FuncName,
            "FuncString": FuncString,
             "SLO": NewSLO}
    #if uuid.uuid4().int % 100 < rate * 100:
            # 分配给RedisExDataClient
    RedisExDataClient.rpush('Alu', json.dumps(newdata))
    #else:
            # 分配给RedisShDataClient
    #    RedisShDataClient.rpush('ShChannel', json.dumps(newdata))
    Cnt+=1
    return 'OK', 200

if __name__ == "__main__":
    shared_dict['rate'] = 1.0
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_rate, 'interval', seconds=3, args=[shared_dict,])
    #scheduler.start()
    app.run(host='0.0.0.0', port=12346)
    #scheduler.shutdown()