import os
import glob
import pandas as pd
import numpy as np
from pathlib import Path

# ------------ SETTINGS ------------
RAW_DIR = Path("../app/data/crime_raw")           # where your raw monthly CSVs live
OUT_DIR = Path("../app/data/clean_data")         # output directory
OUT_FILE = OUT_DIR / "crime_hotspot_cities_clean.csv"

# Filter by policing authority (appears in "Falls within" and often "Reported by")
TARGET_FORCES = {
    "Metropolitan Police Service",
    "City of London Police",
    "Leicestershire Police",
    "Cambridgeshire Constabulary",
    "West Yorkshire Police",
}

# Keep these columns (we'll rename to the normalized names below)
COLMAP = {
    "Crime ID": "crime_id",
    "Month": "month",
    "Reported by": "reported_by",
    "Falls within": "falls_within",
    "Longitude": "longitude",
    "Latitude": "latitude",
    "Location": "location",
    "LSOA code": "lsoa_code",
    "LSOA name": "lsoa_name",
    "Crime type": "crime_type",
    "Last outcome category": "outcome",
}

# Optional UK bounding box (very loose) to discard obvious geocoding outliers
UK_LON_MIN, UK_LON_MAX = -8.5, 2.5
UK_LAT_MIN, UK_LAT_MAX = 49.5, 61.5

CHUNKSIZE = 50_000   # adjust if you have more memory

# ------------ PIPELINE ------------
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Strip column whitespace and rename to our canonical names where present
    df.rename(columns=lambda c: c.strip(), inplace=True)
    df.rename(columns=COLMAP, inplace=True)
    # Keep only known columns
    keep = list(COLMAP.values())
    cols_present = [c for c in df.columns if c in keep]
    return df[cols_present]

def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    # Coordinates
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    # Month
    # The monthly files usually provide "YYYY-MM". Keep that as string,
    # but also create a first-of-month date for time-series work.
    df["month"] = df["month"].astype("string").str.strip()
    df["month_date"] = pd.to_datetime(df["month"] + "-01", errors="coerce", utc=True)
    # Text fields
    for txt in ["crime_id","reported_by","falls_within","location","lsoa_code","lsoa_name","crime_type","outcome"]:
        if txt in df.columns:
            df[txt] = df[txt].astype("string").str.strip()
    return df

def filter_targets(df: pd.DataFrame) -> pd.DataFrame:
    # Use Falls within primarily; if missing, fall back to Reported by.
    if "falls_within" in df.columns:
        mask = df["falls_within"].isin(TARGET_FORCES)
    else:
        mask = pd.Series([False] * len(df))
    if ("reported_by" in df.columns) and (~mask).any():
        mask = mask | df["reported_by"].isin(TARGET_FORCES)
    return df[mask]

def drop_bad_coords(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["latitude","longitude"])
    # Optional outlier filter
    in_box = (
        (df["longitude"].between(UK_LON_MIN, UK_LON_MAX)) &
        (df["latitude"].between(UK_LAT_MIN, UK_LAT_MAX))
    )
    return df[in_box]

def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    # 1) If crime_id exists, remove duplicates by (crime_id, month)
    if "crime_id" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["crime_id","month"])
        # print(f"dedupe by crime_id removed {before - len(df)} rows")
    # 2) For rows with missing crime_id, fall back to a spatial-temporal-key
    # Build a rounding key to ~1m precision (5 dp)
    missing = df["crime_id"].isna() | (df["crime_id"].str.len() == 0)
    if missing.any():
        tmp = df.loc[missing].copy()
        tmp["lat_r5"] = tmp["latitude"].round(5)
        tmp["lon_r5"] = tmp["longitude"].round(5)
        tmp["__key__"] = tmp["month"].fillna("") + "|" + tmp["crime_type"].fillna("") + "|" + tmp["lat_r5"].astype(str) + "|" + tmp["lon_r5"].astype(str)
        # Keep first per key
        keep_idx = ~tmp["__key__"].duplicated(keep="first")
        df = pd.concat([df.loc[~missing], tmp.loc[keep_idx].drop(columns=["lat_r5","lon_r5","__key__"])], ignore_index=True)
    return df

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = glob.glob(str(RAW_DIR / "*.csv"))
    if not files:
        print(f"No CSVs found in {RAW_DIR}")
        return

    print(f"Found {len(files)} crime files in {RAW_DIR}")
    parts = []

    for f in files:
        print(f"Reading: {f}")
        try:
            for chunk in pd.read_csv(f, chunksize=CHUNKSIZE, low_memory=False):
                # Normalise columns & filter
                chunk = normalize_columns(chunk)
                if chunk.empty:
                    continue

                chunk = coerce_types(chunk)
                chunk = filter_targets(chunk)
                if chunk.empty:
                    continue

                chunk = drop_bad_coords(chunk)
                if chunk.empty:
                    continue

                parts.append(chunk)
        except Exception as e:
            print(f"Skipping {f} due to error: {e}")

    if not parts:
        print("No matching rows found for target police forces.")
        return

    crime = pd.concat(parts, ignore_index=True)

    # Final de-duplication and ordering
    crime = dedupe(crime)
    crime = crime.sort_values(["month","falls_within","crime_type","latitude","longitude"], kind="stable")

    # Save single merged CSV
    crime.to_csv(OUT_FILE, index=False)
    print(f"Saved {len(crime):,} rows to {OUT_FILE}")

if __name__ == "__main__":
    main()