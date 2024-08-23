import time
import numpy as np
import os
from cython_omp import xtriad
os.sched_setaffinity(0, {6})
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


print("Now ready for BW Tests")
while True:
    alu()