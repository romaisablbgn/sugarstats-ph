from pathlib import Path
import re
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

df = read_extracted_tables("refined_production")

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
                "metric": "refined_sugar_production",
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

fallback_pdf = Path("data/raw/2020-2025/refined_production.pdf")
if fallback_pdf.exists():
    try:
        import pdfplumber

        with pdfplumber.open(fallback_pdf) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        number_pattern = re.compile(r"(?:\d\s+)?\d{1,3}(?:,\d{3})+|\d+|-")
        existing_keys = {
            (row_data.get("crop_year"), row_data.get("month"))
            for row_data in rows
        }

        for line in text.splitlines():
            parts = line.strip().split(maxsplit=1)
            if not parts:
                continue

            month_key = normalize_month(parts[0])
            if month_key is None or len(parts) < 2:
                continue

            values = number_pattern.findall(parts[1])
            if len(values) < 5:
                continue

            value_lkg = parse_number(values[4])
            if value_lkg is None:
                continue

            crop_year = "2020-2021"
            month_name = month_key.title()
            if (crop_year, month_name) in existing_keys:
                continue

            rows.append({
                "source_period": "2020-2025",
                "source_file": str(fallback_pdf),
                "value_position": 5,
                "explicit_crop_year": crop_year,
                "month": month_name,
                "month_order": MONTH_ORDER[month_key],
                "product_type": "refined_sugar",
                "metric": "refined_sugar_production",
                "unit": "LKg",
                "value_lkg": value_lkg,
                "value_mt": value_lkg * 0.05,
            })
    except Exception as exc:
        rejected_rows.append({
            "source_period": "2020-2025",
            "source_file": str(fallback_pdf),
            "raw_row": "",
            "reason": f"pdf_text_fallback_failed: {exc}",
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

save_csv(out, PROCESSED_DIR / "refined_production_monthly.csv")
save_rejected_rows(rejected_rows, AUDIT_DIR / "refined_production_rejected_rows.csv")

print("Saved data/processed/refined_production_monthly.csv")
