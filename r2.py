import os
from pathlib import Path

import boto3
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")

BUCKET_NAME = "big-game-analytics"

R2_ENDPOINT = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"


def get_r2_client():
    """Create and return an R2 client."""

    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_ACCESS_KEY,
    )


def get_draw_result_files():
    """
    Find all limited-entry draw result PDFs in the Utah folder.
    """

    s3 = get_r2_client()

    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix="Utah/"
    )

    files = []

    for obj in response.get("Contents", []):

        key = obj["Key"]

        if key.endswith("_limited_entry_draw_results.pdf"):
            files.append(key)

    print(f"Found {len(files)} draw result file(s):")

    for file in files:
        print(f"  {file}")

    return files


def download_file(r2_key):
    """Download a file from R2 to the local temp folder."""

    s3 = get_r2_client()

    base_dir = Path(__file__).resolve().parent
    temp_folder = base_dir / "temp"

    temp_folder.mkdir(exist_ok=True)

    filename = Path(r2_key).name
    local_path = temp_folder / filename

    s3.download_file(
        BUCKET_NAME,
        r2_key,
        str(local_path)
    )

    print(f"Downloaded to: {local_path}")

    return local_path


