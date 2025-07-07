#!/usr/bin/env python3
"""
scripts/csv_merger.py

Merge two CSV sources of trim variants into a single master_map,
and (optionally) dump it to master_map.json for later use.
"""

import os
import csv
import json
from collections import defaultdict

# adjust this import path if utils.py lives elsewhere
from utils import normalize_text


def load_trim_csv(path, variant_col, code_col=None):
    """
    Reads a CSV of trims and returns a dict:
      { (make,model,year): { normalized_variant: canonical_code, … }, … }

    If code_col is None, we use variant.upper() as the canonical code.
    """
    mapping = defaultdict(dict)
    with open(path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            make   = row['make'].strip()
            model  = row['model'].strip()
            year   = int(row['year'])
            raw_var= row[variant_col].strip()
            norm   = normalize_text(raw_var)
            if code_col and row.get(code_col):
                code = row[code_col].strip().upper()
            else:
                code = norm.upper()
            mapping[(make, model, year)][norm] = code
    return mapping

def build_master_map(extracted_csv, generic_csv):
    """
    Load two CSV files and merge their mappings into one master_map.
    """
    extracted_map = load_trim_csv(extracted_csv, variant_col="cluster_seed")
    generic_map   = load_trim_csv(generic_csv,   variant_col="trim")
    master_map    = defaultdict(dict)
    for src in (extracted_map, generic_map):
        for key, var2code in src.items():
            master_map[key].update(var2code)
    return master_map




if __name__ == "__main__":
    # Determine paths relative to this script
    BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
    EXTRACTED_CSV = os.path.join(BASE_DIR, "clustered_trim_variants.csv")
    GENERIC_CSV   = os.path.join(BASE_DIR, "trim_ref.csv")
    OUTPUT_JSON   = os.path.join(BASE_DIR, "master_map.json")

    # Build the master map
    master_map = build_master_map(EXTRACTED_CSV, GENERIC_CSV)

    # Print a quick summary
    print(f"Loaded {len(master_map)} (make,model,year) keys")
    sample = list(master_map.items())[:5]
    for (make, model, year), variants in sample:
        print(f"{make} {model} {year}: {len(variants)} variants")

    # Dump to JSON for later loading in your pipeline
    # Convert tuple keys to "make|model|year" strings
    serializable = {
        "|".join(map(str, key)): var2code
        for key, var2code in master_map.items()
    }
    with open(OUTPUT_JSON, "w", encoding='utf-8') as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)

    print(f"✅ Master map written to {OUTPUT_JSON}")
