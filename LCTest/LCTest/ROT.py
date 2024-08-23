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

    
def rotate_image(image_array, angle):
    angle_rad = np.deg2rad(angle)  # ????????
    rotation_matrix = np.array([[np.cos(angle_rad), -np.sin(angle_rad)], 
                                [np.sin(angle_rad),  np.cos(angle_rad)]])
    
    rows, cols = image_array.shape[:2]
    
    # ??????????,?????????
    coords = np.indices((rows, cols)).reshape(2, -1)
    coords_centered = coords - np.array([[rows // 2], [cols // 2]])

    # ????????????
    new_coords = np.dot(rotation_matrix, coords_centered)
    new_coords = new_coords + np.array([[rows // 2], [cols // 2]])
    new_coords = new_coords.astype(int)

    # ?????????
    rotated_image_array = np.zeros_like(image_array)

    # ???????????
    for channel in range(image_array.shape[2]):  # ????????
        valid_coords = (new_coords[0] >= 0) & (new_coords[0] < rows) & (new_coords[1] >= 0) & (new_coords[1] < cols)
        rotated_image_array[coords[0, valid_coords], coords[1, valid_coords], channel] = image_array[new_coords[0, valid_coords], new_coords[1, valid_coords], channel]
    return rotated_image_array

def imgrot():
   # os.sched_setaffinity(0, {6})
    generation_count = 1
    ls = []
    total_time = 0.0
    inputlist = []
    for i in range(generation_count):
        input_image_path ='./ROT/large_image_'+str(i)+'.png'
        image = Image.open(input_image_path)
        image_array = np.array(image)
        flipped_image_array = rotate_image(image_array, 180)
        flipped_image = Image.fromarray(flipped_image_array.astype(np.uint8))
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
#os.sched_setaffinity(0, {6})
#while True:
#    st = time.time()
#    results = imgrot()
#    et = time.time()
#    print(et-st,flush=True)

def measure_throughput(duration_seconds):
    start_time = time.time()
    end_time = start_time + duration_seconds
    iterations = 0

    while time.time() < end_time:
        result = imgrot()  # Adjust as needed
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


