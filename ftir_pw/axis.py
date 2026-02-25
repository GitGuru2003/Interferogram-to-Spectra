import numpy as np

def wn_axis_rfft(nfft: int, lwn: float) -> np.ndarray:
    # For an interferogram sampled in OPD, wavenumber axis for rFFT:
    # d_opd = 1/(2*lwn) cm per sample (matches your previous assumption)
    d_opd = 1.0 / (2.0 * float(lwn))
    return np.fft.rfftfreq(int(nfft), d=d_opd)