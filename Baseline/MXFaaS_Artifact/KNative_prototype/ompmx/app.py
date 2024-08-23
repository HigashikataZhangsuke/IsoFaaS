import numpy as np
from cython_omp import xcopy, xscale, xadd, xtriad

def lambda_handler():
    STREAM_ARRAY_SIZE = 20000000
    NTIMES = 10
    OFFSET = 0
    STREAM_TYPE = 'double'

    a = np.empty((STREAM_ARRAY_SIZE + OFFSET,), dtype=STREAM_TYPE)
    b = np.empty((STREAM_ARRAY_SIZE + OFFSET,), dtype=STREAM_TYPE)
    c = np.empty((STREAM_ARRAY_SIZE + OFFSET,), dtype=STREAM_TYPE)
    scalar = 3.0
    for k in range(NTIMES):
        #xcopy(a, c)
        #xscale(b, c, scalar)
        #xadd(a, b, c)
        xtriad(a, b, c, scalar)
        b += np.random.default_rng().random(b.shape) * 1e-6
        c += np.random.default_rng().random(c.shape) * 1e-6
    return {"Ok": "done"}
