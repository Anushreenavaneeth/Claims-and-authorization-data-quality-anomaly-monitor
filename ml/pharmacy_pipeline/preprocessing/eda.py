import duckdb
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

DATASETS = {
    2019: RAW_DATA_DIR / "data_2019.csv",
    2020: RAW_DATA_DIR / "data_2020.csv",
    2021: RAW_DATA_DIR / "data_2021.csv",
    2022: RAW_DATA_DIR / "data_2022.csv",
    2023: RAW_DATA_DIR / "data_2023.csv",
    2024: RAW_DATA_DIR / "data_2024.csv",
}


# ============================================================
# DUCKDB
# ============================================================

con = duckdb.connect()


# ============================================================
# BASIC DATASET EDA
# ============================================================

def run_eda(year, file_path):

    print("\n" + "=" * 80)
    print(f"PHARMACY EDA - {year}")
    print("=" * 80)

    if not file_path.exists():
        print(f"FILE NOT FOUND: {file_path}")
        return

    file = file_path.as_posix()

    # --------------------------------------------------------
    # 1. ROW COUNT
    # --------------------------------------------------------

    row_count = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{file}')
        """
    ).fetchone()[0]

    print(f"\nTotal records: {row_count:,}")

    # --------------------------------------------------------
    # 2. COLUMN INFORMATION
    # --------------------------------------------------------

    schema = con.execute(
        f"""
        DESCRIBE
        SELECT *
        FROM read_csv_auto('{file}')
        """
    ).fetchdf()

    print(f"Total columns: {len(schema)}")

    print("\nColumn information:")
    print(schema[["column_name", "column_type"]].to_string(index=False))

    # --------------------------------------------------------
    # 3. NULL / MISSING VALUE ANALYSIS
    # --------------------------------------------------------

    print("\n" + "-" * 80)
    print("MISSING VALUE ANALYSIS")
    print("-" * 80)

    null_query = f"""
        SELECT
            COUNT(*) AS total_rows,

            {", ".join(
                [
                    f'COUNT(*) - COUNT("{col}") AS "{col}"'
                    for col in schema["column_name"]
                ]
            )}

        FROM read_csv_auto('{file}')
    """

    null_result = con.execute(null_query).fetchdf()

    total_rows = null_result.iloc[0]["total_rows"]

    null_counts = []

    for column in schema["column_name"]:

        count = null_result.iloc[0][column]

        if count > 0:

            percentage = (
                count / total_rows * 100
                if total_rows > 0
                else 0
            )

            null_counts.append(
                (column, int(count), percentage)
            )

    if null_counts:

        print(
            f"{'Column':35} "
            f"{'Null Count':15} "
            f"{'Null %':10}"
        )

        for column, count, percentage in sorted(
            null_counts,
            key=lambda x: x[1],
            reverse=True
        ):

            print(
                f"{column:35} "
                f"{count:<15,} "
                f"{percentage:>8.2f}%"
            )

    else:
        print("No NULL values found.")
        # --------------------------------------------------------
    # 4. DUPLICATE ANALYSIS
    # --------------------------------------------------------

    print("\n" + "-" * 80)
    print("DUPLICATE ANALYSIS")
    print("-" * 80)

    print(
        "Exact duplicate analysis will be performed "
        "after the dataset grain is confirmed."
        )

    print(
    "Status: SKIPPED during initial EDA"
    )

    

    # --------------------------------------------------------
    # 5. NUMERIC COLUMN SUMMARY
    # --------------------------------------------------------

    print("\n" + "-" * 80)
    print("NUMERIC COLUMN SUMMARY")
    print("-" * 80)

    numeric_columns = schema[
        schema["column_type"].str.contains(
            "INT|DOUBLE|DECIMAL|FLOAT|BIGINT|HUGEINT",
            case=False,
            regex=True
        )
    ]["column_name"].tolist()

    if numeric_columns:

        for column in numeric_columns:

            result = con.execute(
                f"""
                SELECT
                    MIN("{column}") AS min_value,
                    MAX("{column}") AS max_value,
                    AVG("{column}") AS avg_value,
                    COUNT("{column}") AS non_null_count
                FROM read_csv_auto('{file}')
                """
            ).fetchone()

            print(
                f"\n{column}"
            )

            print(
                f"  Min       : {result[0]}"
            )

            print(
                f"  Max       : {result[1]}"
            )

            print(
                f"  Mean      : {result[2]}"
            )

            print(
                f"  Non-null  : {result[3]:,}"
            )

    # --------------------------------------------------------
    # 6. ZERO VALUE ANALYSIS
    # --------------------------------------------------------

    print("\n" + "-" * 80)
    print("ZERO VALUE ANALYSIS")
    print("-" * 80)

    for column in numeric_columns:

        zero_count = con.execute(
            f"""
            SELECT COUNT(*)
            FROM read_csv_auto('{file}')
            WHERE "{column}" = 0
            """
        ).fetchone()[0]

        if zero_count > 0:

            print(
                f"{column}: {zero_count:,} zero values"
            )

    # --------------------------------------------------------
    # 7. PHARMACY-SPECIFIC SUMMARY
    # --------------------------------------------------------

    pharmacy_columns = [
        "Tot_Clms",
        "Tot_30day_Fills",
        "Tot_Day_Suply",
        "Tot_Drug_Cst",
        "Tot_Benes",
    ]

    available = [
        column
        for column in pharmacy_columns
        if column in schema["column_name"].tolist()
    ]

    if available:

        print("\n" + "-" * 80)
        print("PHARMACY METRIC SUMMARY")
        print("-" * 80)

        for column in available:

            result = con.execute(
                f"""
                SELECT
                    SUM("{column}") AS total,
                    AVG("{column}") AS average,
                    MIN("{column}") AS minimum,
                    MAX("{column}") AS maximum
                FROM read_csv_auto('{file}')
                """
            ).fetchone()

            print(f"\n{column}")

            print(f"  Total : {result[0]}")
            print(f"  Mean  : {result[1]}")
            print(f"  Min   : {result[2]}")
            print(f"  Max   : {result[3]}")

    print("\nEDA completed for:", year)


# ============================================================
# RUN ALL YEARS
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("PHARMACY DATA - EXPLORATORY DATA ANALYSIS")
    print("=" * 80)

    for year, file_path in DATASETS.items():

        run_eda(
            year,
            file_path
        )

    con.close()

    print("\n" + "=" * 80)
    print("ALL PHARMACY EDA COMPLETED")
    print("=" * 80)