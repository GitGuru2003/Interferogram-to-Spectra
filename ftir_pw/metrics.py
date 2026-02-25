import numpy as np

def interp_and_metrics(wn_proc_desc, A_proc_desc, wn_opus, A_opus):
    wno = np.asarray(wn_opus, dtype=float).copy()
    Ao  = np.asarray(A_opus, dtype=float).copy()

    # ensure ascending for interp axis
    if wno[0] > wno[-1]:
        wno = wno[::-1]
        Ao  = Ao[::-1]

    wn_p = np.asarray(wn_proc_desc, dtype=float)
    A_p  = np.asarray(A_proc_desc, dtype=float)

    if len(wn_p) < 2:
        return float("nan"), float("nan"), float("nan")

    # wn_proc_desc is typically descending; make ascending for interp
    if wn_p[0] > wn_p[-1]:
        wn_p = wn_p[::-1]
        A_p  = A_p[::-1]

    A_interp = np.interp(wno, wn_p, A_p)
    diff = Ao - A_interp

    rms = float(np.sqrt(np.mean(diff**2)))
    mae = float(np.mean(np.abs(diff)))
    mx  = float(np.max(np.abs(diff)))
    return rms, mae, mx

def mean_spacing(wn_desc):
    wn = np.asarray(wn_desc, dtype=float)
    if len(wn) < 2:
        return float("nan")
    return float(np.mean(np.abs(np.diff(wn))))

def find_peak(wn, A):
    wn = np.asarray(wn, dtype=float)
    A  = np.asarray(A, dtype=float)
    if len(wn) == 0:
        return float("nan"), float("nan")
    i = int(np.argmax(A))
    return float(wn[i]), float(A[i])