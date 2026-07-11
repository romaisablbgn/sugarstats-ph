from pathlib import Path
import pandas as pd
import tabula

MANIFEST_PATH = Path("config/sra_files.csv")
EXTRACTED_DIR = Path("data/extracted")
AUDIT_DIR = Path("outputs/audit")

EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

manifest = pd.read_csv(MANIFEST_PATH)

audit_rows = []


def extract_with_mode(pdf_path, mode):
    """
    mode='lattice' works better for tables with visible grid lines.
    mode='stream' works better for tables separated by spaces.
    """
    kwargs = {
        "pages": "all",
        "multiple_tables": True,
        "pandas_options": {"header": None},
    }

    if mode == "lattice":
        kwargs["lattice"] = True
        kwargs["stream"] = False
    elif mode == "stream":
        kwargs["stream"] = True
        kwargs["lattice"] = False

    return tabula.read_pdf(str(pdf_path), **kwargs)


for _, row in manifest.iterrows():
    dataset = row["dataset"]
    source_period = row["source_period"]
    pdf_path = Path(row["path"])

    print(f"\nExtracting {dataset} | {source_period}")
    print(f"PDF: {pdf_path}")

    output_folder = EXTRACTED_DIR / dataset / source_period
    output_folder.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        audit_rows.append({
            "dataset": dataset,
            "source_period": source_period,
            "path": str(pdf_path),
            "status": "missing_file",
            "mode_used": None,
            "tables_found": 0,
        })
        print("Missing file.")
        continue

    try:
        tables = extract_with_mode(pdf_path, mode="lattice")
        mode_used = "lattice"

        if len(tables) == 0:
            tables = extract_with_mode(pdf_path, mode="stream")
            mode_used = "stream"

        # Some PDFs extract tables but badly in lattice.
        # Save all outputs so we can inspect later.
        for i, table in enumerate(tables, start=1):
            output_file = output_folder / f"table_{i:02d}_{mode_used}.csv"
            table.to_csv(output_file, index=False)

        audit_rows.append({
            "dataset": dataset,
            "source_period": source_period,
            "path": str(pdf_path),
            "status": "success",
            "mode_used": mode_used,
            "tables_found": len(tables),
        })

        print(f"Success: {len(tables)} tables using {mode_used}")

    except Exception as e:
        audit_rows.append({
            "dataset": dataset,
            "source_period": source_period,
            "path": str(pdf_path),
            "status": f"error: {e}",
            "mode_used": None,
            "tables_found": 0,
        })
        print(f"Error: {e}")

audit = pd.DataFrame(audit_rows)
audit.to_csv(AUDIT_DIR / "extraction_report.csv", index=False)

print("\nDone. Check outputs/audit/extraction_report.csv")