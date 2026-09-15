import re
from pathlib import Path

import pandas as pd
import pdfplumber


# ---------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------

HUNT_PATTERN = re.compile(
    r"^Hunt:\s+(\S+)\s+(.+?)\s+Page\s+\d+$"
)

ROW_PATTERN = re.compile(
    r"^"
    r"(\d+)\s+"              # Resident bonus points
    r"(\d+)\s+"              # Resident applicants
    r"(\d+)\s+"              # Resident bonus permits
    r"(\d+)\s+"              # Resident regular permits
    r"(\d+)\s+"              # Resident total permits
    r"(N/A|1 in [\d.]+)\s+"  # Resident success ratio
    r"(\d+)\s+"              # Nonresident bonus points
    r"(\d+)\s+"              # Nonresident applicants
    r"(\d+)\s+"              # Nonresident bonus permits
    r"(\d+)\s+"              # Nonresident regular permits
    r"(\d+)\s+"              # Nonresident total permits
    r"(N/A|1 in [\d.]+)"     # Nonresident success ratio
    r"$"
)

TOTAL_PATTERN = re.compile(
    r"^Totals\s+"
    r"(\d+)\s+"               # Resident applicants
    r"(\d+)\s+"               # Resident bonus permits
    r"(\d+)\s+"               # Resident regular permits
    r"(\d+)\s+"               # Resident total permits
    r"(N/A|1 in [\d.]+)\s+"
    r"Totals\s+"
    r"(\d+)\s+"               # Nonresident applicants
    r"(\d+)\s+"               # Nonresident bonus permits
    r"(\d+)\s+"               # Nonresident regular permits
    r"(\d+)\s+"               # Nonresident total permits
    r"(N/A|1 in [\d.]+)"
    r"$"
)


def get_species(hunt_name):
    """Determine species from the hunt name."""

    name = hunt_name.lower()

    if "bighorn sheep" in name:
        return "Bighorn Sheep"
    elif "mountain goat" in name:
        return "Mountain Goat"
    elif "bison" in name:
        return "Bison"
    elif "moose" in name:
        return "Moose"
    elif "pronghorn" in name:
        return "Pronghorn"
    elif "elk" in name:
        return "Elk"
    elif "deer" in name:
        return "Deer"
    else:
        return "Unknown"


def get_weapon(hunt_name):
    """Extract the weapon from the end of the hunt name."""

    weapon_options = [
        "Any Legal Weapon",
        "Muzzleloader",
        "Archery",
    ]

    for weapon in weapon_options:
        if hunt_name.endswith(f" - {weapon}"):
            return weapon

    return "Unknown"


def clean_hunt_name(hunt_name):
    """Remove the weapon from the hunt name."""

    weapon = get_weapon(hunt_name)

    if weapon != "Unknown":
        return hunt_name[:-len(f" - {weapon}")]

    return hunt_name


# ---------------------------------------------------------
# Parse PDF
# ---------------------------------------------------------

def parse_pdf(pdf_path):
    """
    Read the Utah limited-entry draw results PDF
    and return a database-ready DataFrame.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    records = []

    with pdfplumber.open(pdf_path) as pdf:

        for page_number, page in enumerate(pdf.pages, start=1):

            text = page.extract_text()

            if not text:
                continue

            lines = text.splitlines()

            # ---------------------------------------------
            # Find hunt metadata
            # ---------------------------------------------

            hunt_match = None

            for line in lines:

                match = HUNT_PATTERN.match(line)

                if match:
                    hunt_match = match
                    break

            # Page 1 is the overall species summary,
            # not an individual hunt.
            if not hunt_match:
                continue

            hunt_number = hunt_match.group(1)
            full_hunt_name = hunt_match.group(2)

            weapon = get_weapon(full_hunt_name)
            hunt_name = clean_hunt_name(full_hunt_name)
            species = get_species(full_hunt_name)

            # Year comes from the PDF filename.
            year_match = re.search(
                r"(20\d{2})",
                pdf_path.name
            )

            if year_match:
                year = int(year_match.group(1))
            else:
                year = None

            # ---------------------------------------------
            # Extract table rows
            # ---------------------------------------------

            for line in lines:

                row_match = ROW_PATTERN.match(line)

                if not row_match:
                    continue

                values = row_match.groups()

                (
                    resident_points,
                    resident_applicants,
                    resident_bonus_permits,
                    resident_regular_permits,
                    resident_total_permits,
                    resident_success,

                    nonresident_points,
                    nonresident_applicants,
                    nonresident_bonus_permits,
                    nonresident_regular_permits,
                    nonresident_total_permits,
                    nonresident_success
                ) = values

                # -----------------------------------------
                # Resident record
                # -----------------------------------------

                records.append({
                    "year": year,
                    "species": species,
                    "weapon": weapon,
                    "hunt_number": hunt_number,
                    "hunt_name": hunt_name,
                    "residency": "Resident",
                    "bonus_points": int(resident_points),
                    "applicants": int(resident_applicants),
                    "bonus_permits": int(resident_bonus_permits),
                    "regular_permits": int(resident_regular_permits),
                    "total_permits": int(resident_total_permits),
                    "success_ratio": resident_success,
                })

                # -----------------------------------------
                # Nonresident record
                # -----------------------------------------

                records.append({
                    "year": year,
                    "species": species,
                    "weapon": weapon,
                    "hunt_number": hunt_number,
                    "hunt_name": hunt_name,
                    "residency": "Nonresident",
                    "bonus_points": int(nonresident_points),
                    "applicants": int(nonresident_applicants),
                    "bonus_permits": int(nonresident_bonus_permits),
                    "regular_permits": int(nonresident_regular_permits),
                    "total_permits": int(nonresident_total_permits),
                    "success_ratio": nonresident_success,
                })

    df = pd.DataFrame(records)

    return df


# ---------------------------------------------------------
# Test the parser directly
# ---------------------------------------------------------

if __name__ == "__main__":

    pdf_path = "temp/2025_limited_entry_draw_results.pdf"

    df = parse_pdf(pdf_path)

    print("\nParsing complete.")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 10 rows:")
    print(df.head(10).to_string(index=False))

    print("\nSpecies:")
    print(df["species"].value_counts())

    # Save a temporary CSV so we can inspect the result.
    output_path = "temp/parsed_draw_results.csv"

    df.to_csv(
        output_path,
        index=False
    )

    print(f"\nSaved test output to: {output_path}")