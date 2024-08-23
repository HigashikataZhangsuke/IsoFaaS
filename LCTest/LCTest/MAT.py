import logging
import random
import redis
import time
import multiprocessing
import os
import json
import threading
import torch
from torchvision import models, transforms
from PIL import Image
import subprocess
import numpy as np
#Class

filename_A='matrix_A.npy'
filename_B='matrix_B.npy'
def Matmul():
    #n = 2500 #This should be far more bigger.?????
    #m = 2500
    #A = np.random.randint(low=1, high=10000, size=(n, m))
    #B = np.random.randint(low=1, high=10000, size=(m, n))
    #np.save(filename_A, A)
    #np.save(filename_B, B)
    start = time.time()
    A = np.load(filename_A)
    B = np.load(filename_B)
    col_idx = 259
    B_col = B[:, col_idx]  # B ?? col_idx ?, ?? (n,)
    
    # ?? A ? B_col ???, ???????? col_idx ?
    C = A.dot(B_col) 
    #n, m = A.shape[0], B.shape[1]  # ?? A ???? B ???
    #C = np.zeros((n, 1))
    #j = 0  # ?????? 0(??????)
    #for i in range(n):  # ?? A ????
    #    for k in range(A.shape[1]):  # ?? A ??? B ??
    #        C[i][0] += A[i][k] * B[k][j]  # ?? C[i][0]
    #C = np.matmul(A,B)
    #C = np.dot(A,B)
    latency = time.time() - start
    return C
#os.sched_setaffinity(0, {6})
#st = time.time()
#results = Matmul()
#et = time.time()
#print(et-st,flush=True)
#os.sched_setaffinity(0, {6})
#while True:
#    st = time.time()
#    results = Matmul()
#    et = time.time()
#    print(et-st,flush=True)

def measure_throughput(duration_seconds):
    start_time = time.time()
    end_time = start_time + duration_seconds
    iterations = 0

    while time.time() < end_time:
        result = Matmul()  # Adjust as needed
        iterations += 1
    return iterations

def run_test():
    duration_seconds = 20  # Duration for each process
    for cpu_count in [1,4,8,12,16,20]:
    #1,4,8,12,16,
    #cpu_count = 4  # Number of CPUs to use
        #for i in range(3):
        with multiprocessing.Pool(cpu_count) as pool:
            results = pool.map(measure_throughput, [duration_seconds] * cpu_count)

        total_iterations = sum(results)
        print(f"Total iterations across all CPUs in {duration_seconds} seconds: {total_iterations/duration_seconds} with {cpu_count}")
        time.sleep(5)

if __name__ == "__main__":
    run_test()
