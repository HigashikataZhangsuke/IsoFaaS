import time
import numpy as np
from cython_omp import xtriad
def alu():
    # It's OK since we think run locally and also use same data.
    STREAM_ARRAY_SIZE = 20000000
    NTIMES = 10
    OFFSET = 0
    STREAM_TYPE = 'double'

    a = np.empty((STREAM_ARRAY_SIZE + OFFSET,), dtype=STREAM_TYPE)
    b = np.empty((STREAM_ARRAY_SIZE + OFFSET,), dtype=STREAM_TYPE)
    c = np.empty((STREAM_ARRAY_SIZE + OFFSET,), dtype=STREAM_TYPE)
    scalar = 3.0
    for k in range(NTIMES):
        # xcopy(a, c)
        # xscale(b, c, scalar)
        # xadd(a, b, c)
        xtriad(a, b, c, scalar)
        b += np.random.random(b.shape) * 1e-6
        c += np.random.random(c.shape) * 1e-6
    return {"Ok": "done"}

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