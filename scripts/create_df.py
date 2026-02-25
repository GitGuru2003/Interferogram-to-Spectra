from pathlib import Path
import pandas as pd
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
source_dir = PROJECT_ROOT / "Data"


rows = []
for f in source_dir.rglob("*"):
    if not f.is_file():
        continue

    rel = f.relative_to(source_dir)
    parts = rel.parts  # tuple of folder names plus filename

    # Heuristic parsing
    # Example structure: Gar At-Line / 10hz / Gar / GCM 01142020 / <file>
    category = parts[0] if len(parts) >= 1 else None   # e.g., "Gar At-Line"
    hz = None
    product = None
    session_folder = None  # e.g., "GCM 01142020" (date/run folder)

    # find "10hz"/"40hz" anywhere in the path
    for p in parts:
        if p.lower().endswith("hz"):
            hz = p
            break

    # find product label "Gar" or "Woo" 
    for p in parts:
        if p in {"Gar", "Woo"}:
            product = p
            break

    # pick a likely "run/date" folder: something starting with GCM 
    for p in parts:
        if p.startswith("GCM"):
            session_folder = p
            break

    rows.append({
        "full_path": str(f.resolve()),
        "relative_path": str(rel),
        "filename": f.name,
        "stem": f.stem,
        "suffix": f.suffix,                 # extensions like ".0" or ".csv"
        "size_bytes": f.stat().st_size,
        "modified_time": datetime.fromtimestamp(f.stat().st_mtime),

        # Parsed metadata
        "category": category,               # e.g., Gar At-Line, Issues, Need Ref, etc.
        "hz": hz,                           # e.g., 10hz, 40hz
        "product": product,                 # Gar or Woo
        "session_folder": session_folder,   # e.g., "GCM 01142020"
        "depth": len(parts) - 1,            # how deep the file was nested
    })

df = pd.DataFrame(rows)

# Sort for readability
df = df.sort_values(["category", "hz", "product", "session_folder", "filename"], na_position="last").reset_index(drop=True)

print(df.head())
print("Total files:", len(df))


# Save outputs
out_dir = PROJECT_ROOT / "info_data"
out_dir.mkdir(exist_ok=True)

df.to_parquet(out_dir / "files_index.parquet", index=False)
df.to_csv(out_dir / "files_index.csv", index=False)
print("Saved to:", out_dir)
