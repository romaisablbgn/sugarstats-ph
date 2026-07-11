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

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

df = read_extracted_tables("raw_production")

monthly_rows = []
annual_rows = []
rejected_rows = []

for _, row in df.iterrows():
    cells = [str(x).strip() if pd.notna(x) else "" for x in row.tolist()]
    source_period = row.get("source_period", "")
    source_file = row.get("source_file", "")

    joined = " ".join(cells).lower()

    # Detect month rows
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

            monthly_rows.append({
                "source_period": source_period,
                "source_file": source_file,
                "value_position": position,
                "month": month.title(),
                "month_order": MONTH_ORDER[month],
                "product_type": "raw_sugar",
                "metric": "raw_sugar_production",
                "unit": "MT",
                "value": value,
            })

        continue

    # Detect annual indicator rows
    if "total" in joined and "production" in joined:
        indicator = "total_raw_sugar_production"
        unit = "MT"
    elif "area" in joined and ("harvest" in joined or "planted" in joined):
        indicator = "area_harvested"
        unit = "hectares"
    elif "yield" in joined:
        indicator = "yield_per_hectare"
        unit = "LKg/Ha"
    else:
        indicator = None
        unit = None

    if indicator:
        data_cells = [
            str(row[column]).strip() if pd.notna(row[column]) else ""
            for column in row.index
            if column not in {"source_period", "source_file"}
        ]

        for position, cell in enumerate(data_cells[1:], start=1):
            value = parse_number(cell)
            if value is None:
                continue

            annual_rows.append({
                "source_period": source_period,
                "source_file": source_file,
                "value_position": position,
                "indicator": indicator,
                "unit": unit,
                "value": value,
            })

        continue

    if any(cells):
        rejected_rows.append({
            "source_period": source_period,
            "source_file": source_file,
            "raw_row": " | ".join(cells),
            "reason": "not_month_or_annual_indicator",
        })

monthly = pd.DataFrame(monthly_rows)
annual = pd.DataFrame(annual_rows)

monthly = assign_crop_year_by_position(monthly)
annual = assign_crop_year_by_position(annual)

monthly = monthly[
    [
        "crop_year",
        "month",
        "month_order",
        "product_type",
        "metric",
        "unit",
        "value",
        "source_period",
        "source_file",
    ]
]

annual = annual[
    [
        "crop_year",
        "indicator",
        "unit",
        "value",
        "source_period",
        "source_file",
    ]
]

save_csv(monthly, PROCESSED_DIR / "raw_production_monthly.csv")
save_csv(annual, PROCESSED_DIR / "raw_production_annual_indicators.csv")
save_rejected_rows(rejected_rows, AUDIT_DIR / "raw_production_rejected_rows.csv")

print("Saved:")
print("- data/processed/raw_production_monthly.csv")
print("- data/processed/raw_production_annual_indicators.csv")
