import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import time
from PIL import Image
import numpy as np
import random
import json
import numpy as np
import joblib
Image.MAX_IMAGE_PIXELS = None
import multiprocessing
np.seterr(all='warn')

    
def resize_image(image_array, scale_x, scale_y):
    # ?????????
    rows, cols = image_array.shape[:2]
    
    # ??????
    scaling_matrix = np.array([[scale_x, 0], [0, scale_y]])

    # ??????,????????? (x, y)
    coords = np.indices((rows, cols)).reshape(2, -1)  # 2 x (rows * cols)

    # ????????????
    new_coords = np.dot(scaling_matrix, coords)  # 2 x (rows * cols)
    
    # ?????????,????????????
    new_rows = int(rows * scale_y)
    new_cols = int(cols * scale_x)

    # ????????????
    new_coords[0] = np.clip(new_coords[0], 0, new_rows - 1)
    new_coords[1] = np.clip(new_coords[1], 0, new_cols - 1)

    # ????????
    new_image_array = np.zeros((new_rows, new_cols, image_array.shape[2]), dtype=image_array.dtype)

    # ?? np.dot ????,?????? RGB ??
    for channel in range(1):
        # ??????????????
        new_image_array[new_coords[0].astype(int), new_coords[1].astype(int), channel] = image_array[coords[0], coords[1], channel]
    
    return new_image_array

def imgres():
    #os.sched_setaffinity(0, {6})
    generation_count = 10
    ls = []
    total_time = 0.0
    inputlist = []
    for i in range(generation_count):
        input_image_path ='./ROT/large_image_'+str(i)+'.png'#str(i)#
        image = Image.open(input_image_path)
        image_array = np.array(image)
        resized_image_array = resize_image(image_array, 1.1, 1.1)
        resized_image = Image.fromarray(resized_image_array.astype(np.uint8))
        start_time = time.time()
        output_image_path = f"./results/output_{os.getpid()}_{i}.jpg"
        #flipped_image.save(output_image_path)
        end_time = time.time()
        # Calculate elapsed time
        elapsed_time = end_time - start_time
        total_time += elapsed_time
    average_time = total_time / generation_count
    return {"AverageExecutionTime": average_time}

#if __name__ == "__main__":
    #run_test()

#while True:
#    st = time.time()
#    results = imgres()
#    et = time.time()
#    print(et-st,flush=True)

def measure_throughput(duration_seconds):
    start_time = time.time()
    end_time = start_time + duration_seconds
    iterations = 0

    while time.time() < end_time:
        result = imgres()  # Adjust as needed
        iterations += 10
    return iterations

def run_test():
    duration_seconds = 30  # Duration for each process
    for cpu_count in [1,19,20,21,22]:
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
    #os.sched_setaffinity(0, {6})
    #st = time.time()
    #results = imgres()
    #et = time.time()
    #print(et-st,flush=True)


