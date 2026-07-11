from pathlib import Path
import re
import pandas as pd

from sugarstats_helpers import (
    MONTH_ORDER,
    parse_number,
    read_extracted_tables,
    load_crop_year_mapping,
    save_csv,
    save_rejected_rows,
)

PROCESSED_DIR = Path("data/processed")
AUDIT_DIR = Path("outputs/audit")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

df = read_extracted_tables("metro_manila_prices")
mapping = load_crop_year_mapping()

if df.empty:
    raise ValueError(
        "No extracted Metro Manila price tables found. "
        "Check that your CSV files are inside data/extracted/metro_manila_prices/<source_period>/"
    )

print("Loaded extracted Metro Manila rows:", len(df))
print("Columns:", df.columns.tolist())
print(df.head())


MONTH_ALIASES = {
    "sep": "september",
    "sept": "september",
    "september": "september",
    "oct": "october",
    "october": "october",
    "nov": "november",
    "november": "november",
    "dec": "december",
    "december": "december",
    "jan": "january",
    "january": "january",
    "feb": "february",
    "february": "february",
    "mar": "march",
    "march": "march",
    "apr": "april",
    "april": "april",
    "may": "may",
    "jun": "june",
    "june": "june",
    "jul": "july",
    "july": "july",
    "aug": "august",
    "august": "august",
}


def clean_cell(value):
    if pd.isna(value):
        return ""
    text = str(value).replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def detect_month(value):
    """
    Detects month from values like:
    September
    September, 2014
    Sept. 2014
    Sep 2014
    """
    text = clean_cell(value).lower()
    text = text.replace(".", "")
    text = text.replace(",", " ")
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    for word in text.split():
        if word in MONTH_ALIASES:
            return MONTH_ALIASES[word]

    compact = re.sub(r"[^a-z]", "", text)
    return MONTH_ALIASES.get(compact)


def detect_crop_year_from_text(value):
    """
    Detects crop year from text like:
    2024-2025
    CY 2024-2025
    Crop Year 2024–2025
    """
    text = clean_cell(value)

    match = re.search(r"(20\d{2})\s*[-–]\s*(20\d{2})", text)
    if not match:
        return None

    return f"{match.group(1)}-{match.group(2)}"


def detect_crop_year_from_month_cell(value):
    """
    Detects crop year from a month cell like:
    September, 2014

    Since sugar crop year starts in September:
    September, 2014 = 2014-2015
    October = keep current crop year
    August = keep current crop year
    """
    text = clean_cell(value)

    month = detect_month(text)
    match = re.search(r"(20\d{2})|['’](\d{2})\b", text)
    if not match:
        return None

    if match.group(1):
        observed_year = int(match.group(1))
    else:
        observed_year = 2000 + int(match.group(2))

    if month in {"september", "october", "november", "december"}:
        start_year = observed_year
    else:
        start_year = observed_year - 1

    return f"{start_year}-{start_year + 1}"


def is_header_or_note_row(joined_lower):
    """
    Rows that are useful for context but not price observations.
    """
    keywords = [
        "month",
        "raw",
        "washed",
        "refined",
        "wholesale",
        "retail",
        "peso",
        "per lkg",
        "per kilo",
        "public wet market",
        "supermarkets",
        "groceries",
        "source",
        "average",
        "prevailing",
        "crop year",
    ]

    return any(keyword in joined_lower for keyword in keywords)


def classify_price_position(position):
    """
    Expected order for Monthly Average Sugar Prices in Metro Manila:

    1-3 = Wholesale Raw / Washed / Refined, PHP/LKg
    4-6 = Retail public wet market Raw / Washed / Refined, PHP/kg
    7-9 = Retail supermarket/grocery Raw / Washed / Refined, PHP/kg
    """
    labels = {
        1: ("wholesale", "raw_sugar", "PHP/LKg"),
        2: ("wholesale", "washed_sugar", "PHP/LKg"),
        3: ("wholesale", "refined_sugar", "PHP/LKg"),
        4: ("retail_wet_market", "raw_sugar", "PHP/kg"),
        5: ("retail_wet_market", "washed_sugar", "PHP/kg"),
        6: ("retail_wet_market", "refined_sugar", "PHP/kg"),
        7: ("retail_supermarket_grocery", "raw_sugar", "PHP/kg"),
        8: ("retail_supermarket_grocery", "washed_sugar", "PHP/kg"),
        9: ("retail_supermarket_grocery", "refined_sugar", "PHP/kg"),
    }

    return labels.get(position, (f"unmapped_position_{position}", "unknown", "unknown"))


rows = []
rejected_rows = []

crop_year_pattern = re.compile(r"20\d{2}\s*[-–]\s*20\d{2}")

for source_file, file_df in df.groupby("source_file"):
    source_period = file_df["source_period"].iloc[0]

    print(f"\nProcessing: {source_file}")

    fallback_crop_years = (
        mapping[mapping["source_period"] == source_period]
        .sort_values("value_position")["crop_year"]
        .tolist()
    )

    current_crop_year = None
    in_prevailing_section = False

    for _, row in file_df.iterrows():
        cells_dict = row.to_dict()

        visible_cells = [
            clean_cell(v)
            for k, v in cells_dict.items()
            if k not in {"source_period", "source_file"}
        ]

        joined = " | ".join(visible_cells)
        joined_lower = joined.lower()

        # Detect crop year anywhere in the row.
        detected_crop_year = detect_crop_year_from_text(joined)
        if detected_crop_year:
            current_crop_year = detected_crop_year

        # Track section. We only want monthly average prices.
        if "prevailing" in joined_lower:
            in_prevailing_section = True
            rejected_rows.append({
                "source_period": source_period,
                "source_file": source_file,
                "crop_year": current_crop_year,
                "month": None,
                "raw_row": joined,
                "reason": "prevailing_section_started_skipped",
            })
            continue

        if "monthly average" in joined_lower or "average sugar prices" in joined_lower:
            in_prevailing_section = False
            continue

        if in_prevailing_section:
            if joined.strip():
                rejected_rows.append({
                    "source_period": source_period,
                    "source_file": source_file,
                    "crop_year": current_crop_year,
                    "month": None,
                    "raw_row": joined,
                    "reason": "prevailing_price_row_skipped",
                })
            continue

        # Detect month from any cell.
        month = None
        month_cell = None

        for cell in visible_cells:
            detected_month = detect_month(cell)
            if detected_month:
                month = detected_month
                month_cell = cell
                break

        if not month:
            if joined.strip() and not is_header_or_note_row(joined_lower):
                rejected_rows.append({
                    "source_period": source_period,
                    "source_file": source_file,
                    "crop_year": current_crop_year,
                    "month": None,
                    "raw_row": joined,
                    "reason": "month_not_detected",
                })
            continue

        # Detect crop year from month cell, e.g., September, 2014.
        detected_from_month = detect_crop_year_from_month_cell(month_cell)
        if detected_from_month:
            current_crop_year = detected_from_month

        # Fallback if no crop year was detected from text.
        if current_crop_year is None and fallback_crop_years:
            current_crop_year = fallback_crop_years[0]

        if current_crop_year is None:
            rejected_rows.append({
                "source_period": source_period,
                "source_file": source_file,
                "crop_year": None,
                "month": month.title(),
                "raw_row": joined,
                "reason": "crop_year_not_detected",
            })
            continue

        # Parse numeric prices.
        numeric_values = []

        for cell in visible_cells:
            value = parse_number(cell)
            if value is not None:
                numeric_values.append(value)

        if len(numeric_values) == 0:
            rejected_rows.append({
                "source_period": source_period,
                "source_file": source_file,
                "crop_year": current_crop_year,
                "month": month.title(),
                "raw_row": joined,
                "reason": "month_row_no_numeric_values",
            })
            continue

        # Important:
        # If the month cell is "September, 2014", parse_number may extract 2014
        # depending on your helper. Remove the year if it got included as a value.
        if detected_from_month and numeric_values:
            year_in_month_cell = re.search(r"(20\d{2})|['’](\d{2})\b", clean_cell(month_cell))
            if year_in_month_cell:
                year_number = float(year_in_month_cell.group(1) or year_in_month_cell.group(2))
                numeric_values = [v for v in numeric_values if v != year_number]

        if len(numeric_values) == 0:
            rejected_rows.append({
                "source_period": source_period,
                "source_file": source_file,
                "crop_year": current_crop_year,
                "month": month.title(),
                "raw_row": joined,
                "reason": "only_year_detected_no_price_values",
            })
            continue

        for position, price in enumerate(numeric_values, start=1):
            market_level, product_type, unit = classify_price_position(position)

            rows.append({
                "crop_year": current_crop_year,
                "month": month.title(),
                "month_order": MONTH_ORDER[month],
                "price_kind": "monthly_average",
                "market_level": market_level,
                "product_type": product_type,
                "unit": unit,
                "value_position": position,
                "price": price,
                "source_period": source_period,
                "source_file": source_file,
            })


expected_columns = [
    "crop_year",
    "month",
    "month_order",
    "price_kind",
    "market_level",
    "product_type",
    "unit",
    "value_position",
    "price",
    "source_period",
    "source_file",
]

out = pd.DataFrame(rows)

if out.empty:
    out = pd.DataFrame(columns=expected_columns)
else:
    out = out[expected_columns]

save_csv(out, PROCESSED_DIR / "metro_manila_prices_monthly.csv")
save_rejected_rows(rejected_rows, AUDIT_DIR / "metro_manila_prices_rejected_rows.csv")

print("\nSaved:")
print("- data/processed/metro_manila_prices_monthly.csv")
print("- outputs/audit/metro_manila_prices_rejected_rows.csv")

print(f"\nRows parsed: {len(out)}")

if not out.empty:
    print("\nCrop years found:")
    print(sorted(out["crop_year"].dropna().unique()))

    print("\nRows by crop year:")
    print(out.groupby("crop_year").size())

    print("\nMarket levels found:")
    print(sorted(out["market_level"].dropna().unique()))

    print("\nProduct types found:")
    print(sorted(out["product_type"].dropna().unique()))
else:
    print("\nNo rows parsed. Open outputs/audit/metro_manila_prices_rejected_rows.csv")
