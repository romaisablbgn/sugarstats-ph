from pathlib import Path
import pandas as pd

from sugarstats_helpers import (
    normalize_month,
    MONTH_ORDER,
    parse_number,
    read_extracted_tables,
    assign_crop_year_by_position,
    save_csv,
    save_rejected_rows,
)

PROCESSED_DIR = Path("data/processed")
AUDIT_DIR = Path("outputs/audit")

df = read_extracted_tables("refined_withdrawals")

rows = []
rejected_rows = []

for _, row in df.iterrows():
    cells = [str(x).strip() if pd.notna(x) else "" for x in row.tolist()]
    source_period = row.get("source_period", "")
    source_file = row.get("source_file", "")

    month = None
    for cell in cells:
        month = normalize_month(cell)
        if month:
            break

    if month:
        data_cells = [
            str(row[column]).strip() if pd.notna(row[column]) else ""
            for column in row.index
            if column not in {"source_period", "source_file"}
        ]
        month_index = next(
            index for index, cell in enumerate(data_cells)
            if normalize_month(cell) == month
        )

        for position, cell in enumerate(data_cells[month_index + 1:], start=1):
            value_lkg = parse_number(cell)
            if value_lkg is None:
                continue

            rows.append({
                "source_period": source_period,
                "source_file": source_file,
                "value_position": position,
                "month": month.title(),
                "month_order": MONTH_ORDER[month],
                "product_type": "refined_sugar",
                "metric": "refined_sugar_withdrawals",
                "unit": "LKg",
                "value_lkg": value_lkg,
                "value_mt": value_lkg * 0.05,
            })

        continue

    joined = " ".join(cells).lower()

    if "total" in joined or "average" in joined:
        continue

    if any(cells):
        rejected_rows.append({
            "source_period": source_period,
            "source_file": source_file,
            "raw_row": " | ".join(cells),
            "reason": "not_month_row",
        })

for source_file, file_df in df.groupby("source_file"):
    data_columns = [
        column
        for column in file_df.columns
        if column not in {"source_period", "source_file"}
        and file_df[column].fillna("").astype(str).str.strip().ne("").any()
    ]

    if len(data_columns) != 1:
        continue

    values = [
        str(value).strip() if pd.notna(value) else ""
        for value in file_df[data_columns[0]].tolist()
    ]

    crop_year = None
    for value in values:
        if "CROP YEAR" in value.upper():
            parts = value.replace("\n", " ").split()
            crop_year = next((part for part in parts if "-" in part), None)
            break

    if crop_year is None:
        continue

    month_values = values[1:13]
    for month_name, value_text in zip(MONTH_ORDER.keys(), month_values):
        value_lkg = parse_number(value_text)
        if value_lkg is None:
            continue

        rows.append({
            "source_period": file_df["source_period"].iloc[0],
            "source_file": source_file,
            "value_position": 1,
            "month": month_name.title(),
            "month_order": MONTH_ORDER[month_name],
            "product_type": "refined_sugar",
            "metric": "refined_sugar_withdrawals",
            "unit": "LKg",
            "value_lkg": value_lkg,
            "value_mt": value_lkg * 0.05,
            "explicit_crop_year": crop_year,
        })

out = pd.DataFrame(rows)
out = assign_crop_year_by_position(out)

if "explicit_crop_year" in out.columns:
    out["crop_year"] = out["explicit_crop_year"].fillna(out["crop_year"])

out = out[
    [
        "crop_year",
        "month",
        "month_order",
        "product_type",
        "metric",
        "unit",
        "value_lkg",
        "value_mt",
        "source_period",
        "source_file",
    ]
]

save_csv(out, PROCESSED_DIR / "refined_withdrawals_monthly.csv")
save_rejected_rows(rejected_rows, AUDIT_DIR / "refined_withdrawals_rejected_rows.csv")

print("Saved data/processed/refined_withdrawals_monthly.csv")
