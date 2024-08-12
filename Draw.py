CFuncList = ["alu", "pyae", "che", "res",  "web"]
MFuncList= ["omp","rot", "mls", "mlt", "vid"]

import random
from itertools import combinations


def select_random_elements(list1, list2, n):
    if n <= 1 or n > len(list1) + len(list2):
        print("Invalid input: n must be between 2 and the sum of the lengths of both lists.")
        return

    results = []
    for i in range(1, n):
        if i < len(list1) and (n - i) < len(list2):
            combinations_list1 = list(combinations(list1, i))
            combinations_list2 = list(combinations(list2, n - i))
            # 对于每种可能的i值，随机选择一个组合
            combo1 = random.choice(combinations_list1)
            combo2 = random.choice(combinations_list2)
            results.append(list(combo1) + list(combo2))

    # 从结果中随机选择一个输出
    if results:
        print(random.choice(results))
    else:
        print("No valid combinations found.")
#
# #select_random_elements(CFuncList, MFuncList, 2)
# # for i in range(10):
# #     select_random_elements(CFuncList, MFuncList, 2)
print("=========================================")
# for i in range(5):
#     select_random_elements(CFuncList, MFuncList, 4)
