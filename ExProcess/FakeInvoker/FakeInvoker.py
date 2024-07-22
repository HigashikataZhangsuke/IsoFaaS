#The Fake Invoker which will working on give instructions for testing. This is the main control logic parts.
#Also, Testing applying the MBA/CAT here.

import json
import redis
import logging
import time
import random
RedisMessageClient =redis.Redis(host='invokermessagesvc.default.svc.cluster.local', port=6379,decode_responses=True)

#Generate Mask continuosly(Which means the CPU allocated)
#Remember Each time you generate a new Mask, you will do MBA and CAT allocation First.
#Yeah Maybe just a loop.
#For testing, fistly, you try to apply SLO very very loose, so only the rate is the key here. You can find out the perf by doing the pktp test(Note that if oversubmission, you will assign more reqs to the
#Shareable parts. This is not good for showing the results)
#Maybe we need to think about SLO to be infinity to mask this problem first, yes!

# 不断检查队列
#Unit test use LoopCnt start from 1.
LoopCnt = 4
def random_k_integers(k):
    # 确保 k 的值在合理范围内
    if k > 24:
        raise ValueError("k cannot be larger than the range of numbers (0-23)")
    if k < 0:
        raise ValueError("k cannot be negative")
    # 从 0 到 23 的数字中随机抽取 k 个不同的数
    result = random.sample(range(23), k)
    output = [0] * 23
    # 遍历result，将output中对应的元素设置为1
    for index in result:
        output[index] = 1
    return output

#while LoopCnt<12:
AssignedMask = random_k_integers(LoopCnt)
print(AssignedMask)
print('Gonna Change')
    #print(AssignedMask)
    #Send the Mask Dict to Exclusive
CPUMASK = {
    'Alu': AssignedMask
}
RedisMessageClient.publish('UpdateChannel',json.dumps(CPUMASK))
print('send correctly')
time.sleep(50)
LoopCnt+=4
      # 防止CPU过载，可根据需要调整

#Then, tunning SLO to see what happens, and the results.