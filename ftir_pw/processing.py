import numpy as np
from .apod import get_window_by_name, next_power_of_two
from .axis import wn_axis_rfft

SMALL_NUMBER_DEFAULT = 1e-12


def split_bidirectional_mid(x: np.ndarray):
    """
    EXACT match to your accurate script:
      - split interferogram in the middle
      - reverse the second half
      - trim to equal length
    Returns (forward, backward_reversed)
    """
    x = np.asarray(x, dtype=float)
    mid = len(x) // 2
    f = x[:mid]
    b = x[mid:][::-1]
    L = min(len(f), len(b))
    return f[:L], b[:L]


def process_one_direction_pw(
    x: np.ndarray,
    lwn: float,
    zf: int,
    window_name: str,
):
    """
    EXACT match to your accurate script:
      1) DC removal: subtract mean
      2) apodize using window_name
      3) zero-fill to next_power_of_two(len) * zf
      4) rFFT and take magnitude |F|
      5) wavenumber axis from lwn
    """
    d = np.asarray(x, dtype=float).copy()

    # 1) DC removal (mean)
    d -= d.mean()

    # 2) apodize
    w = get_window_by_name(window_name, len(d))
    d *= w

    # 3) zero-fill
    zf = max(1, int(zf))
    nfft = next_power_of_two(len(d)) * zf

    pad = np.zeros(int(nfft), dtype=float)
    pad[:len(d)] = d

    # 4) FFT magnitude (PW in your accurate script)
    F = np.fft.rfft(pad)
    sb = np.abs(F)

    # 5) wavenumber axis
    wn = wn_axis_rfft(nfft, lwn)
    return wn, sb


def process_bidirectional_pw(
    sample_ifg: np.ndarray,
    reference_ifg: np.ndarray,
    lwn: float,
    zf: int,
    window_name: str,
):
    """
    EXACT match to your accurate script:
      - midpoint split forward/back for sample and reference
      - process each half
      - average forward/back single beams
    """
    s_f, s_b = split_bidirectional_mid(sample_ifg)
    r_f, r_b = split_bidirectional_mid(reference_ifg)

    wn_sf, sb_sf = process_one_direction_pw(s_f, lwn, zf, window_name)
    wn_sb, sb_sb = process_one_direction_pw(s_b, lwn, zf, window_name)
    wn_rf, sb_rf = process_one_direction_pw(r_f, lwn, zf, window_name)
    wn_rb, sb_rb = process_one_direction_pw(r_b, lwn, zf, window_name)

    sb_s = 0.5 * (sb_sf + sb_sb)
    sb_r = 0.5 * (sb_rf + sb_rb)

    return wn_sf, sb_s, sb_r


def ratio_to_absorbance(
    wn: np.ndarray,
    sb_sample: np.ndarray,
    sb_ref: np.ndarray,
    hfq: float,
    lfq: float,
    small_number: float = SMALL_NUMBER_DEFAULT,
):
    """
    Same as your accurate script but with robust hfq/lfq handling.
    """
    sb_ref = np.maximum(sb_ref, small_number)
    T = np.clip(sb_sample / sb_ref, small_number, None)
    A = -np.log10(T)

    # sort descending (high -> low cm^-1) like your script
    idx = np.argsort(wn)[::-1]
    wn_d = wn[idx]
    A_d = A[idx]
    T_d = T[idx]

    # robust range crop (works regardless of hfq/lfq ordering)
    lo = min(float(hfq), float(lfq))
    hi = max(float(hfq), float(lfq))
    m = (wn_d >= lo) & (wn_d <= hi)

    return wn_d[m], A_d[m], T_d[m]