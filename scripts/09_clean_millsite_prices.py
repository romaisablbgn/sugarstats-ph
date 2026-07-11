from pathlib import Path
import re
import pandas as pd

from sugarstats_helpers import (
    normalize_month,
    MONTH_ORDER,
    parse_number,
    survey_status,
    read_extracted_tables,
    save_csv,
    save_rejected_rows,
)

PROCESSED_DIR = Path("data/processed")
AUDIT_DIR = Path("outputs/audit")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

df = read_extracted_tables("millsite_prices")

if df.empty:
    raise ValueError(
        "No extracted millsite price tables found. "
        "Check that your CSV files are inside data/extracted/millsite_prices/<source_period>/"
    )

print("Loaded extracted millsite rows:", len(df))
print("Columns:", df.columns.tolist())
print(df.head())


def detect_crop_year_from_month_cell(value):
    """
    Detects crop year from cells like:
    - September, 2014
    - September 2014
    - Sept. 2014

    Crop year starts in September.
    September, 2014 = 2014-2015
    """
    text = "" if pd.isna(value) else str(value).strip()

    match = re.search(r"(20\d{2})", text)
    if not match:
        return None

    start_year = int(match.group(1))
    end_year = start_year + 1

    return f"{start_year}-{end_year}"


def clean_header_label(value):
    text = "" if pd.isna(value) else str(value).strip()
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def identify_price_column(header_value):
    """
    Converts messy extracted header text into a clean millsite price definition.
    """
    header = clean_header_label(header_value).lower()

    if header == "":
        return None

    if "month" in header:
        return None

    if "a" in header and "export" in header:
        return {
            "price_type": '"A" Export',
            "sugar_class": '"A"',
            "product_type": "raw_sugar",
            "unit": "PHP/LKg",
        }

    if "b" in header and "domestic" in header:
        return {
            "price_type": '"B" Domestic',
            "sugar_class": '"B"',
            "product_type": "raw_sugar",
            "unit": "PHP/LKg",
        }

    if "d" in header and ("world" in header or "market" in header):
        return {
            "price_type": '"D" World Market',
            "sugar_class": '"D"',
            "product_type": "raw_sugar",
            "unit": "PHP/LKg",
        }

    if "composite" in header:
        return {
            "price_type": "Composite Price",
            "sugar_class": None,
            "product_type": "raw_sugar",
            "unit": "PHP/LKg",
        }

    if "molasses" in header:
        return {
            "price_type": "Molasses",
            "sugar_class": None,
            "product_type": "molasses",
            "unit": "PHP/MT",
        }

    return None


def fallback_price_columns(number_of_value_columns):
    """
    Used only when the header row cannot be read properly.
    Most recent tables usually have:
    Month, A Export, B Domestic, Composite Price, Molasses

    Some older tables may have D World Market:
    Month, A Export, B Domestic, D World Market, Composite Price, Molasses
    """
    if number_of_value_columns >= 5:
        return {
            "1": {
                "price_type": '"A" Export',
                "sugar_class": '"A"',
                "product_type": "raw_sugar",
                "unit": "PHP/LKg",
            },
            "2": {
                "price_type": '"B" Domestic',
                "sugar_class": '"B"',
                "product_type": "raw_sugar",
                "unit": "PHP/LKg",
            },
            "3": {
                "price_type": '"D" World Market',
                "sugar_class": '"D"',
                "product_type": "raw_sugar",
                "unit": "PHP/LKg",
            },
            "4": {
                "price_type": "Composite Price",
                "sugar_class": None,
                "product_type": "raw_sugar",
                "unit": "PHP/LKg",
            },
            "5": {
                "price_type": "Molasses",
                "sugar_class": None,
                "product_type": "molasses",
                "unit": "PHP/MT",
            },
        }

    return {
        "1": {
            "price_type": '"A" Export',
            "sugar_class": '"A"',
            "product_type": "raw_sugar",
            "unit": "PHP/LKg",
        },
        "2": {
            "price_type": '"B" Domestic',
            "sugar_class": '"B"',
            "product_type": "raw_sugar",
            "unit": "PHP/LKg",
        },
        "3": {
            "price_type": "Composite Price",
            "sugar_class": None,
            "product_type": "raw_sugar",
            "unit": "PHP/LKg",
        },
        "4": {
            "price_type": "Molasses",
            "sugar_class": None,
            "product_type": "molasses",
            "unit": "PHP/MT",
        },
    }


rows = []
rejected_rows = []

# Process each extracted CSV separately because each file/table can have its own header.
for source_file, file_df in df.groupby("source_file"):
    source_period = file_df["source_period"].iloc[0]

    print(f"\nProcessing: {source_file}")

    current_crop_year = None
    price_columns = {}

    for _, row in file_df.iterrows():
        cells = row.to_dict()

        # The extracted CSV columns are strings: "0", "1", "2", ...
        month_cell = cells.get("0", "")
        month = normalize_month(month_cell)

        # Detect header row
        first_cell = "" if pd.isna(month_cell) else str(month_cell).strip().lower()

        if first_cell == "month":
            price_columns = {}

            for col_name, raw_header in cells.items():
                if col_name in {"source_period", "source_file"}:
                    continue

                definition = identify_price_column(raw_header)
                if definition is not None:
                    price_columns[str(col_name)] = definition

            if not price_columns:
                value_columns = [
                    c for c in cells.keys()
                    if c not in {"0", "source_period", "source_file"}
                ]
                price_columns = fallback_price_columns(len(value_columns))

            continue

        # Skip non-month rows
        if not month:
            raw_row = " | ".join(
                "" if pd.isna(v) else str(v)
                for k, v in cells.items()
                if k not in {"source_period", "source_file"}
            )

            if raw_row.strip():
                rejected_rows.append({
                    "source_period": source_period,
                    "source_file": source_file,
                    "crop_year": current_crop_year,
                    "month": None,
                    "raw_row": raw_row,
                    "reason": "month_not_detected",
                })

            continue

        # If month cell contains a year, use it to start/update crop year.
        detected_crop_year = detect_crop_year_from_month_cell(month_cell)
        if detected_crop_year is not None:
            current_crop_year = detected_crop_year

        if current_crop_year is None:
            raw_row = " | ".join(
                "" if pd.isna(v) else str(v)
                for k, v in cells.items()
                if k not in {"source_period", "source_file"}
            )

            rejected_rows.append({
                "source_period": source_period,
                "source_file": source_file,
                "crop_year": None,
                "month": month.title(),
                "raw_row": raw_row,
                "reason": "crop_year_not_detected",
            })

            continue

        # If no header was detected, infer based on available value columns.
        if not price_columns:
            value_columns = [
                c for c in cells.keys()
                if c not in {"0", "source_period", "source_file"}
            ]
            price_columns = fallback_price_columns(len(value_columns))

        for col_name, definition in price_columns.items():
            raw_value = cells.get(col_name, "")

            status = survey_status(raw_value)
            price = parse_number(raw_value)

            rows.append({
                "crop_year": current_crop_year,
                "month": month.title(),
                "month_order": MONTH_ORDER[month],
                "price_type": definition["price_type"],
                "sugar_class": definition["sugar_class"],
                "product_type": definition["product_type"],
                "unit": definition["unit"],
                "raw_value": raw_value,
                "survey_status": status,
                "price": price,
                "include_in_analysis": status == "reported",
                "source_period": source_period,
                "source_file": source_file,
            })


expected_columns = [
    "crop_year",
    "month",
    "month_order",
    "price_type",
    "sugar_class",
    "product_type",
    "unit",
    "raw_value",
    "survey_status",
    "price",
    "include_in_analysis",
    "source_period",
    "source_file",
]

out = pd.DataFrame(rows)

if out.empty:
    out = pd.DataFrame(columns=expected_columns)
else:
    out = out[expected_columns]

save_csv(out, PROCESSED_DIR / "millsite_prices_monthly.csv")
save_rejected_rows(rejected_rows, AUDIT_DIR / "millsite_prices_rejected_rows.csv")

analysis = out[out["include_in_analysis"] == True].copy()
save_csv(analysis, PROCESSED_DIR / "millsite_prices_monthly_analysis.csv")

print("\nSaved:")
print("- data/processed/millsite_prices_monthly.csv")
print("- data/processed/millsite_prices_monthly_analysis.csv")
print("- outputs/audit/millsite_prices_rejected_rows.csv")
print(f"\nRows parsed: {len(out)}")
print(f"Rows included in analysis: {len(analysis)}")

if not out.empty:
    print("\nCrop years found:")
    print(sorted(out["crop_year"].dropna().unique()))

    print("\nPrice types found:")
    print(sorted(out["price_type"].dropna().unique()))

    print("\nSurvey status counts:")
    print(out["survey_status"].value_counts(dropna=False))