import duckdb
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

YEARS = [
    2019,
    2021,
    2022,
    2023,
    2024
]


# ============================================================
# EXPECTED PHARMACY COLUMNS
# ============================================================

EXPECTED_COLUMNS = [
    "Prscrbr_NPI",
    "Prscrbr_Last_Org_Name",
    "Prscrbr_First_Name",
    "Prscrbr_City",
    "Prscrbr_State_Abrvtn",
    "Prscrbr_State_FIPS",
    "Prscrbr_Type",
    "Prscrbr_Type_Src",
    "Brnd_Name",
    "Gnrc_Name",
    "Tot_Clms",
    "Tot_30day_Fills",
    "Tot_Day_Suply",
    "Tot_Drug_Cst",
    "Tot_Benes",
    "GE65_Sprsn_Flag",
    "GE65_Tot_Clms",
    "GE65_Tot_30day_Fills",
    "GE65_Tot_Drug_Cst",
    "GE65_Tot_Day_Suply",
    "GE65_Bene_Sprsn_Flag",
    "GE65_Tot_Benes",
]


# ============================================================
# NUMERIC PHARMACY COLUMNS
# ============================================================

NUMERIC_COLUMNS = [
    "Tot_Clms",
    "Tot_30day_Fills",
    "Tot_Day_Suply",
    "Tot_Drug_Cst",
    "Tot_Benes",
    "GE65_Tot_Clms",
    "GE65_Tot_30day_Fills",
    "GE65_Tot_Drug_Cst",
    "GE65_Tot_Day_Suply",
    "GE65_Tot_Benes",
]


# ============================================================
# DUCKDB
# ============================================================

con = duckdb.connect()


# ============================================================
# HELPER
# ============================================================

def processed_file(year):
    return (
        PROCESSED_DIR
        / f"pharmacy_{year}_processed.parquet"
    )


# ============================================================
# SCHEMA VALIDATION
# ============================================================

def validate_schema(year, file_path):

    print("\n" + "-" * 80)
    print(f"SCHEMA VALIDATION - {year}")
    print("-" * 80)

    schema = con.execute(
        f"""
        DESCRIBE
        SELECT *
        FROM read_parquet('{file_path.as_posix()}')
        """
    ).fetchdf()

    actual_columns = schema["column_name"].tolist()

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in actual_columns
    ]

    if missing_columns:

        print("STATUS: FAILED")

        print("\nMissing expected columns:")

        for column in missing_columns:
            print(f"  - {column}")

        return False

    print("STATUS: PASSED")
    print("All expected Pharmacy columns are present.")

    return True


# ============================================================
# MISSING VALUE VALIDATION
# ============================================================

def validate_missing_values(year, file_path):

    print("\n" + "-" * 80)
    print(f"MISSING VALUE VALIDATION - {year}")
    print("-" * 80)

    schema = con.execute(
        f"""
        DESCRIBE
        SELECT *
        FROM read_parquet('{file_path.as_posix()}')
        """
    ).fetchdf()

    columns = schema["column_name"].tolist()

    total_rows = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{file_path.as_posix()}')
        """
    ).fetchone()[0]

    findings = []

    for column in columns:

        result = con.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet('{file_path.as_posix()}')
            WHERE "{column}" IS NULL
            """
        ).fetchone()[0]

        if result > 0:

            percentage = (
                result / total_rows * 100
                if total_rows > 0
                else 0
            )

            findings.append(
                (
                    column,
                    result,
                    percentage
                )
            )

    if not findings:

        print("No NULL values detected.")

        return

    print(
        f"{'Column':35}"
        f"{'NULL Count':15}"
        f"{'NULL %':10}"
    )

    for column, count, percentage in sorted(
        findings,
        key=lambda x: x[1],
        reverse=True
    ):

        print(
            f"{column:35}"
            f"{count:<15,}"
            f"{percentage:>8.2f}%"
        )

    print(
        "\nNOTE:"
        "\nNULL values are NOT automatically classified "
        "as anomalies."
    )


# ============================================================
# NEGATIVE VALUE VALIDATION
# ============================================================

def validate_negative_values(year, file_path):

    print("\n" + "-" * 80)
    print(f"INVALID NEGATIVE VALUES - {year}")
    print("-" * 80)

    for column in NUMERIC_COLUMNS:

        result = con.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet('{file_path.as_posix()}')
            WHERE "{column}" < 0
            """
        ).fetchone()[0]

        if result > 0:

            print(
                f"ANOMALY | {column} | "
                f"{result:,} negative values"
            )

        else:

            print(
                f"OK      | {column}"
            )


# ============================================================
# ZERO / NEGATIVE BASIC VALIDATION
# ============================================================

def validate_basic_values(year, file_path):

    print("\n" + "-" * 80)
    print(f"BASIC VALUE VALIDATION - {year}")
    print("-" * 80)

    for column in NUMERIC_COLUMNS:

        result = con.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet('{file_path.as_posix()}')
            WHERE "{column}" < 0
            """
        ).fetchone()[0]

        if result > 0:

            print(
                f"{column}: INVALID"
            )

        else:

            print(
                f"{column}: OK"
            )


# ============================================================
# RECORD COUNT
# ============================================================

def get_record_count(file_path):

    return con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{file_path.as_posix()}')
        """
    ).fetchone()[0]


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("PHARMACY DATA QUALITY VALIDATION")
    print("=" * 80)

    yearly_counts = {}

    for year in YEARS:

        file_path = processed_file(year)

        print("\n" + "=" * 80)
        print(f"PROCESSING YEAR: {year}")
        print("=" * 80)

        if not file_path.exists():

            print(
                f"Processed file not found: {file_path}"
            )

            continue

        # ----------------------------------------------------
        # Schema
        # ----------------------------------------------------

        schema_valid = validate_schema(
            year,
            file_path
        )

        # ----------------------------------------------------
        # Record count
        # ----------------------------------------------------

        count = get_record_count(
            file_path
        )

        yearly_counts[year] = count

        print(
            f"\nRecord count: {count:,}"
        )

        # ----------------------------------------------------
        # Missing values
        # ----------------------------------------------------

        validate_missing_values(
            year,
            file_path
        )

        # ----------------------------------------------------
        # Negative values
        # ----------------------------------------------------

        validate_negative_values(
            year,
            file_path
        )

        # ----------------------------------------------------
        # Basic values
        # ----------------------------------------------------

        validate_basic_values(
            year,
            file_path
        )

    # ========================================================
    # HISTORICAL RECORD COUNT
    # ========================================================

    print("\n" + "=" * 80)
    print("HISTORICAL RECORD COUNT")
    print("=" * 80)

    for year, count in yearly_counts.items():

        print(
            f"{year}: {count:,} records"
        )

    con.close()

    print("\n" + "=" * 80)
    print("PHARMACY VALIDATION COMPLETED")
    print("=" * 80)