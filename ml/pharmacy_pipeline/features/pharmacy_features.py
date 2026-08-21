import duckdb
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FEATURE_DIR = PROJECT_ROOT / "data" / "features"

FEATURE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# YEARS AVAILABLE
# 2020 TEMPORARILY EXCLUDED
# ============================================================

YEARS = [
    2019,
    2021,
    2022,
    2023,
    2024
]


# ============================================================
# DUCKDB CONNECTION
# ============================================================

con = duckdb.connect()


# ============================================================
# CREATE FEATURES FOR ONE YEAR
# ============================================================

def create_features(year):

    print("\n" + "=" * 80)
    print(f"PHARMACY FEATURE ENGINEERING - {year}")
    print("=" * 80)

    input_file = (
        PROCESSED_DIR
        / f"pharmacy_{year}_processed.parquet"
    )

    output_file = (
        FEATURE_DIR
        / f"pharmacy_{year}_features.parquet"
    )

    # --------------------------------------------------------
    # Check input
    # --------------------------------------------------------

    if not input_file.exists():

        print(
            f"INPUT FILE NOT FOUND:\n"
            f"{input_file}"
        )

        return False

    print("\nInput:")
    print(input_file)

    print("\nOutput:")
    print(output_file)

    # ========================================================
    # FEATURE ENGINEERING
    # ========================================================

    query = f"""

    COPY (

        SELECT

            ------------------------------------------------
            -- IDENTIFICATION
            ------------------------------------------------

            Prscrbr_NPI,
            Prscrbr_Last_Org_Name,
            Prscrbr_First_Name,
            Prscrbr_City,
            Prscrbr_State_Abrvtn,
            Prscrbr_State_FIPS,
            Prscrbr_Type,
            Brnd_Name,
            Gnrc_Name,

            data_year,


            ------------------------------------------------
            -- ORIGINAL PHARMACY METRICS
            ------------------------------------------------

            Tot_Clms,
            Tot_30day_Fills,
            Tot_Day_Suply,
            Tot_Drug_Cst,
            Tot_Benes,


            ------------------------------------------------
            -- FEATURE 1
            -- Fills per claim
            ------------------------------------------------

            CASE
                WHEN Tot_Clms > 0
                THEN Tot_30day_Fills / Tot_Clms
                ELSE NULL
            END AS fills_per_claim,


            ------------------------------------------------
            -- FEATURE 2
            -- Days supply per claim
            ------------------------------------------------

            CASE
                WHEN Tot_Clms > 0
                THEN Tot_Day_Suply / Tot_Clms
                ELSE NULL
            END AS days_supply_per_claim,


            ------------------------------------------------
            -- FEATURE 3
            -- Drug cost per claim
            ------------------------------------------------

            CASE
                WHEN Tot_Clms > 0
                THEN Tot_Drug_Cst / Tot_Clms
                ELSE NULL
            END AS drug_cost_per_claim,


            ------------------------------------------------
            -- FEATURE 4
            -- Drug cost per beneficiary
            ------------------------------------------------

            CASE
                WHEN Tot_Benes > 0
                THEN Tot_Drug_Cst / Tot_Benes
                ELSE NULL
            END AS drug_cost_per_beneficiary,


            ------------------------------------------------
            -- FEATURE 5
            -- Claims per beneficiary
            ------------------------------------------------

            CASE
                WHEN Tot_Benes > 0
                THEN Tot_Clms / Tot_Benes
                ELSE NULL
            END AS claims_per_beneficiary,


            ------------------------------------------------
            -- FEATURE 6
            -- Fills per beneficiary
            ------------------------------------------------

            CASE
                WHEN Tot_Benes > 0
                THEN Tot_30day_Fills / Tot_Benes
                ELSE NULL
            END AS fills_per_beneficiary,


            ------------------------------------------------
            -- FEATURE 7
            -- Days supply per beneficiary
            ------------------------------------------------

            CASE
                WHEN Tot_Benes > 0
                THEN Tot_Day_Suply / Tot_Benes
                ELSE NULL
            END AS days_supply_per_beneficiary,


            ------------------------------------------------
            -- FEATURE 8
            -- Average cost per fill
            ------------------------------------------------

            CASE
                WHEN Tot_30day_Fills > 0
                THEN Tot_Drug_Cst / Tot_30day_Fills
                ELSE NULL
            END AS drug_cost_per_fill,


            ------------------------------------------------
            -- FEATURE 9
            -- Cost intensity
            ------------------------------------------------

            CASE
                WHEN Tot_Clms > 0
                THEN Tot_Drug_Cst / Tot_Clms
                ELSE NULL
            END AS cost_intensity,


            ------------------------------------------------
            -- FEATURE 10
            -- Fill intensity
            ------------------------------------------------

            CASE
                WHEN Tot_Clms > 0
                THEN Tot_30day_Fills / Tot_Clms
                ELSE NULL
            END AS fill_intensity,


            ------------------------------------------------
            -- FEATURE 11
            -- Days supply intensity
            ------------------------------------------------

            CASE
                WHEN Tot_Clms > 0
                THEN Tot_Day_Suply / Tot_Clms
                ELSE NULL
            END AS supply_intensity


        FROM read_parquet(
            '{input_file.as_posix()}'
        )

    )

    TO '{output_file.as_posix()}'

    (
        FORMAT PARQUET,
        COMPRESSION ZSTD
    );

    """

    # ========================================================
    # EXECUTE
    # ========================================================

    try:

        print(
            "\nCreating Pharmacy features..."
        )

        con.execute(query)

    except Exception as error:

        print(
            "\nERROR DURING FEATURE ENGINEERING:"
        )

        print(error)

        return False


    # ========================================================
    # VERIFY
    # ========================================================

    print(
        "\nVerifying feature dataset..."
    )

    result = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet(
            '{output_file.as_posix()}'
        )
        """
    ).fetchone()[0]

    print(
        f"Feature records: {result:,}"
    )

    print(
        f"\nSUCCESS: {year} features created."
    )

    return True


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("PHARMACY FEATURE ENGINEERING")
    print("=" * 80)

    successful = 0
    failed = 0

    for year in YEARS:

        result = create_features(year)

        if result:
            successful += 1
        else:
            failed += 1


    con.close()


    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 80)
    print("FEATURE ENGINEERING SUMMARY")
    print("=" * 80)

    print(
        f"Successful datasets : {successful}"
    )

    print(
        f"Failed datasets     : {failed}"
    )

    print("\nFeature directory:")
    print(FEATURE_DIR)

    print("=" * 80)