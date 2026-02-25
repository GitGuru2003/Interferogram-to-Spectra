import os, csv
import argparse
import numpy as np
from brukeropus import read_opus

from .processing import process_bidirectional_pw, ratio_to_absorbance
from .metrics import interp_and_metrics, mean_spacing, find_peak
from .plotting import plot_abs, plot_compare


def get_param(params, key, default=None):
    for k in (key, key.lower(), key.upper()):
        try:
            return params[k]
        except Exception:
            pass
    return default


def run_file(
    opus_file: str,
    apod: str,
    zf: int,
    out_dir: str,
):
    op = read_opus(opus_file)
    params = op.params

    lwn = float(get_param(params, "lwn"))
    lfq = float(get_param(params, "lfq"))
    hfq = float(get_param(params, "hfq"))

    ifg_sample = np.array(op.igsm.y, dtype=float)
    ifg_ref    = np.array(op.igrf.y, dtype=float)

    wn_opus = np.array(op.a.x, dtype=float)
    A_opus  = np.array(op.a.y, dtype=float)

    # EXACT match pipeline
    wn_tmp, sb_s, sb_r = process_bidirectional_pw(
        ifg_sample, ifg_ref, lwn, zf, apod
    )
    wn_out, A_out, _ = ratio_to_absorbance(wn_tmp, sb_s, sb_r, hfq, lfq)

    rms, mae, mx = interp_and_metrics(wn_out, A_out, wn_opus, A_opus)
    N = len(wn_out)
    dnu = mean_spacing(wn_out)
    wn_pk, A_pk = find_peak(wn_out, A_out)

    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(opus_file))[0]
    safe_apod = apod.replace("-", "_")
    tag = f"{stem}_apod{safe_apod}_zf{zf}"

    plot_abs(
        wn_out, A_out,
        f"Absorbance — {stem} (apod={apod}, ZF={zf})",
        os.path.join(out_dir, f"absorb_{tag}.png"),
    )
    plot_compare(
        wn_out, A_out, wn_opus, A_opus,
        f"OPUS vs Processed — {stem}",
        os.path.join(out_dir, f"compare_{tag}.png"),
    )

    metrics = {
        "file": opus_file,
        "apod": apod,
        "zf": int(zf),
        "points": int(N),
        "mean_dnu_cm-1": float(dnu),
        "peak_cm-1": float(wn_pk),
        "peak_A": float(A_pk),
        "rms_vs_opus": float(rms),
        "mae_vs_opus": float(mae),
        "maxabs_vs_opus": float(mx),
    }

    csv_path = os.path.join(out_dir, f"metrics_{stem}.csv")
    write_header = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(metrics.keys()))
        if write_header:
            w.writeheader()
        w.writerow(metrics)

    return metrics


def build_parser():
    p = argparse.ArgumentParser(
        description="Exact-match pipeline to your accurate PW script (mid-split, B3/magnitude, mean DC)."
    )
    p.add_argument("opus_file", help="Path to OPUS file")
    p.add_argument("--apod", default="b3", help="Apod/window name (use 'b3' for OPUS B3)")
    p.add_argument("--zf", type=int, default=2, help="Zero-fill multiplier")
    p.add_argument("--out", default="Results", help="Output directory for plots/CSV")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    metrics = run_file(
        opus_file=args.opus_file,
        apod=args.apod,
        zf=args.zf,
        out_dir=args.out,
    )

    print("\n=== Metrics ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")
    print(f"\nSaved plots + CSV in: {os.path.abspath(args.out)}")