import r2
import parser
import supabase_client


def main():

    print("Starting Utah draw data ingestion...")
    print()

    # 1. Find all draw result files in R2
    files = r2.get_draw_result_files()

    if not files:
        print("No draw result files found.")
        return

    print()

    # 2. Check each file
    for r2_key in files:

        print(f"Checking: {r2_key}")

        # Skip files that have already been successfully imported
        if supabase_client.is_file_processed(r2_key):

            print("Already imported. Skipping.")
            print()

            continue

        print("New file found. Processing...")
        print()

        try:

            # 3. Download the file
            pdf_path = r2.download_file(r2_key)

            # 4. Parse the PDF
            print("Parsing PDF...")

            df = parser.parse_pdf(pdf_path)

            print(f"Parsed {len(df):,} rows.")
            print()

            # 5. Remove any data from a previous failed attempt
            supabase_client.delete_file_data(r2_key)

            # 6. Upload the data to Supabase
            print("Uploading data to Supabase...")

            supabase_client.upload_dataframe(
                df,
                r2_key
            )

            print()

            # 7. Record successful import
            supabase_client.log_import_success(
                r2_key,
                len(df)
            )

            print("Import logged successfully.")

            # 8. Delete temporary PDF
            pdf_path.unlink()

            print("Temporary PDF deleted.")
            print()

        except Exception as e:

            print("ERROR:")
            print(e)

            # Record the failed import
            supabase_client.log_import_failure(
                r2_key,
                str(e)
            )

            print("Import failure logged.")
            print()


if __name__ == "__main__":
    main()
