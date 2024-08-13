import time
import numpy as np
from sklearn.linear_model import LogisticRegression
import joblib
import pandas as pd
import os
def alu():
    input_dir = './MLT/'
    csv_list = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    generation_count = 100

    total_time = 0.0

    for i in range(generation_count):
        input_csv_name = csv_list[i % len(csv_list)]
        input_csv_path = os.path.join(input_dir, input_csv_name)

        # 读取CSV文件
        df = pd.read_csv(input_csv_path)
        X = df[['X']].values
        Y = df['Y'].values

        start_time = time.time()

        # 训练逻辑回归模型
        model = LogisticRegression()
        model.fit(X, Y)

        end_time = time.time()

        # 保存模型到本地
        model_filename = f"./results/logistic_regression_model_{os.getpid()}.pkl"
        joblib.dump(model, model_filename)
        execution_time = end_time - start_time
        total_time += execution_time

    average_time = total_time / generation_count

    return {"AverageExecutionTime": average_time}


listoftheresult = []
for i in range(5):
    st = time.time()
    result = alu()
    et = time.time()
    if i>1:
        listoftheresult.append(et-st)

print(sum(listoftheresult)/len(listoftheresult))
print("Now ready for BW Tests")
while True:
    alu()