import multiprocessing as mp
import time


def worker(Perf_Cnter_All):
    for i in range(5):
        Perf_Cnter_All[2] += 1
    print(Perf_Cnter_All,flush=True)

if __name__ == '__main__':
    manager = mp.Manager()
    Perf_Cnter_All = manager.list()
    for i in range(3):
        Perf_Cnter_All.append(0)
    np = mp.Process(target=worker,args=(Perf_Cnter_All,))
    np.start()
    time.sleep(10)
    np.join()