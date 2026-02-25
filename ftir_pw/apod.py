# ftir_pw/apod.py
import numpy as np


def next_power_of_two(n: int) -> int:
    p = 1
    while p < int(n):
        p *= 2
    return p


# Blackman–Harris Windows

def blackman_harris_B3(N: int) -> np.ndarray:
    """
    3-term Blackman–Harris (OPUS B3 equivalent).
    Coefficients match validated script.
    """
    a0, a1, a2 = 0.42323, 0.49755, 0.07922
    if N <= 1:
        return np.ones(N, dtype=float)

    k = np.arange(N, dtype=float)
    return (
        a0
        - a1 * np.cos(2 * np.pi * k / (N - 1))
        + a2 * np.cos(4 * np.pi * k / (N - 1))
    )


# def blackman_harris_BH2(N: int) -> np.ndarray:
#     """
#     2-term Blackman–Harris window.
#     """
#     a0, a1 = 0.54, 0.46
#     if N <= 1:
#         return np.ones(N, dtype=float)

#     k = np.arange(N, dtype=float)
#     return a0 - a1 * np.cos(2 * np.pi * k / (N - 1))



# Window Dispatcher
def get_window_by_name(name: str, N: int) -> np.ndarray:
    n = str(name).strip().lower()

    # Boxcar
    if n in ("boxcar", "rect", "rectangle", "none"):
        return np.ones(N, dtype=float)

    # Hann / Hanning
    if n in ("hann", "hanning"):
        return np.hanning(N)

    # Hamming
    if n == "hamming":
        return np.hamming(N)

    # Blackman–Harris
    if n in ("b3", "blackmanharris3", "blackman-harris3", "bh3", "blackmanharris", "blackman-harris"):
        return blackman_harris_B3(N)

    if n in ("bh2", "blackmanharris2", "blackman-harris2"):
        return blackman_harris_BH2(N)

    raise ValueError(f"Unknown apod/window name: {name}")