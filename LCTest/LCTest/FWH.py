import numpy as np
import multiprocessing
import os
import time
import math
import pickle
def fwht():
    n = 33000
    graph=np.load("regular_graph_adj_matrix.npy")
    # ??,???????????
    #out_degree = np.sum(graph, axis=1)
    out_degree = 10
    # ???PageRank?,????
    rank = np.ones(n) / n

    # ??PageRank?
    for _ in range(1):
        new_rank = np.ones(n) * 0.15 / n  # ???????PageRank?
        for i in range(10):
            # ?????????????PageRank??
            for j in range(n):
                if graph[j, i] == 1:
                    new_rank[i] += 0.85 * rank[j] /out_degree  # ????


        rank = new_rank

    return rank
        
def measure_throughput(duration_seconds):
    st = time.time()
    end_time = st + duration_seconds
    iterations = 0

    while time.time() < end_time:
        result = fwht()  # Adjust as needed
        iterations += 10
    #et = time.time()
    return iterations

def run_test():
    duration_seconds = 10  # Duration for each process
    for cpu_count in [1,17,18,19,20,21,22]:#[1,4,8,12,16,20]: #[17,18,19,20,21,22]:
        st = time.time()
        with multiprocessing.Pool(cpu_count) as pool:
            results = pool.map(measure_throughput, [duration_seconds] * cpu_count)
        et = time.time()
        total_iterations = sum(results)
        print(f"Total iterations across all CPUs in {duration_seconds} seconds: {total_iterations/(et-st)} with {cpu_count}")
        time.sleep(5)

if __name__ == "__main__":
    #run_test()
    os.sched_setaffinity(0, {6})
    while True:
    #st = time.time()
        results = fwht()
    #et = time.time()
    #print(et-st,flush=True)
