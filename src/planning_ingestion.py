from pathlib import Path
import requests
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "planning"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "planning"

RAW_FILE = RAW_DIR / "planning_applications_raw.csv"
PROCESSED_FILE = PROCESSED_DIR / "planning_applications_cleaned.csv"


# ============================================================
# SOURCE
# ============================================================

# Planning Application Sites layer (Layer 1)
ARCGIS_URL = (
    "https://services.arcgis.com/NzlPQPKn5QF9v2US/"
    "arcgis/rest/services/IrishPlanningApplications/FeatureServer/1/query"
)


# ============================================================
# CONFIGURATION
# ============================================================

PAGE_SIZE = 2000


# ============================================================
# DIRECTORY SETUP
# ============================================================

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FETCH DATA
# ============================================================

def fetch_planning_data():
    """
    Download all planning application records from the ArcGIS
    FeatureServer using pagination.
    """

    print("Starting planning application ingestion...")
    print("Source: Irish Planning Applications - Planning Application Sites")

    all_features = []
    offset = 0

    while True:

        print(f"Requesting records starting at offset {offset}...")

        params = {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "false",
            "resultOffset": offset,
            "resultRecordCount": PAGE_SIZE,
            "f": "json",
        }

        response = requests.get(
            ARCGIS_URL,
            params=params,
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise RuntimeError(
                f"ArcGIS API error: {data['error']}"
            )

        features = data.get("features", [])

        if not features:
            break

        all_features.extend(features)

        print(
            f"Retrieved {len(features)} records "
            f"(total: {len(all_features)})"
        )

        if len(features) < PAGE_SIZE:
            break

        offset += PAGE_SIZE

    print()
    print(f"Total records retrieved: {len(all_features)}")

    if not all_features:
        raise ValueError(
            "No planning application records were retrieved."
        )

    records = [
        feature.get("attributes", {})
        for feature in all_features
    ]

    return pd.DataFrame(records)


# ============================================================
# VALIDATION
# ============================================================

def validate_planning_data(df):
    """Validate basic planning dataset structure."""

    if df.empty:
        raise ValueError("Planning dataset is empty.")

    if len(df.columns) == 0:
        raise ValueError("Planning dataset contains no columns.")

    # Check for completely duplicated rows
    duplicate_count = df.duplicated().sum()

    print()
    print("Planning structure validation passed.")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Duplicate rows: {duplicate_count:,}")

    return True


# ============================================================
# CLEANING
# ============================================================

def clean_planning_data(df):
    """Perform conservative cleaning without destroying source data."""

    df = df.copy()

    # Remove completely duplicated rows
    df = df.drop_duplicates().reset_index(drop=True)

    # Strip whitespace from string columns
    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].apply(
            lambda x: x.strip() if isinstance(x, str) else x
        )

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PLANNING APPLICATION INGESTION")
    print("=" * 60)

    # --------------------------------------------------------
    # Extract
    # --------------------------------------------------------

    planning = fetch_planning_data()

    # --------------------------------------------------------
    # Raw validation
    # --------------------------------------------------------

    validate_planning_data(planning)

    # --------------------------------------------------------
    # Save raw data
    # --------------------------------------------------------

    planning.to_csv(
        RAW_FILE,
        index=False,
        encoding="utf-8",
    )

    print()
    print(f"Raw planning dataset saved to:")
    print(RAW_FILE)

    # --------------------------------------------------------
    # Clean
    # --------------------------------------------------------

    cleaned = clean_planning_data(planning)

    # --------------------------------------------------------
    # Missing-value analysis
    # --------------------------------------------------------

    missing = (
        cleaned.isna()
        .sum()
        .sort_values(ascending=False)
    )

    missing_percentage = (
        cleaned.isna().mean() * 100
    ).sort_values(ascending=False)

    missing_summary = pd.DataFrame({
        "missing_count": missing,
        "missing_percentage": missing_percentage.round(2),
    })

    # --------------------------------------------------------
    # Save processed data
    # --------------------------------------------------------

    cleaned.to_csv(
        PROCESSED_FILE,
        index=False,
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("PLANNING DATASET SUMMARY")
    print("=" * 60)

    print(f"Rows before cleaning: {len(planning):,}")
    print(f"Rows after cleaning:  {len(cleaned):,}")
    print(
        f"Duplicates removed:  "
        f"{len(planning) - len(cleaned):,}"
    )

    print()
    print("Columns:")
    print(cleaned.columns.tolist())

    print()
    print("Missing values:")
    print(missing_summary.to_string())

    print()
    print("First 10 rows:")
    print(cleaned.head(10).to_string(index=False))

    print()
    print(f"Processed planning dataset saved to:")
    print(PROCESSED_FILE)

    print()
    print(f"Saved rows: {len(cleaned):,}")
    print(f"Saved columns: {len(cleaned.columns)}")

    print()
    print("=" * 60)
    print("PLANNING INGESTION COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()