from pathlib import Path
import pandas as pd

PROCESSED_DIR = Path("data/processed")

expected = pd.read_csv("config/expected_crop_years.csv")

FILES = [
    "raw_production_monthly_intermediate.csv",
    "refined_production_monthly_intermediate.csv",
    "raw_domestic_withdrawals_monthly_intermediate.csv",
    "refined_withdrawals_monthly_intermediate.csv",
    "raw_production_annual_intermediate.csv",
]

for filename in FILES:
    path = PROCESSED_DIR / filename

    if not path.exists():
        print(f"Skipping missing file: {filename}")
        continue

    df = pd.read_csv(path)

    merged = df.merge(
        expected,
        left_on=["source_period", "value_position"],
        right_on=["source_period", "sort_order"],
        how="left",
    )

    missing = merged[merged["crop_year"].isna()]
    if not missing.empty:
        audit_path = Path("outputs/audit") / f"{filename}_missing_crop_year.csv"
        missing.to_csv(audit_path, index=False)
        print(f"Warning: missing crop-year mapping in {filename}. Check {audit_path}")

    cleaned = merged.drop(columns=["sort_order"], errors="ignore")

    output_name = filename.replace("_intermediate", "")
    output_path = PROCESSED_DIR / output_name
    cleaned.to_csv(output_path, index=False)

    print(f"Saved {output_path}")