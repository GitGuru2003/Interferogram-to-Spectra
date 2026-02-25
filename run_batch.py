import os
import csv
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
from brukeropus import read_opus

from ftir_pw.processing import process_bidirectional_pw, ratio_to_absorbance
from ftir_pw.metrics import interp_and_metrics, mean_spacing, find_peak


ALLOWED_EXTS = {
    ".0",".1",".2",".3",".4",".5",".6",".7",".8",
    ".0001",".0002",".0003",".0004",".0005",".0006",".0007"
}

def get_param(params, key, default=None):
    for k in (key, key.lower(), key.upper()):
        try:
            return params[k]
        except Exception:
            pass
    return default

def process_one_file(path: str, apod: str, zf: int):
    """
    Worker-safe function: returns a dict (metrics row).
    Never raises: returns status=FAIL with error.
    """
    row = {
        "path": path,
        "apod": apod,
        "zf": int(zf),
        "status": "OK",
        "error": "",
    }
    try:
        op = read_opus(path)
        params = op.params

        lwn = float(get_param(params, "lwn"))
        lfq = float(get_param(params, "lfq"))
        hfq = float(get_param(params, "hfq"))

        ifg_sample = np.array(op.igsm.y, dtype=float)
        ifg_ref    = np.array(op.igrf.y, dtype=float)

        wn_opus = np.array(op.a.x, dtype=float)
        A_opus  = np.array(op.a.y, dtype=float)

        wn_tmp, sb_s, sb_r = process_bidirectional_pw(ifg_sample, ifg_ref, lwn, zf, apod)
        wn_out, A_out, _   = ratio_to_absorbance(wn_tmp, sb_s, sb_r, hfq, lfq)

        rms, mae, mx = interp_and_metrics(wn_out, A_out, wn_opus, A_opus)

        row.update({
            "lwn": lwn, "hfq": hfq, "lfq": lfq,
            "points": int(len(wn_out)),
            "mean_dnu_cm-1": float(mean_spacing(wn_out)),
            "peak_cm-1": float(find_peak(wn_out, A_out)[0]),
            "peak_A": float(find_peak(wn_out, A_out)[1]),
            "rms_vs_opus": float(rms),
            "mae_vs_opus": float(mae),
            "maxabs_vs_opus": float(mx),
        })
        return row

    except Exception as e:
        row["status"] = "FAIL"
        row["error"] = (repr(e)[:500])  # keep it bounded
        # Fill numeric fields so CSV stays consistent
        row.update({
            "lwn": "", "hfq": "", "lfq": "",
            "points": "", "mean_dnu_cm-1": "",
            "peak_cm-1": "", "peak_A": "",
            "rms_vs_opus": "", "mae_vs_opus": "", "maxabs_vs_opus": "",
        })
        return row

def list_opus_files(data_dir: str):
    files = []
    for name in os.listdir(data_dir):
        p = os.path.join(data_dir, name)
        if not os.path.isfile(p):
            continue
        _, ext = os.path.splitext(name)
        if ext in ALLOWED_EXTS:
            files.append(p)
    files.sort()
    return files

def load_done_set(csv_path: str):
    done = set()
    if not os.path.exists(csv_path):
        return done
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        if "path" not in r.fieldnames:
            return done
        for row in r:
            done.add(row["path"])
    return done

def append_row(csv_path: str, fieldnames, row: dict):
    write_header = not os.path.exists(csv_path)
    with open(csv_path, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        w.writerow(row)

def main():
    ap = argparse.ArgumentParser(description="Batch-run FTIR pipeline on many OPUS files.")
    ap.add_argument("--data", default="Data", help="Data directory containing OPUS files")
    ap.add_argument("--apod", default="b3", help="Apodization (e.g., b3)")
    ap.add_argument("--zf", type=int, default=2, help="Zero-fill factor (e.g., 2)")
    ap.add_argument("--out", default="Results", help="Output directory")
    ap.add_argument("--workers", type=int, default=6, help="Process workers")
    ap.add_argument("--resume", action="store_true", help="Skip files already in batch_metrics.csv")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    metrics_csv  = os.path.join(args.out, "batch_metrics.csv")
    failures_csv = os.path.join(args.out, "batch_failures.csv")

    files = list_opus_files(args.data)
    print(f"Found {len(files)} candidate OPUS files in {args.data}/")

    done = load_done_set(metrics_csv) if args.resume else set()
    if args.resume:
        print(f"Resume enabled: {len(done)} already processed (from {metrics_csv})")

    todo = [p for p in files if p not in done]
    print(f"To process: {len(todo)} files")

    fieldnames = [
        "path","apod","zf","status","error",
        "lwn","hfq","lfq",
        "points","mean_dnu_cm-1","peak_cm-1","peak_A",
        "rms_vs_opus","mae_vs_opus","maxabs_vs_opus"
    ]

    # Parallel run
    ok = fail = 0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(process_one_file, p, args.apod, args.zf) for p in todo]
        for i, fut in enumerate(as_completed(futs), start=1):
            row = fut.result()
            append_row(metrics_csv, fieldnames, row)
            if row["status"] == "OK":
                ok += 1
            else:
                fail += 1
                append_row(failures_csv, fieldnames, row)

            if i % 200 == 0:
                print(f"Progress: {i}/{len(todo)} | OK={ok} FAIL={fail}")

    print(f"Done. OK={ok} FAIL={fail}")
    print(f"Metrics:  {metrics_csv}")
    print(f"Failures: {failures_csv}")

if __name__ == "__main__":
    main()