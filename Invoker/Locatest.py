import os
import time
import multiprocessing as mp
def subprocess(interval):
    print(os.sched_getaffinity(0),flush=True)
    os.sched_setaffinity(0, {2})
    print(os.sched_getaffinity(0),flush=True)
    time.sleep(100)

if __name__ == '__main__':
    #mainprocess here
    mp.set_start_method('spawn')
    interval = 5
    subprocessEx = mp.Process(target=subprocess,args=(interval,))
    subprocessEx.start()
    print(os.sched_getaffinity(0), flush=True)
    subprocessEx.join()
