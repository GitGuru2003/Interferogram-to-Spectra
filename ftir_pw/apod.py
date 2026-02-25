import re
import numpy as np

def next_power_of_two(n: int) -> int:
    p = 1
    while p < int(n):
        p *= 2
    return p

def blackman_harris_B3(N: int) -> np.ndarray:
    a0, a1, a2 = 0.42323, 0.49755, 0.07922
    if N <= 1:
        return np.ones(N, dtype=float)
    k = np.arange(N, dtype=float)
    return a0 - a1*np.cos(2*np.pi*k/(N-1)) + a2*np.cos(4*np.pi*k/(N-1))

def _kaiser_window(N: int, beta: float) -> np.ndarray:
    return np.kaiser(N, beta)

def _poly_window(N: int, p: int) -> np.ndarray:
    p = max(0, int(p))
    if N <= 1:
        return np.ones(N, dtype=float)
    u = np.linspace(-1.0, 1.0, N, dtype=float)
    w = (1.0 - u*u)**p
    w[u < -1] = 0.0
    w[u >  1] = 0.0
    return w

def get_window_by_name(name: str, N: int) -> np.ndarray:
    n = str(name).strip().lower()

    if n in ("boxcar", "rect", "rectangle", "none"):
        return np.ones(N, dtype=float)
    if n in ("hann", "hanning"):
        return np.hanning(N)
    if n == "hamming":
        return np.hamming(N)
    if n in ("b3", "blackmanharris", "blackman-harris", "bh"):
        return blackman_harris_B3(N)

    # "kaiser-" naming (recommended, clearer than calling it NB)
    if n in ("kaiser-weak", "kaiser_w", "kaiserweak"):
        return _kaiser_window(N, 5.0)
    if n in ("kaiser-medium", "kaiser_m", "kaisermedium"):
        return _kaiser_window(N, 8.0)
    if n in ("kaiser-strong", "kaiser_s", "kaiserstrong"):
        return _kaiser_window(N, 12.0)

    m = re.match(r"kaiser-beta(\d+(\.\d+)?)", n)
    if m:
        return _kaiser_window(N, float(m.group(1)))

    m = re.match(r"poly(\d+)", n)
    if m:
        return _poly_window(N, int(m.group(1)))

    raise ValueError(f"Unknown apod/window name: {name}")