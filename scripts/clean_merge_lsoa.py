# clean_merge_lsoa.py
import sys
from pathlib import Path
import pandas as pd

# ---------- config: resolve paths relative to this script ----------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "app" / "data"
OUT_DIR  = DATA_DIR / "clean_data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

POP_PATH = DATA_DIR / "LSOA.xlsx"          # population workbook (mid-2021, single-year ages)
LOC_PATH = DATA_DIR / "LSOA (2).xlsx"      # LSOA 2021 attributes (centroids/area/length)

# ---------- dependency guard for reading .xlsx ----------
try:
    import openpyxl  # noqa: F401
except ImportError as e:
    sys.exit(
        "❌ openpyxl is required to read .xlsx files.\n"
        "   Fix: activate your venv and run:  pip install \"openpyxl>=3.1.2,<4\"\n"
        f"   venv hint (PowerShell):  {BASE_DIR / '.venv' / 'Scripts' / 'Activate.ps1'}"
    )

# ---------- existence checks ----------
for p in [POP_PATH, LOC_PATH]:
    if not p.exists():
        sys.exit(f"❌ Input file not found: {p}\n   Expected under app/data/. "
                 f"If your files are elsewhere, adjust POP_PATH/LOC_PATH in the script.")

# ---------- 1) Clean LSOA population (mid-2021 sheet) ----------
# The population workbook contains a sheet named "Mid-2021 LSOA 2021" with:
# LAD 2021 Code/Name, LSOA 2021 Code/Name, Total, and F0..F90, M0..M90 columns. 1.xlsx&action=default&mobileredirect=true)
POP_SHEET = "Mid-2021 LSOA 2021"
pop_df = pd.read_excel(POP_PATH, sheet_name=POP_SHEET, header=3, engine="openpyxl")
pop_df = pop_df.loc[:, ~pop_df.columns.astype(str).str.startswith("Unnamed")]
pop_df.columns = [str(c).strip() for c in pop_df.columns]

# Keep rows that have an LSOA code
if "LSOA 2021 Code" not in pop_df.columns:
    sys.exit("❌ Column 'LSOA 2021 Code' not found in population sheet. "
             "Check the sheet name or header row.")
pop_df = pop_df[pop_df["LSOA 2021 Code"].notna()].copy()

# Identify single-year age columns (F0..F90, M0..M90) and convert numerics
f_cols = [c for c in pop_df.columns if c.startswith("F") and c[1:].isdigit()]
m_cols = [c for c in pop_df.columns if c.startswith("M") and c[1:].isdigit()]
for c in ["Total"] + f_cols + m_cols:
    pop_df[c] = pd.to_numeric(pop_df[c], errors="coerce")

def band_sum(df, a0, a1):
    cols = [f"F{i}" for i in range(a0, a1 + 1) if f"F{i}" in df.columns] + \
           [f"M{i}" for i in range(a0, a1 + 1) if f"M{i}" in df.columns]
    return df[cols].sum(axis=1)

max_age = max(max(int(c[1:]) for c in f_cols), max(int(c[1:]) for c in m_cols))
pop_df["pop_0_15"]    = band_sum(pop_df, 0, 15)
pop_df["pop_16_24"]   = band_sum(pop_df, 16, 24)
pop_df["pop_25_64"]   = band_sum(pop_df, 25, 64)
pop_df["pop_65_plus"] = band_sum(pop_df, 65, max_age)

pop_compact = pop_df[[
    "LAD 2021 Code", "LAD 2021 Name", "LSOA 2021 Code", "LSOA 2021 Name", "Total",
    "pop_0_15", "pop_16_24", "pop_25_64", "pop_65_plus"
]].rename(columns={
    "LAD 2021 Code":  "LAD21CD",
    "LAD 2021 Name":  "LAD21NM",
    "LSOA 2021 Code": "LSOA21CD",
    "LSOA 2021 Name": "LSOA21NM"
})

pop_out = OUT_DIR / "lsoa_population_summary_2021.csv"
pop_compact.to_csv(pop_out, index=False)

# ---------- 2) Clean LSOA attributes/locations ----------
# The attributes workbook sheet "LSOA_2021_EW_BGC_V5" contains LSOA21CD/LSOA21NM,
# BNG_E, BNG_N, LAT, LONG, Shape__Area, Shape__Length, etc. 1.xlsx&action=default&mobileredirect=true)
loc_sheet = pd.ExcelFile(LOC_PATH, engine="openpyxl").sheet_names[0]  # 'LSOA_2021_EW_BGC_V5'
loc_df = pd.read_excel(LOC_PATH, sheet_name=loc_sheet, engine="openpyxl")
loc_df.columns = [str(c).strip().replace("\n", " ") for c in loc_df.columns]

for c in ["BNG_E", "BNG_N", "LAT", "LONG", "Shape__Area", "Shape__Length"]:
    if c in loc_df.columns:
        loc_df[c] = pd.to_numeric(loc_df[c], errors="coerce")

# Parse LA_Name and suffix label from LSOA21NM (e.g., "Barking and Dagenham 016A")
if "LSOA21NM" not in loc_df.columns or "LSOA21CD" not in loc_df.columns:
    sys.exit("❌ Columns 'LSOA21CD' or 'LSOA21NM' not found in attributes sheet.")

parts = loc_df["LSOA21NM"].astype(str).str.rsplit(" ", n=1)
loc_df["LA_Name"] = parts.str[0]
loc_df["LSOA_Local_Label"] = parts.str[1]

loc_min = loc_df[[
    "LSOA21CD", "LSOA21NM", "LA_Name", "LSOA_Local_Label",
    "LAT", "LONG", "BNG_E", "BNG_N", "Shape__Area", "Shape__Length"
]].copy()
loc_min["area_km2"] = loc_min["Shape__Area"] / 1e6

loc_out = OUT_DIR / "lsoa_2021_locations_minimal.csv"
loc_min.to_csv(loc_out, index=False)

# ---------- 3) Merge on (LSOA21CD, LSOA21NM) and compute density ----------
merged = pop_compact.merge(loc_min, on=["LSOA21CD", "LSOA21NM"], how="inner")
merged["device_density_per_km2"] = merged["Total"] / merged["area_km2"]

merged_out = OUT_DIR / "lsoa_context_2021.csv"
merged.to_csv(merged_out, index=False)

print("Wrote:")
print(" -", pop_out)
print(" -", loc_out)
print(" -", merged_out)