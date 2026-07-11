from pathlib import Path
import pandas as pd
import tabula

manifest = pd.read_csv("config/sra_files.csv")

price_datasets = ["metro_manila_prices", "millsite_prices"]

for _, row in manifest[manifest["dataset"].isin(price_datasets)].iterrows():
    dataset = row["dataset"]
    source_period = row["source_period"]
    pdf_path = Path(row["path"])

    if not pdf_path.exists():
        print(f"Missing: {pdf_path}")
        continue

    output_folder = Path("data/extracted") / dataset / source_period
    output_folder.mkdir(parents=True, exist_ok=True)

    print(f"Extracting price file using stream mode: {dataset} | {source_period}")

    tables = tabula.read_pdf(
        str(pdf_path),
        pages="all",
        multiple_tables=True,
        stream=True,
        guess=True,
        pandas_options={"header": None},
    )

    for i, table in enumerate(tables, start=1):
        output_file = output_folder / f"price_stream_table_{i:02d}.csv"
        table.to_csv(output_file, index=False)

    print(f"Saved {len(tables)} stream tables for {dataset} | {source_period}")