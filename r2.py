import os
from pathlib import Path

import boto3
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


# R2 settings
ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")

BUCKET_NAME = "big-game-analytics"
FOLDER = "Utah/"
FILE_PATTERN = "_limited_entry_draw_results.pdf"

# R2's S3-compatible endpoint
ENDPOINT_URL = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"


def get_r2_client():
    """Create a connection to Cloudflare R2."""

    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_ACCESS_KEY,
        region_name="auto"
    )


def find_draw_files():
    """Find all limited-entry draw result PDFs in the Utah folder."""

    s3 = get_r2_client()

    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=FOLDER
    )

    files = []

    for item in response.get("Contents", []):
        filename = item["Key"]

        if filename.endswith(FILE_PATTERN):
            files.append(filename)

    return files


def download_file(r2_key):
    """Download a file from R2 to the local temp folder."""

    s3 = get_r2_client()

    temp_folder = Path("temp")
    temp_folder.mkdir(exist_ok=True)

    filename = Path(r2_key).name
    local_path = temp_folder / filename

    s3.download_file(
        BUCKET_NAME,
        r2_key,
        str(local_path)
    )

    return local_path


def main():
    print("Checking R2 for draw result files...")

    files = find_draw_files()

    if not files:
        print("No matching files found.")
        return

    print(f"Found {len(files)} matching file(s):")

    for file in files:
        print(f"  {file}")

    # For now, download the first matching file
    file = files[0]

    print(f"\nDownloading: {file}")

    local_path = download_file(file)

    print(f"Downloaded to: {local_path}")


if __name__ == "__main__":
    main()