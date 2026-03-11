"""
Merge & clean 5 UK public WiFi datasets into a canonical API-ready table.

Inputs expected (same project; default data dir = app/data/wifi_hotspots):
  - Camden.csv
  - Leicester.csv              (semicolon-delimited)
  - Cambridgeshire.csv
  - Calderdale.csv
  - Leeds.csv

Output (default): wifi_hotspots_clean.csv

Canonical schema (columns):
  wifi_id, name, address, postcode, city, latitude, longitude, status, venue_type,
  network_provider, security_protection, accessibility_policy, govroam_enabled,
  date_live, easting, northing, wkt_point, coverage_radius_m, coverage_polygon_wkt,
  url, description, uprn, install_type, source_dataset, source_row_id
"""

from __future__ import annotations
import argparse
import os
import sys
import glob
from pathlib import Path
import uuid
import re
from datetime import datetime

import pandas as pd


# =========================
# CLI & paths
# =========================
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean & merge UK public WiFi datasets")
    default_data = Path(__file__).parent / "app" / "data" / "wifi_hotspots"
    parser.add_argument("--data-dir", type=Path, default=default_data,
                        help=f"Folder containing the 5 CSVs (default: {default_data})")
    parser.add_argument("--output", type=Path, default=Path("../app/data/clean_data/wifi_hotspots_clean.csv"),
                        help="Output CSV path (default: wifi_hotspots_clean.csv)")
    parser.add_argument("--dedupe-precision", type=int, default=5,
                        help="Rounding precision (decimal places) for lat/lon when deduping (default: 5 ≈ ~1 m)")
    return parser.parse_args()


def find_file(data_dir: Path, preferred_names: list[str]) -> Path:
    """
    Find a file in data_dir by trying preferred names (case-insensitive) and
    falling back to glob matches. Raises FileNotFoundError if not found.
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Data folder not found: {data_dir.resolve()}")

    # Exact (case-insensitive)
    entries = {p.name.lower(): p for p in data_dir.iterdir() if p.is_file()}
    for name in preferred_names:
        lower = name.lower()
        if lower in entries:
            return entries[lower]

    # Glob fallback on tokens (e.g., 'Camden*.csv')
    for token in preferred_names:
        token_noext = os.path.splitext(token)[0]
        matches = list(data_dir.glob(f"*{token_noext}*.csv"))
        if matches:
            return matches[0]

    available = ", ".join(sorted(p.name for p in data_dir.iterdir() if p.is_file()))
    raise FileNotFoundError(
        f"Could not find any of {preferred_names} in {data_dir.resolve()}. "
        f"Available files: {available}"
    )


def read_csv_safely(path: Path, **kwargs) -> pd.DataFrame:
    """
    Try UTF-8 first, then fallback to UTF-8-SIG or latin-1 if needed.
    """
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError:
            continue
    # last attempt raises the original error if it fails
    return pd.read_csv(path, **kwargs)


# =========================
# Helpers & normalisers
# =========================
UK_POSTCODE_RE = re.compile(r"\s+")

def uuid4_str() -> str:
    return str(uuid.uuid4())

def normalise_postcode(s) -> str | None:
    if pd.isna(s) or s is None:
        return None
    s = str(s).strip().upper()
    s = UK_POSTCODE_RE.sub(" ", s)  # collapse whitespace
    return s if s else None

def parse_date_ddmmyyyy(s) -> str | None:
    """
    Parse 'DD/MM/YYYY' (and a couple of variants) into ISO 'YYYY-MM-DD'.
    Return None if invalid/blank.
    """
    if pd.isna(s) or s is None:
        return None
    s = str(s).strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None

def combine_address(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    """
    Row-wise join of address parts with trimming and blank suppression.
    """
    parts = []
    for c in cols:
        if c in df.columns:
            series = df[c].astype("string")
            parts.append(series.where(series.str.strip().fillna("") != "", None))
        else:
            parts.append(pd.Series([None] * len(df)))
    stacked = pd.concat(parts, axis=1)

    def join_row(row):
        vals = [str(x).strip() for x in row if x is not None and not pd.isna(x) and str(x).strip()]
        return ", ".join(vals) if vals else None

    return stacked.apply(join_row, axis=1)

def to_bool01(x) -> bool | None:
    if pd.isna(x):
        return None
    try:
        return bool(int(x))
    except Exception:
        return None

def wkt_point(lon, lat) -> str | None:
    if pd.isna(lat) or pd.isna(lon):
        return None
    return f"POINT ({lon:.6f} {lat:.6f})"

def choose_best_record(group: pd.DataFrame) -> pd.Series:
    """
    Pick the best representative row in a near-duplicate group.
      +3 if status in {'Live','Complete'}
      +2 if security_protection present
      +1 if coverage_polygon_wkt present
      +1 if url present
    """
    def score(row):
        s = 0
        if str(row.get("status", "")).strip().lower() in {"live", "complete"}:
            s += 3
        if pd.notna(row.get("security_protection")):
            s += 2
        if pd.notna(row.get("coverage_polygon_wkt")):
            s += 1
        if pd.notna(row.get("url")):
            s += 1
        return s

    scores = group.apply(score, axis=1)
    return group.loc[scores.idxmax()]


# =========================
# Builders per dataset
# =========================
def build_camden(df: pd.DataFrame) -> pd.DataFrame:
    # Camden provides POINT and POLYGON WKT, Range in Metres, Install Type
    out = pd.DataFrame({
        "name": df["Wi-Fi Name"],
        "address": combine_address(df, ["Road", "Location Description"]),
        "postcode": None,  # not explicitly present
        "city": "Camden",
        "latitude": df["Latitude"],
        "longitude": df["Longitude"],
        "status": None,
        "venue_type": df["Install Type"],               # Lighting/CCTV/Library
        "network_provider": None,
        "security_protection": None,
        "accessibility_policy": None,
        "govroam_enabled": None,
        "date_live": df["Install Date"].map(parse_date_ddmmyyyy),
        "easting": df["Easting"] if "Easting" in df.columns else None,
        "northing": df["Northing"] if "Northing" in df.columns else None,
        "wkt_point": df["Location"],                    # POINT WKT
        "coverage_radius_m": df["Range in Metres"],
        "coverage_polygon_wkt": df["Range"],            # POLYGON WKT
        "url": None,
        "description": None,
        "uprn": None,
        "install_type": df["Install Type"],
        "source_dataset": "Camden.csv",
        "source_row_id": df.index.astype(str),
    })
    # ensure WKT point for all
    mask = out["wkt_point"].isna()
    out.loc[mask, "wkt_point"] = out.loc[mask].apply(lambda r: wkt_point(r["longitude"], r["latitude"]), axis=1)
    return out


def build_leicester(df: pd.DataFrame) -> pd.DataFrame:
    # Provider normalisation map
    prov_map = {
        "THE_CLOUD": "The_Cloud",
        "THE CLOUD": "The_Cloud",
        "THE_CLOUD PROVIDED BY DMH": "The_Cloud",
        "LEICESTERLIBRARIES ONLY": "LeicesterLibraries",
        "LEICESTERLIBRARIES AND 5FOILLCC ONLY": "LeicesterLibraries",
        "ALL SSIDS EXCEPT THE_CLOUD": "NonCloud",
    }
    raw_provider = df["current_ssid_broadcast"].fillna("").astype(str).str.strip()
    norm_provider = raw_provider.str.upper().map(prov_map).where(lambda s: s.notna() & (s != ""))

    out = pd.DataFrame({
        "name": df["property_name"],
        "address": df["address"],
        "postcode": df["post_code"].map(normalise_postcode),
        "city": "Leicester",
        "latitude": df["lat"],
        "longitude": df["long"],
        "status": df["status"],   # Complete / Not Live
        "venue_type": df["sub_type"].fillna(df["property_type"]),
        "network_provider": norm_provider,
        "security_protection": None,
        "accessibility_policy": None,
        "govroam_enabled": None,
        "date_live": None,
        "easting": None,
        "northing": None,
        "wkt_point": df.apply(lambda r: wkt_point(r["long"], r["lat"]), axis=1),
        "coverage_radius_m": None,
        "coverage_polygon_wkt": None,
        "url": None,
        "description": None,
        "uprn": None,
        "install_type": None,
        "source_dataset": "Leicester.csv",
        "source_row_id": df.index.astype(str),
    })
    return out


def build_cambridgeshire(df: pd.DataFrame) -> pd.DataFrame:
    def norm_cambs_provider(x):
        if pd.isna(x):
            return None
        s = str(x).strip().lower()
        if "cambwifi" in s:
            return "CambWifi"
        return None

    out = pd.DataFrame({
        "name": df["Site Name"],
        "address": df["Address"],
        "postcode": df["PostCode"].map(normalise_postcode),
        "city": "Cambridgeshire",
        "latitude": df["Lat"],
        "longitude": df["Long"],
        "status": df["Status"],   # typically Live
        "venue_type": None,
        "network_provider": df["Access"].map(norm_cambs_provider),
        "security_protection": None,
        "accessibility_policy": None,
        "govroam_enabled": None,
        "date_live": df["Date Live"].map(parse_date_ddmmyyyy),
        "easting": df["Easting"],
        "northing": df["Northing"],
        "wkt_point": df.apply(lambda r: wkt_point(r["Long"], r["Lat"]), axis=1),
        "coverage_radius_m": None,
        "coverage_polygon_wkt": None,
        "url": df["URL"],
        "description": df["Description"],
        "uprn": df["UPRN"],   # store as text; dtype set at read_csv
        "install_type": None,
        "source_dataset": "Cambridgeshire.csv",
        "source_row_id": df["ID"].astype(str),
    })
    return out


def build_calderdale(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "name": df["Site_name"],
        "address": combine_address(df, ["Address1", "Address2", "Address3", "Postcode"]),
        "postcode": df["Postcode"].map(normalise_postcode),
        "city": "Calderdale",
        "latitude": df["Latitude"],
        "longitude": df["Longitude"],
        "status": None,
        "venue_type": None,
        "network_provider": None,
        "security_protection": None,
        "accessibility_policy": None,
        "govroam_enabled": None,
        "date_live": None,
        "easting": df["Easting"],
        "northing": df["Northing"],
        "wkt_point": df.apply(lambda r: wkt_point(r["Longitude"], r["Latitude"]), axis=1),
        "coverage_radius_m": None,
        "coverage_polygon_wkt": None,
        "url": None,
        "description": None,
        "uprn": None,
        "install_type": None,
        "source_dataset": "Calderdale.csv",
        "source_row_id": df.index.astype(str),
    })
    return out


def build_leeds(df: pd.DataFrame) -> pd.DataFrame:
    # Map Stage=Active -> status=Live
    status_norm = df["Stage"].fillna("").str.strip().str.lower().map({"active": "Live"})

    out = pd.DataFrame({
        "name": df["Name"],
        "address": combine_address(df, ["Address1", "Address2", "Address3", "PostalCode"]),
        "postcode": df["PostalCode"].map(normalise_postcode),
        "city": "Leeds",
        "latitude": df["Latitude"],
        "longitude": df["Longitude"],
        "status": status_norm,
        "venue_type": df["Type"],                     # SingleSpot / Area
        "network_provider": None,
        "security_protection": df["Protection"],      # e.g., WPA2
        "accessibility_policy": df["Accessibility"],  # e.g., No Restrictions
        "govroam_enabled": df["GovroamEnabled"].map(lambda x: None if pd.isna(x) else bool(int(x))),
        "date_live": None,
        "easting": None,
        "northing": None,
        "wkt_point": df.apply(lambda r: wkt_point(r["Longitude"], r["Latitude"]), axis=1),
        "coverage_radius_m": None,
        "coverage_polygon_wkt": None,
        "url": None,
        "description": None,
        "uprn": None,
        "install_type": None,
        "source_dataset": "Leeds.csv",
        "source_row_id": df.index.astype(str),
    })
    return out


# =========================
# Main ETL
# =========================
def main():
    args = parse_args()

    # Resolve input files
    camden_path         = find_file(args.data_dir, ["Camden.csv"])
    leicester_path      = find_file(args.data_dir, ["Leicester.csv"])
    cambridgeshire_path = find_file(args.data_dir, ["Cambridgeshire.csv"])
    calderdale_path     = find_file(args.data_dir, ["Calderdale.csv"])
    leeds_path          = find_file(args.data_dir, ["Leeds.csv"])

    print("Using data files:")
    print("  Camden         :", camden_path)
    print("  Leicester      :", leicester_path)
    print("  Cambridgeshire :", cambridgeshire_path)
    print("  Calderdale     :", calderdale_path)
    print("  Leeds          :", leeds_path)
    print()

    # Load with tolerant encodings; Leicester is semicolon-delimited
    camden          = read_csv_safely(camden_path)
    leicester       = read_csv_safely(leicester_path, sep=';')
    cambridgeshire  = read_csv_safely(cambridgeshire_path, dtype={'UPRN': 'string'})
    calderdale      = read_csv_safely(calderdale_path)
    leeds           = read_csv_safely(leeds_path)

    # Build canonical dataframes
    frames = [
        build_camden(camden),
        build_leicester(leicester),
        build_cambridgeshire(cambridgeshire),
        build_calderdale(calderdale),
        build_leeds(leeds),
    ]

    merged = pd.concat(frames, ignore_index=True)

    # Assign IDs
    merged.insert(0, "wifi_id", [uuid4_str() for _ in range(len(merged))])

    # Try postcode extraction from address if missing (loose heuristic)
    pat = re.compile(r"([A-Z]{1,2}[0-9][0-9A-Z]?)\s*([0-9][A-Z]{2})$")
    def extract_pc_from_addr(addr):
        if addr and isinstance(addr, str):
            m = pat.search(addr.upper())
            if m:
                return f"{m.group(1)} {m.group(2)}"
        return None
    missing_pc = merged["postcode"].isna()
    merged.loc[missing_pc, "postcode"] = merged.loc[missing_pc, "address"].map(extract_pc_from_addr)

    # Canonical dtypes
    str_cols = [
        "name","address","postcode","city","status","venue_type","network_provider",
        "security_protection","accessibility_policy","date_live","url","description",
        "uprn","install_type","wkt_point","coverage_polygon_wkt","source_dataset","source_row_id"
    ]
    for col in str_cols:
        merged[col] = merged[col].astype("string")

    for col in ["latitude", "longitude", "easting", "northing"]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    if "coverage_radius_m" in merged.columns:
        merged["coverage_radius_m"] = pd.to_numeric(merged["coverage_radius_m"], errors="coerce").astype("Int64")

    # -----------------------------
    # Deduplicate near-identical records
    # Group by (postcode + rounded coords) or just (rounded coords) when postcode is missing
    # -----------------------------
    prec = int(args.dedupe_precision)
    merged["_lat_r"] = merged["latitude"].round(prec)
    merged["_lon_r"] = merged["longitude"].round(prec)
    merged["_pc_key"] = merged["postcode"].fillna("")

    with_pc = merged[merged["_pc_key"] != ""]
    no_pc   = merged[merged["_pc_key"] == ""]

    kept_with = with_pc.groupby(["_pc_key","_lat_r","_lon_r"], dropna=False, group_keys=False).apply(choose_best_record)
    kept_no   = no_pc.groupby(["_lat_r","_lon_r"], dropna=False, group_keys=False).apply(choose_best_record)

    clean = pd.concat([kept_with, kept_no], ignore_index=True)
    clean = clean.drop(columns=["_pc_key","_lat_r","_lon_r"], errors="ignore")

    # Ensure WKT present
    mask_wkt = clean["wkt_point"].isna()
    clean.loc[mask_wkt, "wkt_point"] = clean.loc[mask_wkt].apply(lambda r: wkt_point(r["longitude"], r["latitude"]), axis=1)

    # Final column order
    final_cols = [
        "wifi_id","name","address","postcode","city","latitude","longitude","status","venue_type","network_provider",
        "security_protection","accessibility_policy","govroam_enabled","date_live","easting","northing","wkt_point",
        "coverage_radius_m","coverage_polygon_wkt","url","description","uprn","install_type","source_dataset","source_row_id"
    ]
    clean = clean[final_cols]

    # Save
    args.output.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(args.output, index=False, encoding="utf-8")
    print(f"Saved {args.output} with {len(clean)} rows")
    print("Rows per city:\n", clean.groupby("city").size().to_string())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)