import subprocess
import time
from multiprocessing import Process
import os
def T1():
    for timercnt in [12]:
        NewMaskMLS = [0]*23
        start_index = 23 - timercnt
        end_index = 23

        for index in range(start_index, end_index):
            NewMaskMLS[index] = 1
        cpu_list = ','.join(str(cpu) for cpu, val in enumerate(NewMaskMLS) if val == 1)
        subprocess.run(['sudo', 'pqos', '-a', f'core:2={cpu_list}'], check=True)
        time.sleep(45)
def T2():
    for timercnt in [12]:
        NewMask = [0]*23
        for index in range(timercnt):
            NewMask[index] = 1
        cpu_list = ','.join(str(cpu) for cpu, val in enumerate(NewMask) if val == 1)
        subprocess.run(['sudo', 'pqos', '-a', f'core:1={cpu_list}'], check=True)
        time.sleep(45)

if __name__ == "__main__":
    os.sched_setaffinity(0, {34})
    subprocess.run(['sudo', 'pqos', '-R', 'mbaCtrl-on'], check=True)
    subprocess.run(['sudo', 'pqos', '-e', 'mba_max:1' + '=' + '14746', '-r'], check=True)
    subprocess.run(['sudo', 'pqos', '-e', 'mba_max:2' + '=' + '11746', '-r'], check=True)
    
    #sudo pqos -I -R mbaCtrl-on
    #14746/69735
    #9830/23245
    #14746/23245
    
    p1 = Process(target=T1)
    p2 = Process(target=T2)

    # 启动进程
    p1.start()
    p2.start()

    # 等待进程完成 (可选)
    p1.join()
    p2.join()
    
    