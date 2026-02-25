# FTIR PW-Mode Processing Pipeline (OPUS-Compatible)

A reproducible FTIR interferogram → absorbance processing pipeline designed to match the behavior of a Bruker OPUS workflow (midpoint forward/back split, Blackman–Harris B3 magnitude spectrum, mean DC removal, OPUS-range cropping).

This repository provides:

- A **single-file CLI** (`run_pw.py`) that generates plots + metrics
- A **batch runner** (`run_batch.py`) to process tens of thousands of OPUS files and write summary CSVs
- Modular code (`ftir_pw/`) for apodization, axis generation, processing, plotting, and metrics

---

## Key Features

- **Exact-match processing choices**
  - Midpoint split of interferogram into forward/backward halves
  - Backward half reversed before FFT
  - DC removal by subtracting the mean
  - Apodization window (default: `b3` = 3-term Blackman–Harris)
  - Zero-fill to `next_pow2(N) * ZF`
  - Real FFT (`rFFT`) and **magnitude** spectrum `|F|`
  - Single-beam ratio → transmittance → absorbance
  - Wavenumber sort descending for plotting
  - Crop to OPUS stored range using `HFQ/LFQ`

- **OPUS comparison metrics**
  - RMS error vs OPUS absorbance
  - MAE vs OPUS absorbance
  - Max absolute error vs OPUS absorbance
  - Peak location and peak absorbance
  - Mean wavenumber spacing

- **Batch processing**
  - Parallel execution (`ProcessPoolExecutor`)
  - Resume support (skip already-processed files)
  - Writes `batch_metrics.csv` and `batch_failures.csv`

---

## Repository Layout

```
.
├── Data/                   # OPUS files (not committed to git)
├── Results/                # Output CSVs and plots (usually gitignored)
├── ftir_pw/
│   ├── __init__.py
│   ├── apod.py             # Apodization windows + next_power_of_two
│   ├── axis.py             # Wavenumber axis for rFFT from laser wavenumber
│   ├── processing.py       # Mid-split PW processing + absorbance conversion
│   ├── metrics.py          # OPUS comparison metrics + helpers
│   ├── plotting.py         # Plot utilities
│   └── cli.py              # Single-file CLI (plots + per-file metrics CSV)
├── run_pw.py               # CLI entrypoint
├── run_batch.py            # Batch runner (CSV outputs)
├── requirements.txt
└── README.md
```

---

## Installation

### 1) Create and activate a virtual environment

**macOS/Linux:**
```bash
python -m venv .ftenv
source .ftenv/bin/activate
```

**Windows:**
```bash
python -m venv .ftenv
.ftenv\Scripts\activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** This project uses the [`brukeropus`](https://pypi.org/project/brukeropus/) Python package for reading OPUS files.

---

## Usage

### Process a single OPUS file

```bash
python run_pw.py Data/CM_Fiber_3_Reps0114082719.0 --apod b3 --zf 2 --out Results
```

This will:

- Read OPUS interferograms (`igsm`, `igrf`) and OPUS absorbance (`a`)
- Run the PW-style pipeline
- Generate plots in the output directory:
  - `absorb_<stem>_apod<apod>_zf<zf>.png`
  - `compare_<stem>_apod<apod>_zf<zf>.png`
- Append metrics to `Results/metrics_<stem>.csv`
- Print metrics to the terminal

### CLI arguments (single-file)

| Argument | Description |
|---|---|
| `opus_file` (positional) | Path to OPUS file |
| `--apod` | Apodization/window name (default: `b3`) |
| `--zf` | Zero-fill multiplier (default: `2`) |
| `--out` | Output directory (default: `Results`) |

---

### Run the pipeline on an entire folder (batch)

```bash
python run_batch.py --data Data --apod b3 --zf 2 --workers 6 --out Results
```

**Outputs:**
- `Results/batch_metrics.csv` (one row per processed file)
- `Results/batch_failures.csv` (rows with `status=FAIL`)

### Batch options

| Option | Description |
|---|---|
| `--data` | Directory containing OPUS files (default: `Data`) |
| `--apod` | Window name (default: `b3`) |
| `--zf` | Zero-fill multiplier (default: `2`) |
| `--workers` | Number of processes (default: `6`) |
| `--out` | Output directory (default: `Results`) |
| `--resume` | Skip files already present in `batch_metrics.csv` |

**Example resume run:**
```bash
python run_batch.py --data Data --apod b3 --zf 2 --workers 6 --resume
```

### Supported OPUS File Extensions (Batch)

The batch runner processes only these extensions (defined in `run_batch.py` as `ALLOWED_EXTS`):

```
.0  .1  .2  .3  .4  .5  .6  .7  .8
.0001  .0002  .0003  .0004  .0005  .0006  .0007
```

---

## Apodization / Window Names

Implemented in `ftir_pw/apod.py`.

| Name | Description |
|---|---|
| `b3` *(default)* | 3-term Blackman–Harris (OPUS-like B3 coefficients) |
| `hann` / `hanning` | Hann window |
| `hamming` | Hamming window |
| `boxcar` / `rect` / `rectangle` / `none` | Rectangular (no apodization) |

**Examples:**
```bash
python run_pw.py Data/CM_Fiber_3_Reps0114082719.0 --apod b3 --zf 2
python run_pw.py Data/CM_Fiber_3_Reps0114082719.0 --apod hann --zf 2
python run_pw.py Data/CM_Fiber_3_Reps0114082719.0 --apod boxcar --zf 2
```

---

## Processing Method (Exact-Match Pipeline)

Implemented in `ftir_pw/processing.py`.

### 1) Split bidirectional interferogram (midpoint)

For both sample and reference interferograms:

```
f = x[:mid]
b = x[mid:][::-1]
```

Trim to equal length.

### 2) One-direction transform

For each half:

1. DC removal: subtract mean
2. Multiply by apodization window
3. Zero-fill to `next_power_of_two(N) * zf`
4. Compute `np.fft.rfft()`
5. Take magnitude `|F|`

### 3) Average forward/back

Average the single-beam magnitudes from forward and backward halves independently for sample and reference:

```
SB_sample = 0.5 * (SB_sf + SB_sb)
SB_ref    = 0.5 * (SB_rf + SB_rb)
```

### 4) Transmittance and absorbance

```
T = SB_sample / SB_ref   (clipped for stability)
A = -log10(T)
```

### 5) Wavenumber axis

Computed from laser wavenumber `LWN` using:

```
d_opd = 1 / (2 * LWN)       # cm per sample
wn    = np.fft.rfftfreq(nfft, d=d_opd)
```

### 6) Sort & crop

- Sort wavenumbers descending (FTIR convention for plotting)
- Crop using OPUS range parameters `HFQ`/`LFQ` (robust to ordering)

---

## Metrics (vs OPUS absorbance)

Implemented in `ftir_pw/metrics.py`:

| Metric | Description |
|---|---|
| `rms_vs_opus` | RMSE of OPUS absorbance vs processed absorbance on OPUS grid |
| `mae_vs_opus` | Mean absolute error |
| `maxabs_vs_opus` | Maximum absolute error |
| `peak_cm-1`, `peak_A` | Max absorbance peak location and value |
| `mean_dnu_cm-1` | Mean spacing in the processed axis |

**Interpolation:**
- OPUS axis is made ascending if needed
- Processed axis is made ascending if needed
- `np.interp()` onto the OPUS grid

---

## Outputs

### Single-file (`run_pw.py`)

In the output folder (default `Results/`):

- `absorb_<stem>_apod<apod>_zf<zf>.png`
- `compare_<stem>_apod<apod>_zf<zf>.png`
- `metrics_<stem>.csv` (appended)

### Batch (`run_batch.py`)

- `Results/batch_metrics.csv`
- `Results/batch_failures.csv`