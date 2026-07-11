from pathlib import Path
import pandas as pd

EXTRACTED_DIR = Path("data/extracted")
AUDIT_DIR = Path("outputs/audit")
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

rows = []

for csv_file in EXTRACTED_DIR.rglob("*.csv"):
    try:
        df = pd.read_csv(csv_file, dtype=str)

        preview_values = (
            df.head(3)
            .fillna("")
            .astype(str)
            .values
            .flatten()
            .tolist()
        )

        rows.append({
            "file": str(csv_file),
            "rows": len(df),
            "columns": len(df.columns),
            "empty_cells": int(df.isna().sum().sum()),
            "preview": " | ".join(preview_values[:30]),
        })

    except Exception as e:
        rows.append({
            "file": str(csv_file),
            "rows": None,
            "columns": None,
            "empty_cells": None,
            "preview": f"ERROR: {e}",
        })

profile = pd.DataFrame(rows)
profile.to_csv(AUDIT_DIR / "extracted_tables_profile.csv", index=False)

print("Saved outputs/audit/extracted_tables_profile.csv")