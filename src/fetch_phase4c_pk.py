"""
fetch_phase4c_pk.py
===================
Phase 4C — Extended Replacement PK Dataset Harvester

Downloads and preserves raw longitudinal open-access pharmacokinetic (PK) benchmark datasets
from Rdatasets (nlme, datasets, pharmaversesdtm packages) into data/raw/replacement_pk/.

Datasets fetched:
  1. Theoph.csv (Theophylline PK)
  2. Indometh.csv (Indomethacin PK)
  3. Phenobarb.csv (Phenobarbital PK)
  4. Quinidine.csv (Quinidine PK)
  5. Remifentanil.csv (Remifentanil PK)
  6. Tetracycline1.csv (Tetracycline PK 1)
  7. Tetracycline2.csv (Tetracycline PK 2)
  8. Cefamandole.csv (Cefamandole PK)
  9. PC.csv (Xanomeline CDISC Pilot PK)

Usage:
    python src/fetch_phase4c_pk.py
"""

import os
import requests
import pandas as pd
from pathlib import Path

WORKSPACE_DIR = Path(__file__).parent.parent
RAW_REPLACEMENT_DIR = WORKSPACE_DIR / "data" / "raw" / "replacement_pk"
RAW_REPLACEMENT_DIR.mkdir(parents=True, exist_ok=True)

DATASET_SOURCES = {
    "Theoph.csv": "https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/datasets/Theoph.csv",
    "Indometh.csv": "https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/datasets/Indometh.csv",
    "Phenobarb.csv": "https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/nlme/Phenobarb.csv",
    "Quinidine.csv": "https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/nlme/Quinidine.csv",
    "Remifentanil.csv": "https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/nlme/Remifentanil.csv",
    "Tetracycline1.csv": "https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/nlme/Tetracycline1.csv",
    "Tetracycline2.csv": "https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/nlme/Tetracycline2.csv",
    "Cefamandole.csv": "https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/nlme/Cefamandole.csv",
    "PC.csv": "https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/pharmaversesdtm/pc.csv",
}

def fetch_datasets():
    print(f"Fetching raw extended benchmark PK datasets into {RAW_REPLACEMENT_DIR}...")
    manifest = []
    
    for filename, url in DATASET_SOURCES.items():
        dest_path = RAW_REPLACEMENT_DIR / filename
        print(f"Fetching {filename} from {url}...")
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                with open(dest_path, "wb") as f:
                    f.write(r.content)
                size = dest_path.stat().st_size
                print(f"  Successfully saved {filename} ({size} bytes)")
                manifest.append({
                    "filename": filename,
                    "url": url,
                    "status": "SUCCESS",
                    "bytes": size
                })
            else:
                print(f"  HTTP error {r.status_code} for {filename}")
                manifest.append({
                    "filename": filename,
                    "url": url,
                    "status": f"HTTP_{r.status_code}",
                    "bytes": 0
                })
        except Exception as e:
            print(f"  Failed to fetch {filename}: {e}")
            manifest.append({
                "filename": filename,
                "url": url,
                "status": f"ERROR: {e}",
                "bytes": 0
            })
            
    manifest_df = pd.DataFrame(manifest)
    manifest_df.to_csv(RAW_REPLACEMENT_DIR / "fetch_manifest.csv", index=False)
    print(f"Fetch manifest saved to {RAW_REPLACEMENT_DIR / 'fetch_manifest.csv'}")

if __name__ == "__main__":
    fetch_datasets()
