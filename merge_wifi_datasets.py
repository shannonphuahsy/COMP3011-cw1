import pandas as pd
import os

DATASET_FOLDER = "app/data/wifi_hotspots"
OUTPUT_FILE = "clean_wifi_hotspots.csv"

# Column variations across different council datasets
COLUMN_MAP = {
    "name": ["name", "location_name", "site_name", "venue", "wifi_name"],
    "address": ["address", "street_address", "location", "site_address"],
    "postcode": ["postcode", "post_code", "zip"],
    "latitude": ["latitude", "lat", "y"],
    "longitude": ["longitude", "lon", "lng", "x"]
}


def find_column(df, possible_names):
    """Find the first matching column name in the dataset."""
    for col in possible_names:
        if col in df.columns:
            return col
    return None


def standardise_dataset(filepath):
    """Load and standardise one dataset safely."""
    try:
        # Attempt to read CSV; skip bad lines
        df = pd.read_csv(filepath, on_bad_lines='skip', quotechar='"')
    except pd.errors.ParserError:
        print(f"Error reading {filepath}, skipping.")
        return pd.DataFrame()  # return empty DataFrame to continue

    clean = pd.DataFrame()

    # Map columns into standard schema
    for standard_col, variations in COLUMN_MAP.items():
        col = find_column(df, variations)
        if col:
            clean[standard_col] = df[col]
        else:
            clean[standard_col] = None

    # Add city from filename
    city = os.path.basename(filepath).replace(".csv", "")
    clean["city"] = city.capitalize()
    clean["source_dataset"] = city

    return clean


def clean_data(df):
    """Apply cleaning rules."""

    # Convert coordinates to numeric
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Remove rows missing coordinates
    df = df.dropna(subset=["latitude", "longitude"])

    # Remove coordinates outside UK bounds
    df = df[(df["latitude"] > 49) & (df["latitude"] < 61)]
    df = df[(df["longitude"] > -8) & (df["longitude"] < 2)]

    # Clean text fields
    df["name"] = df["name"].astype(str).str.strip().str.title()
    df["address"] = df["address"].astype(str).str.strip()
    df["postcode"] = df["postcode"].astype(str).str.strip().str.upper()

    # Remove duplicates
    df = df.drop_duplicates(subset=["name", "latitude", "longitude"])

    return df


def main():
    all_datasets = []

    for file in os.listdir(DATASET_FOLDER):
        if file.endswith(".csv"):
            filepath = os.path.join(DATASET_FOLDER, file)
            print(f"Processing {file}")

            df = standardise_dataset(filepath)
            if not df.empty:
                all_datasets.append(df)

    if not all_datasets:
        print("No valid datasets found.")
        return

    # Merge all datasets
    merged = pd.concat(all_datasets, ignore_index=True)

    # Clean merged dataset
    merged = clean_data(merged)

    # Create unique wifi ID
    merged.insert(0, "wifi_id", range(1, len(merged) + 1))

    # Save clean dataset
    merged.to_csv(OUTPUT_FILE, index=False)

    print("\nDataset successfully merged!")
    print(f"Total WiFi hotspots: {len(merged)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()