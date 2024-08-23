import time
import cv2
import random
import os

os.sched_setaffinity(0, {6})

def alu():
    # It's OK since we think run locally and also use same data.
    video_list = [f for f in os.listdir(f'/home/ubuntu/IsoFaaS/Profiling/vid') if f.endswith('.mp4')]
    generation_count = 1

    total_time = 0.0

    for i in range(generation_count):
        video_name = video_list[i]
        video_path = os.path.join(f'/home/ubuntu/IsoFaaS/Profiling/vid', video_name)

        st = time.time()
        video = cv2.VideoCapture(video_path)

        width = int(video.get(3))
        height = int(video.get(4))
        fourcc = cv2.VideoWriter_fourcc(*'MPEG')
        out = cv2.VideoWriter('/home/ubuntu/IsoFaaS/Profiling/results/output_' + str(os.getpid()) + str(random.randint(1, 1000)) + '.avi', fourcc,
                              120.0, (width, height))

        # 用于存储所有灰度帧的列表
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
        #     # 增加内存访问频率
        #     out.write(gray_frame)

        video.release()
        out.release()
        et = time.time()

        elapsed_time = et - st
        total_time += elapsed_time

    average_time = total_time / generation_count
    return average_time

print("Now ready for BW Tests")
while True:
    alu()