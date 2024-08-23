import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import logging
import random
import redis
import time
import multiprocessing
import json
import threading
import numpy as np
import cv2
np.seterr(all='warn')
def vid():
    #It's OK since we think run locally and also use same data.
    video_list = [f for f in os.listdir(f'./vid') if f.endswith('.avi')]
    generation_count = 1

    total_time = 0.0

    for i in range(generation_count):
        video_name = video_list[i]
        video_path = os.path.join(f'./vid', video_name)

        st = time.time()
        video = cv2.VideoCapture(video_path)

        width = int(video.get(3))
        height = int(video.get(4))
        fourcc = cv2.VideoWriter_fourcc(*'MPEG')
        out = cv2.VideoWriter('./result/output_' + str(os.getpid()) + str(random.randint(1, 1000)) + '.avi', fourcc,
                              120.0, (width, height))

        # ????????????
        frames = []

        while video.isOpened():
            ret, frame = video.read()
            if ret:
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # frames.append(gray_frame)
                out.write(gray_frame)
            else:
                break

        # for gray_frame in frames:
        #     # ????????
        #     out.write(gray_frame)

        video.release()
        out.release()
        et = time.time()

        elapsed_time = et - st
        total_time += elapsed_time

    average_time = total_time / generation_count
    return average_time

def set_affinity(cpu_id):
    """Set the CPU affinity for the current process."""
    pid = os.getpid()
    os.sched_setaffinity(pid, {cpu_id})

def measure_throughput(duration_seconds):
    start_time = time.time()
    end_time = start_time + duration_seconds
    iterations = 0

    while time.time() < end_time:
        result = vid()  # Run the video processing task
        iterations += 1
    return iterations

def run_test():
    duration_seconds = 20  # Duration for each process
    cpu_list = list(range(23))  # Available CPUs (adjust this as needed)

    for cpu_count in [1, 17, 18, 19, 20, 21, 22]:
        assigned_cpus = cpu_list[:cpu_count]  # Pick a unique set of CPUs
        with multiprocessing.Pool(cpu_count) as pool:
            results = pool.starmap(measure_throughput_with_affinity, [(duration_seconds, assigned_cpus[i]) for i in range(cpu_count)])

        total_iterations = sum(results)
        print(f"Total iterations across all CPUs in {duration_seconds} seconds: {total_iterations/duration_seconds} with {cpu_count}")
        time.sleep(5)

def measure_throughput_with_affinity(duration_seconds, cpu_id):
    """Measure throughput while ensuring the process is bound to a specific CPU."""
    set_affinity(cpu_id)  # Bind the process to a unique CPU
    return measure_throughput(duration_seconds)  # Run the workload


if __name__ == "__main__":
    run_test()
    #os.sched_setaffinity(0, {6})
    #while True:
    #    st = time.time()
    #    results = vid()
    #    et = time.time()
    #    print(et-st,flush=True)
    #st = time.time()
    #results = vid()
    #et = time.time()
    #print(et-st)