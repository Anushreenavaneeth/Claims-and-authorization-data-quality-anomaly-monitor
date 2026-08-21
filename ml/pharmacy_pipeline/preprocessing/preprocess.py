import duckdb
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# INPUT DATASETS
# ============================================================

DATASETS = {
    2019: RAW_DATA_DIR / "data_2019.csv",
    2020: RAW_DATA_DIR / "data_2020.csv",
    2021: RAW_DATA_DIR / "data_2021.csv",
    2022: RAW_DATA_DIR / "data_2022.csv",
    2023: RAW_DATA_DIR / "data_2023.csv",
    2024: RAW_DATA_DIR / "data_2024.csv",
}


# ============================================================
# PHARMACY NUMERIC COLUMNS
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
# PHARMACY IDENTIFICATION COLUMNS
# ============================================================

PHARMACY_INDICATORS = {
    "Prscrbr_NPI",
    "Brnd_Name",
    "Gnrc_Name",
    "Tot_Clms",
    "Tot_30day_Fills",
    "Tot_Day_Suply",
    "Tot_Drug_Cst",
    "Tot_Benes",
}


# ============================================================
# DUCKDB CONNECTION
# ============================================================

con = duckdb.connect()


# ============================================================
# GET DATASET COLUMNS
# ============================================================

def get_columns(file_path):

    schema = con.execute(
        f"""
        DESCRIBE
        SELECT *
        FROM read_csv_auto(
            '{file_path.as_posix()}'
        )
        """
    ).fetchdf()

    return schema["column_name"].tolist()


# ============================================================
# SOURCE IDENTIFICATION
# ============================================================

def identify_pharmacy(columns):

    matched = PHARMACY_INDICATORS.intersection(
        set(columns)
    )

    return len(matched) >= 6


# ============================================================
# PROCESS ONE DATASET
# ============================================================

def preprocess_dataset(year, input_file):

    print("\n" + "=" * 80)
    print(f"PREPROCESSING PHARMACY DATA - {year}")
    print("=" * 80)

    # --------------------------------------------------------
    # Check input
    # --------------------------------------------------------

    if not input_file.exists():

        print(
            f"ERROR: Input file not found:\n"
            f"{input_file}"
        )

        return False

    print(f"\nInput file:")
    print(input_file)

    # --------------------------------------------------------
    # Read schema only
    # --------------------------------------------------------

    columns = get_columns(input_file)

    print(
        f"\nColumns detected: {len(columns)}"
    )

    # --------------------------------------------------------
    # Pharmacy identification
    # --------------------------------------------------------

    if not identify_pharmacy(columns):

        print(
            "\nERROR: File does not match "
            "Pharmacy schema."
        )

        return False

    print(
        "Source identified: PHARMACY"
    )

    # --------------------------------------------------------
    # Numeric columns actually present
    # --------------------------------------------------------

    numeric_columns = [
        column
        for column in NUMERIC_COLUMNS
        if column in columns
    ]

    print(
        f"\nNumeric Pharmacy columns found: "
        f"{len(numeric_columns)}"
    )

    # --------------------------------------------------------
    # Build SELECT expressions
    # --------------------------------------------------------

    select_expressions = []

    for column in columns:

        quoted_column = f'"{column}"'

        if column in numeric_columns:

            # Convert numeric fields safely.
            #
            # Invalid numeric strings become NULL.
            #
            # We do NOT replace NULL with zero here.

            expression = f"""
                TRY_CAST(
                    NULLIF(
                        TRIM(
                            CAST(
                                {quoted_column}
                                AS VARCHAR
                            )
                        ),
                        ''
                    )
                    AS DOUBLE
                ) AS {quoted_column}
            """

        else:

            expression = quoted_column

        select_expressions.append(
            expression
        )

    select_sql = ",\n".join(
        select_expressions
    )

    # --------------------------------------------------------
    # Add year
    # --------------------------------------------------------

    select_sql += f",\n{year} AS data_year"

    # --------------------------------------------------------
    # Output file
    # --------------------------------------------------------

    output_file = (
        PROCESSED_DIR
        / f"pharmacy_{year}_processed.parquet"
    )

    print(
        f"\nOutput file:"
    )

    print(output_file)

    # --------------------------------------------------------
    # Process CSV → Parquet
    # --------------------------------------------------------

    print(
        "\nProcessing large CSV file..."
    )

    query = f"""
        COPY (
            SELECT
                {select_sql}

            FROM read_csv_auto(
                '{input_file.as_posix()}',
                header = true,
                ignore_errors = false
            )
        )
        TO '{output_file.as_posix()}'
        (
            FORMAT PARQUET,
            COMPRESSION ZSTD
        );
    """

    try:

        con.execute(query)

    except Exception as error:

        print(
            "\nERROR DURING PREPROCESSING:"
        )

        print(error)

        return False

    # --------------------------------------------------------
    # Verify output
    # --------------------------------------------------------

    print(
        "\nVerifying processed file..."
    )

    processed_count = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet(
            '{output_file.as_posix()}'
        )
        """
    ).fetchone()[0]

    print(
        f"Processed records: "
        f"{processed_count:,}"
    )

    print(
        f"\nSUCCESS: {year} preprocessing completed."
    )

    return True


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    preprocess_dataset(
        2020,
        DATASETS[2020]
    )