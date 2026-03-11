#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Clean & normalise the ONS Postcode Directory into a slim, API-friendly dimension table.

Defaults:
  Input  : app/data/ONS Postcode Directory.csv
  Output : app/data/clean_data/dim_postcode.csv
Optional:
  --parquet        -> also writes app/data/clean_data/dim_postcode.parquet
  --keep-historic  -> keep terminated (historic) postcodes as well as live ones
"""

import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# ------------------ Constants ------------------
# ONS uses "S99999999" (and sometimes blanks) to represent nulls in many code columns.
NULL_TOKEN = "S99999999"
CHUNKSIZE  = 150_000   # adjust if you have more/less memory
UK_BOUNDS  = {"lon_min": -8.8, "lon_max": 2.8, "lat_min": 49.0, "lat_max": 61.5}

# Columns to keep -> concise names for your dimension table
# All names below must match your file's header row exactly (case & punctuation).
COLMAP = {
    "Postcode (7 char)": "postcode7",
    "Postcode (8 char)": "postcode8",
    "Postcode (e-GIF)": "postcode_egif",

    "Date of Introduction": "date_introduced",
    "Date of Termination": "date_terminated",
    "Postcode User Type": "user_type",

    "National Grid Reference (Easting)": "easting",
    "National Grid Reference (Northing)": "northing",
    "Latitude": "lat",
    "Longitude": "lon",
    "Grid Reference Positional Quality Indicator": "positional_quality",

    "Local Authority District Code (2025)": "lad_2025",
    "Ward Code (2025)": "ward_2025",
    "Parish and Non-Civil Parished Area Code (2025)": "parish_2025",

    "Output Area Code (2021)": "oa_2021",
    "Lower layer Super Output Area Code (2021)": "lsoa_2021",
    "Middle layer Super Output Area Code (2021)": "msoa_2021",

    "NHS England Region Code (2024)": "nhs_region_2024",
    "Integrated Care Board Code (2023)": "icb_2023",
    "Sub Integrated Care Board Location Code (2024)": "sub_icb_2024",
    "Cancer Alliance Code (2024)": "cancer_alliance_2024",

    "Police Force Area Code (2023)": "police_2023",
    "Index of Multiple Deprivation Indicator (2020)": "imd_2020",

    "Travel to Work Area Code (2015)": "ttwa_2015",
    "International Territorial Level Code (2025)": "itl_2025",
    "Built-up Area Code (2024)": "bua_2024",

    "Local Enterprise Partnership Code (2021) (1st instance)": "lep2021_1",
    "Local Enterprise Partnership Code (2021) (2nd instance)": "lep2021_2",
}

NUMERIC_INT = ["easting", "northing", "positional_quality", "imd_2020"]
NUMERIC_FLOAT = ["lat", "lon"]
DATE_INT_YYYYMM = ["date_introduced", "date_terminated"]


def parse_args():
    p = argparse.ArgumentParser(
        "Clean & normalise ONS Postcode Directory → app/data/clean_data/"
    )
    # Default input is your app/data location (note the space in the filename).
    p.add_argument(
        "--input", type=Path, default=Path("../app/data/ONS Postcode Directory.csv"),
        help='Path to the ONS CSV (default: "app/data/ONS Postcode Directory.csv")'
    )
    p.add_argument(
        "--out-dir", type=Path, default=Path("../app/data/clean_data"),
        help="Output directory (default: app/data/clean_data)"
    )
    p.add_argument(
        "--filename", type=str, default="dim_postcode.csv",
        help="Output filename (default: dim_postcode.csv)"
    )
    p.add_argument(
        "--parquet", action="store_true",
        help="Also write Parquet as dim_postcode.parquet in the same folder"
    )
    p.add_argument(
        "--keep-historic", action="store_true",
        help="Keep terminated postcodes too (default keeps only live)"
    )
    return p.parse_args()


def normalise_chunk(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a chunk:
      - Trim headers
      - Convert ONS null sentinel + blanks to NaN
      - Keep/rename a curated set of columns
      - Fix dtypes
      - Drop rows outside UK lat/lon bounds
      - Normalise postcode7 (uppercase/trim)
    """
    # Trim header names
    df_raw.columns = [c.strip() for c in df_raw.columns]
    # Replace null sentinels and empty strings with NaN
    df = df_raw.replace({NULL_TOKEN: np.nan, "": np.nan})

    # Select & rename to concise schema
    keep = [c for c in COLMAP.keys() if c in df.columns]
    df = df[keep].rename(columns=COLMAP)

    # Types
    for c in NUMERIC_INT:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce", downcast="integer")
    for c in NUMERIC_FLOAT:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in DATE_INT_YYYYMM:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")

    # UK bounds sanity check on coordinates (drop outliers)
    if {"lat", "lon"}.issubset(df.columns):
        m = (
            df["lon"].between(UK_BOUNDS["lon_min"], UK_BOUNDS["lon_max"]) &
            df["lat"].between(UK_BOUNDS["lat_min"], UK_BOUNDS["lat_max"])
        )
        df = df[m]

    # Canonical postcode key: uppercase, trimmed
    if "postcode7" in df.columns:
        df["postcode7"] = df["postcode7"].astype("string").str.strip().str.upper()

    return df


def resolve_duplicates(df: pd.DataFrame, keep_historic: bool) -> pd.DataFrame:
    """
    Resolve duplicates per postcode7.
    - Default (keep_historic=False): prefer non-terminated rows (date_terminated is NA),
      otherwise keep the most recently introduced.
    - If keep_historic=True: keep all distinct (postcode7, date_introduced, date_terminated) rows.
    """
    if not keep_historic:
        df["_terminated"] = df["date_terminated"].notna()
        df = (
            df.sort_values(["_terminated", "date_introduced"], ascending=[True, False])
              .drop_duplicates(subset=["postcode7"], keep="first")
              .drop(columns=["_terminated"])
        )
    else:
        df = df.drop_duplicates(subset=["postcode7", "date_introduced", "date_terminated"])
    return df


def main():
    args = parse_args()

    # Ensure paths
    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input.resolve()}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = args.out_dir / args.filename

    parts = []
    # Read as strings to preserve alphanumeric codes like 'S12000033' intact.
    for chunk in pd.read_csv(args.input, dtype=str, low_memory=False, chunksize=CHUNKSIZE):
        parts.append(normalise_chunk(chunk))

    if not parts:
        print("No rows read — please check the input file.")
        return

    # Combine & resolve duplicates
    df = pd.concat(parts, ignore_index=True)
    df = resolve_duplicates(df, keep_historic=args.keep_historic)

    # Consistent column order
    ordered = list(COLMAP.values())
    cols = [c for c in ordered if c in df.columns]
    df = df[cols]

    # Save CSV
    df.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"Saved {len(df):,} rows → {out_csv}")

    # Optional Parquet
    if args.parquet:
        out_pq = args.out_dir / "dim_postcode.parquet"
        try:
            df.to_parquet(out_pq, index=False)
            print(f"Saved Parquet → {out_pq}")
        except Exception as e:
            print(f"Parquet write failed ({e}). "
                  f"Install pyarrow or fastparquet to enable Parquet output.")


if __name__ == "__main__":
    main()