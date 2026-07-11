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

df = read_extracted_tables("raw_domestic_withdrawals")

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
            value = parse_number(cell)
            if value is None:
                continue

            rows.append({
                "source_period": source_period,
                "source_file": source_file,
                "value_position": position,
                "month": month.title(),
                "month_order": MONTH_ORDER[month],
                "product_type": "raw_sugar",
                "sugar_class": '"B" Domestic',
                "metric": "raw_sugar_domestic_withdrawals",
                "unit": "MT",
                "value": value,
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

out = pd.DataFrame(rows)
out = assign_crop_year_by_position(out)

out = out[
    [
        "crop_year",
        "month",
        "month_order",
        "product_type",
        "sugar_class",
        "metric",
        "unit",
        "value",
        "source_period",
        "source_file",
    ]
]

save_csv(out, PROCESSED_DIR / "raw_domestic_withdrawals_monthly.csv")
save_rejected_rows(rejected_rows, AUDIT_DIR / "raw_domestic_withdrawals_rejected_rows.csv")

print("Saved data/processed/raw_domestic_withdrawals_monthly.csv")
