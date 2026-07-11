import re
from pathlib import Path
import pandas as pd

MONTH_ORDER = {
    "september": 1,
    "october": 2,
    "november": 3,
    "december": 4,
    "january": 5,
    "february": 6,
    "march": 7,
    "april": 8,
    "may": 9,
    "june": 10,
    "july": 11,
    "august": 12,
}

MONTH_NAMES = set(MONTH_ORDER.keys())


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_month(value):
    text = clean_text(value).lower()
    text = re.sub(r"[^a-z]", "", text)
    return text if text in MONTH_NAMES else None


def parse_number(value):
    text = clean_text(value)

    if text == "":
        return None

    lowered = text.lower()

    if lowered in {"-", "–", "—", "na", "n/a", "nan"}:
        return None

    if "terminated" in lowered:
        return None

    text = text.replace(",", "")
    text = text.replace("*", "")
    text = text.replace("₱", "")
    text = re.sub(r"(?<=\d)\s+(?=\d)", "", text)
    text = text.strip()

    try:
        return float(text)
    except ValueError:
        return None


def survey_status(value):
    text = clean_text(value).lower()

    if text == "":
        return "missing"

    if text in {"-", "–", "—", "na", "n/a", "nan"}:
        return "missing"

    if "terminated" in text:
        return "terminated"

    if parse_number(value) is not None:
        return "reported"

    return "unparsed"


def read_extracted_tables(dataset):
    base = Path("data/extracted") / dataset
    frames = []

    for file in base.rglob("*.csv"):
        source_period = file.parent.name
        df = pd.read_csv(file, dtype=str)
        df["source_period"] = source_period
        df["source_file"] = str(file)
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def load_crop_year_mapping():
    mapping = pd.read_csv("config/crop_year_mapping.csv")
    mapping["value_position"] = mapping["value_position"].astype(int)
    return mapping


def assign_crop_year_by_position(df):
    mapping = load_crop_year_mapping()

    df["value_position"] = df["value_position"].astype(int)

    merged = df.merge(
        mapping,
        on=["source_period", "value_position"],
        how="left",
    )

    missing = merged[merged["crop_year"].isna()]
    if not missing.empty:
        Path("outputs/audit").mkdir(parents=True, exist_ok=True)
        missing.to_csv("outputs/audit/missing_crop_year_assignment.csv", index=False)
        print("Warning: some rows did not receive crop_year. Check outputs/audit/missing_crop_year_assignment.csv")

    return merged


def get_numeric_values_from_row(cells):
    values = []

    for cell in cells:
        value = parse_number(cell)
        if value is not None:
            values.append(value)

    return values


def save_csv(df, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def save_rejected_rows(rows, path):
    rejected = pd.DataFrame(rows)
    save_csv(rejected, path)
