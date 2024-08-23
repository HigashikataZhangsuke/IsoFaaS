import time
import pandas as pd
import os

os.sched_setaffinity(0, {6})
def alu():
    input_dir = '/home/ubuntu/IsoFaaS/Profiling/MLT/'
    csv_list = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    generation_count = 100

    total_time = 0.0

    for i in range(generation_count):
        input_csv_name = csv_list[i % len(csv_list)]
        input_csv_path = os.path.join(input_dir, input_csv_name)

        # 开始计时
        start_time = time.time()

        # 读取CSV文件
        df = pd.read_csv(input_csv_path)

        # 遍历奇数行并更新值
        for j in range(len(df)):
            if j % 2 != 0:  # 奇数行
                df.at[j, 'X'] += 1  # 更新X列的值
                df.at[j, 'Y'] += 1  # 更新Y列的值

        # 保存更新后的CSV文件
        updated_csv_path = os.path.join('/home/ubuntu/IsoFaaS/Profiling/results/', f'updated_{input_csv_name}')
        df.to_csv(updated_csv_path, index=False)

        # 结束计时
        end_time = time.time()
        execution_time = end_time - start_time
        total_time += execution_time

    average_time = total_time / generation_count

    return {"average_execution_time": average_time}

print("Now ready for BW Tests")
while True:
    alu()