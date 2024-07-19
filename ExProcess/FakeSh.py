#This is the Fake Share IsoContainer, it will be used for Fetching the requests dispatched to shareble queue, and record it.
import logging
import redis
import time
import json

# 设置日志
logging.basicConfig(filename='ShareSamplelog.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# 创建 Redis 连接
redis_client = redis.Redis(host='172.31.16.166', port=32283, db=0, decode_responses=True)

# 不断检查队列
while True:
    try:
        # 从队列中取出数据，如果10秒内无数据则超时返回
        Task = redis_client.blpop(['ShChannel'], timeout=10)
        if Task:
            # 处理数据
            logging.info(json.loads(Task))
            #data_dict = json.loads(Task)  # 注意：实际应用中应该使用 json.loads(data) 来确保安全
           # func_name = data_dict.get('FuncName')
            # 记录到日志
            #logging.info(f'Function Name: {func_name}')
    except Exception as e:
        logging.error(f'Error while processing data: {str(e)}')
    time.sleep(1)  # 防止CPU过载，可根据需要调整


