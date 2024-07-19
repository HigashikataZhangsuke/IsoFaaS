#This is the Fake Ex IsoContainer.
#So it's main usage is Provide a virtual SLO violation rate, and then it will just receive requests
import logging
import redis
import time
import json
import random

# 设置日志
logging.basicConfig(filename='ExSamplelog.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# 创建 Redis 连接
redis_client = redis.Redis(host='AluDataSvc.default.svc.cluster.local', port=6379, db=0,decode_responses=True)
RedisFlaskClient = redis.Redis(host='AluDataSvc.default.svc.cluster.local', port=6379, db=1,decode_responses=True)
# 不断检查队列
Cnt =0
while True:
    try:
        # 从队列中取出数据，如果10秒内无数据则超时返回
        key, data = redis_client.blpop(['Alu'], timeout=10)
        if data:
            # 处理数据
            data_dict = json.loads(data)  # 注意：实际应用中应该使用 json.loads(data) 来确保安全
            func_name = data_dict.get('FuncName')
            # 记录到日志
            logging.info(f'Function Name: {func_name}')

        if Cnt%100 ==0:
            RedisFlaskClient.set('ExSLOVio',random.random() )
    except Exception as e:
        logging.error(f'Error while processing data: {str(e)}')
    Cnt+=1
    time.sleep(0.1)  # 防止CPU过载，可根据需要调整


