import time
os.sched_setaffinity(0, {6})
def alu():
    #It's OK since we think run locally and also use same data.
    a = 506678
    b = 765467
    temp = 0
    for i in range(100000):
        if i % 4 == 0:
            temp = a + b
        elif i % 4 == 1:
            temp = a - b
        elif i % 4 == 2:
            temp = a * b
        else:
            temp = a / b
    return temp

print("Now ready for BW Tests")
while True:
    alu()