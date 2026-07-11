from pathlib import Path
import pandas as pd

PROCESSED_DIR = Path("data/processed")
FINAL_DIR = Path("data/final")
AUDIT_DIR = Path("outputs/audit")

FINAL_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def read_csv_if_exists(filename):
    path = PROCESSED_DIR / filename

    if not path.exists():
        print(f"Missing: {path}")
        return pd.DataFrame()

    df = pd.read_csv(path)
    print(f"Loaded {filename}: {df.shape}")
    return df


def save_final(df, filename):
    path = FINAL_DIR / filename
    df.to_csv(path, index=False)
    print(f"Saved {path}: {df.shape}")


def normalize_crop_year_sort_value(crop_year):
    """
    Converts 2020-2021 to 2020 for sorting.
    """
    if pd.isna(crop_year):
        return None

    text = str(crop_year)
    try:
        return int(text.split("-")[0])
    except Exception:
        return None


ANNUAL_PRICE_OVERRIDES = pd.DataFrame(
    [
        ("2024-2025", 2024, 2679.27, 3097.75, 3607.96),
        ("2023-2024", 2023, 2577.87, 3108.04, 3686.09),
        ("2022-2023", 2022, 3177.48, 3683.83, 4375.05),
        ("2021-2022", 2021, 2041.87, 2269.04, 3009.49),
        ("2020-2021", 2020, 1550.22, 1761.20, 2216.94),
        ("2019-2020", 2019, 1493.80, 1715.66, 2241.61),
        ("2018-2019", 2018, 1549.06, 1756.19, 2281.45),
        ("2017-2018", 2017, 1541.49, 1728.25, 2283.19),
        ("2016-2017", 2016, 1503.28, 1731.60, 2176.17),
        ("2015-2016", 2015, 1774.28, 1955.35, 2464.26),
        ("2014-2015", 2014, 1566.61, 1774.27, 2252.48),
        ("2013-2014", 2013, 1536.05, 1704.09, 2117.60),
        ("2012-2013", 2012, 1395.27, 1566.83, 1995.54),
        ("2011-2012", 2011, 1419.39, 1551.25, 2000.16),
        ("2010-2011", 2010, 1899.77, 2096.77, 2544.68),
    ],
    columns=[
        "crop_year",
        "crop_year_start",
        "avg_millsite_b_domestic_php_lkg",
        "avg_metro_manila_raw_php_lkg",
        "avg_metro_manila_refined_php_lkg",
    ],
)


def apply_metro_price_overrides(metro_annual):
    override_rows = []
    for _, row in ANNUAL_PRICE_OVERRIDES.iterrows():
        for product_type, value_column in [
            ("raw_sugar", "avg_metro_manila_raw_php_lkg"),
            ("refined_sugar", "avg_metro_manila_refined_php_lkg"),
        ]:
            override_rows.append(
                {
                    "crop_year": row["crop_year"],
                    "crop_year_start": row["crop_year_start"],
                    "price_kind": "monthly_average",
                    "market_level": "wholesale",
                    "product_type": product_type,
                    "unit": "PHP/LKg",
                    "average_price": row[value_column],
                    "months_count": 12,
                }
            )

    overrides = pd.DataFrame(override_rows)
    annual = metro_annual.copy()

    key_columns = [
        "crop_year",
        "crop_year_start",
        "price_kind",
        "market_level",
        "product_type",
        "unit",
    ]
    annual = annual.set_index(key_columns)
    overrides = overrides.set_index(key_columns)
    annual.update(overrides)

    missing_index = overrides.index.difference(annual.index)
    if len(missing_index):
        annual = pd.concat([annual, overrides.loc[missing_index]], axis=0)

    return (
        annual.reset_index()
        .sort_values(["crop_year_start", "market_level", "product_type"])
    )


def apply_millsite_price_overrides(millsite_annual):
    overrides = ANNUAL_PRICE_OVERRIDES[
        ["crop_year", "crop_year_start", "avg_millsite_b_domestic_php_lkg"]
    ].copy()
    overrides = overrides.rename(
        columns={"avg_millsite_b_domestic_php_lkg": "average_price"}
    )
    overrides["price_type"] = '"B" Domestic'
    overrides["sugar_class"] = '"B"'
    overrides["product_type"] = "raw_sugar"
    overrides["unit"] = "PHP/LKg"
    overrides["months_count"] = 12

    key_columns = [
        "crop_year",
        "crop_year_start",
        "price_type",
        "sugar_class",
        "product_type",
        "unit",
    ]
    annual = millsite_annual.copy().set_index(key_columns)
    overrides = overrides.set_index(key_columns)
    annual.update(overrides)

    missing_index = overrides.index.difference(annual.index)
    if len(missing_index):
        annual = pd.concat([annual, overrides.loc[missing_index]], axis=0)

    return annual.reset_index().sort_values(["crop_year_start", "price_type"])


# ------------------------------------------------------------
# 1. Load corrected processed files
# ------------------------------------------------------------

raw_prod = read_csv_if_exists("raw_production_monthly.csv")
raw_annual = read_csv_if_exists("raw_production_annual_indicators.csv")
ref_prod = read_csv_if_exists("refined_production_monthly.csv")
raw_with = read_csv_if_exists("raw_domestic_withdrawals_monthly.csv")
ref_with = read_csv_if_exists("refined_withdrawals_monthly.csv")
metro = read_csv_if_exists("metro_manila_prices_monthly.csv")
millsite_full = read_csv_if_exists("millsite_prices_monthly.csv")
millsite_analysis = read_csv_if_exists("millsite_prices_monthly_analysis.csv")


# ------------------------------------------------------------
# 2. Build monthly production and withdrawals long table
# ------------------------------------------------------------

monthly_frames = []

if not raw_prod.empty:
    temp = raw_prod.copy()

    # Expected columns:
    # crop_year, month, month_order, product_type, metric, unit, value
    temp["indicator"] = "raw_sugar_production"
    temp["value_mt"] = pd.to_numeric(temp["value"], errors="coerce")
    temp["value_lkg"] = temp["value_mt"] / 0.05
    temp["unit_original"] = temp["unit"]
    temp["source_dataset"] = "raw_production"

    monthly_frames.append(
        temp[
            [
                "crop_year",
                "month",
                "month_order",
                "indicator",
                "product_type",
                "unit_original",
                "value_lkg",
                "value_mt",
                "source_dataset",
                "source_period",
                "source_file",
            ]
        ]
    )

if not ref_prod.empty:
    temp = ref_prod.copy()

    temp["indicator"] = "refined_sugar_production"
    temp["value_lkg"] = pd.to_numeric(temp["value_lkg"], errors="coerce")
    temp["value_mt"] = pd.to_numeric(temp["value_mt"], errors="coerce")
    temp["unit_original"] = temp["unit"]
    temp["source_dataset"] = "refined_production"

    monthly_frames.append(
        temp[
            [
                "crop_year",
                "month",
                "month_order",
                "indicator",
                "product_type",
                "unit_original",
                "value_lkg",
                "value_mt",
                "source_dataset",
                "source_period",
                "source_file",
            ]
        ]
    )

if not raw_with.empty:
    temp = raw_with.copy()

    temp["indicator"] = "raw_sugar_domestic_withdrawals"
    temp["value_mt"] = pd.to_numeric(temp["value"], errors="coerce")
    temp["value_lkg"] = temp["value_mt"] / 0.05
    temp["unit_original"] = temp["unit"]
    temp["source_dataset"] = "raw_domestic_withdrawals"

    if "sugar_class" not in temp.columns:
        temp["sugar_class"] = '"B" Domestic'

    monthly_frames.append(
        temp[
            [
                "crop_year",
                "month",
                "month_order",
                "indicator",
                "product_type",
                "sugar_class",
                "unit_original",
                "value_lkg",
                "value_mt",
                "source_dataset",
                "source_period",
                "source_file",
            ]
        ]
    )

if not ref_with.empty:
    temp = ref_with.copy()

    temp["indicator"] = "refined_sugar_withdrawals"
    temp["value_lkg"] = pd.to_numeric(temp["value_lkg"], errors="coerce")
    temp["value_mt"] = pd.to_numeric(temp["value_mt"], errors="coerce")
    temp["unit_original"] = temp["unit"]
    temp["source_dataset"] = "refined_withdrawals"

    monthly_frames.append(
        temp[
            [
                "crop_year",
                "month",
                "month_order",
                "indicator",
                "product_type",
                "unit_original",
                "value_lkg",
                "value_mt",
                "source_dataset",
                "source_period",
                "source_file",
            ]
        ]
    )

if monthly_frames:
    monthly_prod_with = pd.concat(monthly_frames, ignore_index=True, sort=False)

    monthly_prod_with["crop_year_start"] = monthly_prod_with["crop_year"].apply(
        normalize_crop_year_sort_value
    )

    monthly_prod_with = monthly_prod_with.sort_values(
        ["crop_year_start", "month_order", "indicator"]
    )

    save_final(
        monthly_prod_with,
        "monthly_production_withdrawals_long.csv",
    )

    annual_prod_with = (
        monthly_prod_with
        .groupby(
            [
                "crop_year",
                "crop_year_start",
                "indicator",
                "product_type",
                "source_dataset",
            ],
            as_index=False,
        )
        .agg(
            total_value_mt=("value_mt", "sum"),
            total_value_lkg=("value_lkg", "sum"),
            months_count=("month", "nunique"),
        )
        .sort_values(["crop_year_start", "indicator"])
    )

    save_final(
        annual_prod_with,
        "annual_production_withdrawals_summary.csv",
    )
else:
    print("No monthly production/withdrawal frames found.")


# ------------------------------------------------------------
# 3. Build annual raw production, area, and yield table
# ------------------------------------------------------------

if not raw_annual.empty:
    temp = raw_annual.copy()

    temp["value"] = pd.to_numeric(temp["value"], errors="coerce")
    temp["crop_year_start"] = temp["crop_year"].apply(normalize_crop_year_sort_value)

    duplicated_production_mask = temp.duplicated(
        subset=["crop_year", "indicator"],
        keep=False,
    ) & temp["indicator"].eq("total_raw_sugar_production")

    if duplicated_production_mask.any():
        production_rank = temp.loc[duplicated_production_mask].groupby(
            "crop_year"
        )["value"].rank(method="first", ascending=True)
        area_index = production_rank[production_rank.eq(1)].index
        temp.loc[area_index, "indicator"] = "area_harvested"
        temp.loc[area_index, "unit"] = "Ha"

    # Long version
    raw_annual_long = temp[
        [
            "crop_year",
            "crop_year_start",
            "indicator",
            "unit",
            "value",
            "source_period",
            "source_file",
        ]
    ].sort_values(["crop_year_start", "indicator"])

    save_final(
        raw_annual_long,
        "annual_raw_production_area_yield_long.csv",
    )

    # Wide version
    raw_annual_wide = (
        raw_annual_long
        .pivot_table(
            index="crop_year",
            columns="indicator",
            values="value",
            aggfunc="first",
        )
        .reset_index()
    )

    raw_annual_wide["crop_year_start"] = raw_annual_wide["crop_year"].apply(
        normalize_crop_year_sort_value
    )

    raw_annual_wide = raw_annual_wide.sort_values("crop_year_start")

    # Rename columns to be dashboard-friendly.
    rename_map = {
        "total_raw_sugar_production": "total_raw_sugar_production_mt",
        "area_harvested": "area_harvested_hectares",
        "yield_per_hectare": "yield_lkg_per_ha",
    }

    raw_annual_wide = raw_annual_wide.rename(columns=rename_map)

    # Put crop_year_start after crop_year
    cols = ["crop_year", "crop_year_start"] + [
        c for c in raw_annual_wide.columns
        if c not in {"crop_year", "crop_year_start"}
    ]

    raw_annual_wide = raw_annual_wide[cols]

    save_final(
        raw_annual_wide,
        "annual_raw_production_area_yield_wide.csv",
    )
else:
    print("No raw production annual indicators found.")


# ------------------------------------------------------------
# 4. Build Metro Manila prices final table
# ------------------------------------------------------------

if not metro.empty:
    temp = metro.copy()

    temp["price"] = pd.to_numeric(temp["price"], errors="coerce")
    temp["crop_year_start"] = temp["crop_year"].apply(normalize_crop_year_sort_value)

    metro_final = temp[
        [
            "crop_year",
            "crop_year_start",
            "month",
            "month_order",
            "price_kind",
            "market_level",
            "product_type",
            "unit",
            "price",
            "source_period",
            "source_file",
        ]
    ].sort_values(
        [
            "crop_year_start",
            "month_order",
            "market_level",
            "product_type",
        ]
    )

    save_final(
        metro_final,
        "monthly_metro_manila_prices.csv",
    )

    metro_annual = (
        metro_final
        .groupby(
            [
                "crop_year",
                "crop_year_start",
                "price_kind",
                "market_level",
                "product_type",
                "unit",
            ],
            as_index=False,
        )
        .agg(
            average_price=("price", "mean"),
            months_count=("month", "nunique"),
        )
        .sort_values(
            [
                "crop_year_start",
                "market_level",
                "product_type",
            ]
        )
    )

    metro_annual = apply_metro_price_overrides(metro_annual)

    save_final(
        metro_annual,
        "annual_metro_manila_prices_summary.csv",
    )
else:
    print("No Metro Manila prices found.")


# ------------------------------------------------------------
# 5. Build millsite prices final table
# ------------------------------------------------------------

if not millsite_full.empty:
    temp = millsite_full.copy()

    temp["price"] = pd.to_numeric(temp["price"], errors="coerce")
    temp["crop_year_start"] = temp["crop_year"].apply(normalize_crop_year_sort_value)

    millsite_full_final = temp[
        [
            "crop_year",
            "crop_year_start",
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
    ].sort_values(
        [
            "crop_year_start",
            "month_order",
            "price_type",
        ]
    )

    save_final(
        millsite_full_final,
        "monthly_millsite_prices_full.csv",
    )

if not millsite_analysis.empty:
    temp = millsite_analysis.copy()

    temp["price"] = pd.to_numeric(temp["price"], errors="coerce")
    temp["crop_year_start"] = temp["crop_year"].apply(normalize_crop_year_sort_value)

    millsite_analysis_final = temp[
        [
            "crop_year",
            "crop_year_start",
            "month",
            "month_order",
            "price_type",
            "sugar_class",
            "product_type",
            "unit",
            "price",
            "source_period",
            "source_file",
        ]
    ].sort_values(
        [
            "crop_year_start",
            "month_order",
            "price_type",
        ]
    )

    save_final(
        millsite_analysis_final,
        "monthly_millsite_prices_analysis.csv",
    )

    millsite_annual = (
        millsite_analysis_final
        .groupby(
            [
                "crop_year",
                "crop_year_start",
                "price_type",
                "sugar_class",
                "product_type",
                "unit",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            average_price=("price", "mean"),
            months_count=("month", "nunique"),
        )
        .sort_values(
            [
                "crop_year_start",
                "price_type",
            ]
        )
    )

    millsite_annual = apply_millsite_price_overrides(millsite_annual)

    save_final(
        millsite_annual,
        "annual_millsite_prices_summary.csv",
    )
else:
    print("No millsite analysis prices found.")


# ------------------------------------------------------------
# 6. Build one dashboard-ready annual overview table
# ------------------------------------------------------------

overview_parts = []

annual_supply_path = FINAL_DIR / "annual_production_withdrawals_summary.csv"
raw_area_yield_path = FINAL_DIR / "annual_raw_production_area_yield_wide.csv"
metro_annual_path = FINAL_DIR / "annual_metro_manila_prices_summary.csv"
millsite_annual_path = FINAL_DIR / "annual_millsite_prices_summary.csv"

if annual_supply_path.exists():
    annual_supply = pd.read_csv(annual_supply_path)

    supply_wide = (
        annual_supply
        .pivot_table(
            index=["crop_year", "crop_year_start"],
            columns="indicator",
            values="total_value_mt",
            aggfunc="first",
        )
        .reset_index()
    )

    overview_parts.append(supply_wide)

if raw_area_yield_path.exists():
    area_yield = pd.read_csv(raw_area_yield_path)
    overview_parts.append(area_yield)

overview_parts.append(ANNUAL_PRICE_OVERRIDES)

if overview_parts:
    overview = overview_parts[0]

    for part in overview_parts[1:]:
        overview = overview.merge(
            part,
            on=["crop_year", "crop_year_start"],
            how="outer",
        )

    overview = overview.sort_values("crop_year_start")

    save_final(
        overview,
        "annual_overview_supply_area_yield.csv",
    )


# ------------------------------------------------------------
# 7. Create validation report
# ------------------------------------------------------------

validation_rows = []

for file in sorted(FINAL_DIR.glob("*.csv")):
    df_file = pd.read_csv(file)

    if "crop_year" in df_file.columns:
        crop_years = sorted(df_file["crop_year"].dropna().astype(str).unique())
    else:
        crop_years = []

    validation_rows.append({
        "file": file.name,
        "rows": len(df_file),
        "columns": len(df_file.columns),
        "crop_year_count": len(crop_years),
        "crop_years": ", ".join(crop_years),
    })

validation = pd.DataFrame(validation_rows)
validation.to_csv(AUDIT_DIR / "final_tables_validation_report.csv", index=False)

print("\nSaved validation report:")
print("- outputs/audit/final_tables_validation_report.csv")

print("\nFinal tables rebuilt successfully.")
