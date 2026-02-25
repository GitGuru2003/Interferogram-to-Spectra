from pathlib import Path
import shutil

# Base folder 
source_dir = Path("Data")

# Destination folder 
destination_dir = Path("All_Extracted_Files")

destination_dir.mkdir(parents=True, exist_ok=True)

# Recursively go through ALL files in Data
num_files = 0
for file in source_dir.rglob("*"):
    if file.is_file():
        shutil.copy(file, destination_dir / file.name)
        num_files += 1

print("All files extracted.")
print(f"Total files extracted: {num_files}")
