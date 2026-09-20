import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing from .env")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is missing from .env")


# ---------------------------------------------------------
# Connect to Supabase
# ---------------------------------------------------------

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ---------------------------------------------------------
# Upload DataFrame
# ---------------------------------------------------------

def is_file_processed(r2_key):
    """
    Check whether this R2 file has already been successfully imported.
    """
    response = (
        supabase
        .table("ImportLog")
        .select("id")
        .eq("r2Key", r2_key)
        .eq("status", "SUCCESS")
        .limit(1)
        .execute()
    )

    return len(response.data) > 0


def delete_file_data(source_file):
    """
    Delete all draw-result rows that came from a specific R2 file.
    """

    print(f"Removing existing data for: {source_file}")

    (
        supabase
        .table("utahDrawResults")
        .delete()
        .eq("sourceFile", source_file)
        .execute()
    )

    print("Existing data removed.")

def upload_dataframe(df, source_file):
    """
    Upload the DataFrame to Supabase in batches.
    """

    df = df.copy()

    # Add the R2 file that produced these rows
    df["sourceFile"] = source_file

    batch_size = 1000
    total_rows = len(df)

    print(
        f"Uploading {total_rows:,} rows "
        f"in batches of {batch_size:,}..."
    )

    for start in range(0, total_rows, batch_size):

        end = start + batch_size

        batch = df.iloc[start:end]

        records = batch.to_dict(orient="records")

        (
            supabase
            .table("utahDrawResults")
            .insert(records)
            .execute()
        )

        print(
            f"Uploaded rows "
            f"{start + 1:,} - {min(end, total_rows):,}"
        )

    print(
        f"Successfully uploaded all "
        f"{total_rows:,} rows."
    )


def log_import_success(r2_key, rows_imported):
    """
    Record a successful file import.
    """

    filename = r2_key.split("/")[-1]

    response = (
        supabase
        .table("ImportLog")
        .insert({
            "fileName": filename,
            "r2Key": r2_key,
            "status": "SUCCESS",
            "rowsImported": rows_imported
        })
        .execute()
    )

    return response



def log_import_failure(r2_key, error_message):
    """
    Record a failed file import.
    """

    filename = r2_key.split("/")[-1]

    response = (
        supabase
        .table("ImportLog")
        .insert({
            "fileName": filename,
            "r2Key": r2_key,
            "status": "FAILED",
            "errorMessage": error_message
        })
        .execute()
    )

    return response

# ---------------------------------------------------------
# Test
# ---------------------------------------------------------

if __name__ == "__main__":

    from parser import parse_pdf

    pdf_path = BASE_DIR / "temp" / "2025_limited_entry_draw_results.pdf"

    print("Parsing PDF...")

    df = parse_pdf(pdf_path)

    print(f"Parsed {len(df)} rows.")

    print("Uploading to Supabase...")

    upload_dataframe(df)

    print("Done.")
