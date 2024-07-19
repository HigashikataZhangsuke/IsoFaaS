import time
import multiprocessing

def alu(times):
    a = 506678
    b = 765467
    temp = 0
    for i in range(times):
        if i % 4 == 0:
            temp = a + b
        elif i % 4 == 1:
            temp = a - b
        elif i % 4 == 2:
            temp = a * b
        else:
            temp = a / b
    return temp

def measure_throughput(duration_seconds):
    start_time = time.time()
    end_time = start_time + duration_seconds
    iterations = 0

    while time.time() < end_time:
        alu(100000)  # Adjust as needed
        iterations += 1
    return iterations

def run_test():
    duration_seconds = 10  # Duration for each process
    cpu_count = 1  # Number of CPUs to use

    with multiprocessing.Pool(cpu_count) as pool:
        results = pool.map(measure_throughput, [duration_seconds] * cpu_count)

    total_iterations = sum(results)
    print(f"Total iterations across all CPUs in {duration_seconds} seconds: {total_iterations} with {cpu_count}")

if __name__ == "__main__":
    run_test()
