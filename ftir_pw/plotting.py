import os
import matplotlib.pyplot as plt

def plot_abs(wn, A, title, out_png):
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    plt.figure(figsize=(9,4))
    plt.plot(wn, A, lw=1.2)
    plt.gca().invert_xaxis()
    plt.xlabel("Wavenumber (cm$^{-1}$)")
    plt.ylabel("Absorbance")
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()

def plot_compare(wn_proc_desc, A_proc_desc, wn_opus, A_opus, title, out_png):
    os.makedirs(os.path.dirname(out_png), exist_ok=True)

    wn_op = wn_opus
    A_op  = A_opus
    if wn_op[0] < wn_op[-1]:
        wn_op = wn_op[::-1]
        A_op  = A_op[::-1]

    plt.figure(figsize=(9,4))
    plt.plot(wn_op, A_op, lw=1.1, label="OPUS")
    plt.plot(wn_proc_desc, A_proc_desc, '--', lw=1.1, label="Processed")
    plt.gca().invert_xaxis()
    plt.xlabel("Wavenumber (cm$^{-1}$)")
    plt.ylabel("Absorbance")
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()