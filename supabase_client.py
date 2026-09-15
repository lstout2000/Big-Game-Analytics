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

def upload_dataframe(df):
    """
    Upload a pandas DataFrame to the utah_draw_results table.
    """

    # Convert DataFrame into a list of dictionaries
    records = df.to_dict(orient="records")

    if not records:
        print("No records to upload.")
        return

    # Insert records into Supabase
    response = (
        supabase
        .table("utah_draw_results")
        .insert(records)
        .execute()
    )

    print(f"Uploaded {len(records)} rows to Supabase.")

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