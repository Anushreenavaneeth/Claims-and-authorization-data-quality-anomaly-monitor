import duckdb
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FEATURE_DIR = PROJECT_ROOT / "data" / "features"
BEHAVIOR_DIR = PROJECT_ROOT / "data" / "behavior"

BEHAVIOR_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# AVAILABLE YEARS
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
# DUCKDB
# ============================================================

con = duckdb.connect()


# ============================================================
# HELPER
# ============================================================

def feature_file(year):

    return (
        FEATURE_DIR
        / f"pharmacy_{year}_features.parquet"
    )


# ============================================================
# CREATE BEHAVIOR FEATURES
# ============================================================

def create_behavior_features(
    current_year,
    previous_year
):

    print("\n" + "=" * 80)
    print(
        f"PHARMACY BEHAVIOR - "
        f"{previous_year} → {current_year}"
    )
    print("=" * 80)

    current_file = feature_file(
        current_year
    )

    previous_file = feature_file(
        previous_year
    )

    if not current_file.exists():

        print(
            f"Current feature file not found:\n"
            f"{current_file}"
        )

        return False

    if not previous_file.exists():

        print(
            f"Previous feature file not found:\n"
            f"{previous_file}"
        )

        return False

    output_file = (
        BEHAVIOR_DIR
        / f"pharmacy_{current_year}_behavior.parquet"
    )

    print("\nCurrent year:")
    print(current_file)

    print("\nPrevious year:")
    print(previous_file)

    print("\nOutput:")
    print(output_file)


    # ========================================================
    # BEHAVIOR QUERY
    # ========================================================

    query = f"""

    COPY (

        SELECT

            ------------------------------------------------
            -- CURRENT RECORD IDENTIFICATION
            ------------------------------------------------

            c.Prscrbr_NPI,
            c.Prscrbr_Last_Org_Name,
            c.Prscrbr_First_Name,
            c.Prscrbr_City,
            c.Prscrbr_State_Abrvtn,
            c.Prscrbr_Type,
            c.Brnd_Name,
            c.Gnrc_Name,

            c.data_year,


            ------------------------------------------------
            -- CURRENT VALUES
            ------------------------------------------------

            c.Tot_Clms,
            c.Tot_30day_Fills,
            c.Tot_Day_Suply,
            c.Tot_Drug_Cst,
            c.Tot_Benes,

            c.fills_per_claim,
            c.days_supply_per_claim,
            c.drug_cost_per_claim,
            c.drug_cost_per_beneficiary,
            c.claims_per_beneficiary,
            c.fills_per_beneficiary,
            c.days_supply_per_beneficiary,
            c.drug_cost_per_fill,


            ------------------------------------------------
            -- PREVIOUS VALUES
            ------------------------------------------------

            p.Tot_Clms AS previous_Tot_Clms,

            p.Tot_30day_Fills
                AS previous_Tot_30day_Fills,

            p.Tot_Day_Suply
                AS previous_Tot_Day_Suply,

            p.Tot_Drug_Cst
                AS previous_Tot_Drug_Cst,

            p.Tot_Benes
                AS previous_Tot_Benes,

            p.fills_per_claim
                AS previous_fills_per_claim,

            p.days_supply_per_claim
                AS previous_days_supply_per_claim,

            p.drug_cost_per_claim
                AS previous_drug_cost_per_claim,

            p.drug_cost_per_beneficiary
                AS previous_drug_cost_per_beneficiary,


            ------------------------------------------------
            -- CLAIM VOLUME CHANGE %
            ------------------------------------------------

            CASE

                WHEN p.Tot_Clms > 0

                THEN
                    (
                        c.Tot_Clms
                        - p.Tot_Clms
                    )
                    / p.Tot_Clms

                ELSE NULL

            END AS claim_volume_change,


            ------------------------------------------------
            -- FILL VOLUME CHANGE %
            ------------------------------------------------

            CASE

                WHEN p.Tot_30day_Fills > 0

                THEN
                    (
                        c.Tot_30day_Fills
                        - p.Tot_30day_Fills
                    )
                    / p.Tot_30day_Fills

                ELSE NULL

            END AS fill_volume_change,


            ------------------------------------------------
            -- DAYS SUPPLY CHANGE %
            ------------------------------------------------

            CASE

                WHEN p.Tot_Day_Suply > 0

                THEN
                    (
                        c.Tot_Day_Suply
                        - p.Tot_Day_Suply
                    )
                    / p.Tot_Day_Suply

                ELSE NULL

            END AS days_supply_change,


            ------------------------------------------------
            -- DRUG COST CHANGE %
            ------------------------------------------------

            CASE

                WHEN p.Tot_Drug_Cst > 0

                THEN
                    (
                        c.Tot_Drug_Cst
                        - p.Tot_Drug_Cst
                    )
                    / p.Tot_Drug_Cst

                ELSE NULL

            END AS drug_cost_change,


            ------------------------------------------------
            -- BENEFICIARY CHANGE %
            ------------------------------------------------

            CASE

                WHEN p.Tot_Benes > 0

                THEN
                    (
                        c.Tot_Benes
                        - p.Tot_Benes
                    )
                    / p.Tot_Benes

                ELSE NULL

            END AS beneficiary_change,


            ------------------------------------------------
            -- COST PER CLAIM CHANGE %
            ------------------------------------------------

            CASE

                WHEN p.drug_cost_per_claim > 0

                THEN
                    (
                        c.drug_cost_per_claim
                        - p.drug_cost_per_claim
                    )
                    / p.drug_cost_per_claim

                ELSE NULL

            END AS cost_per_claim_change,


            ------------------------------------------------
            -- FILLS PER CLAIM CHANGE %
            ------------------------------------------------

            CASE

                WHEN p.fills_per_claim > 0

                THEN
                    (
                        c.fills_per_claim
                        - p.fills_per_claim
                    )
                    / p.fills_per_claim

                ELSE NULL

            END AS fills_per_claim_change,


            ------------------------------------------------
            -- DAYS SUPPLY PER CLAIM CHANGE %
            ------------------------------------------------

            CASE

                WHEN p.days_supply_per_claim > 0

                THEN
                    (
                        c.days_supply_per_claim
                        - p.days_supply_per_claim
                    )
                    / p.days_supply_per_claim

                ELSE NULL

            END AS days_supply_per_claim_change,


            ------------------------------------------------
            -- PREVIOUS YEAR AVAILABILITY
            ------------------------------------------------

            CASE
                WHEN p.Prscrbr_NPI IS NULL
                THEN TRUE
                ELSE FALSE
            END AS new_pharmacy_record,


            ------------------------------------------------
            -- PREVIOUS RECORD EXISTS
            ------------------------------------------------

            CASE
                WHEN p.Prscrbr_NPI IS NOT NULL
                THEN TRUE
                ELSE FALSE
            END AS previous_year_record_exists


        FROM read_parquet(
            '{current_file.as_posix()}'
        ) c

        LEFT JOIN read_parquet(
            '{previous_file.as_posix()}'
        ) p

        ON
            c.Prscrbr_NPI = p.Prscrbr_NPI
            AND c.Brnd_Name = p.Brnd_Name
            AND c.Gnrc_Name = p.Gnrc_Name

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
            "\nCreating historical behavior features..."
        )

        con.execute(query)

    except Exception as error:

        print(
            "\nERROR DURING BEHAVIOR FEATURE ENGINEERING:"
        )

        print(error)

        return False


    # ========================================================
    # VERIFY
    # ========================================================

    print(
        "\nVerifying behavior dataset..."
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
        f"Behavior records: {result:,}"
    )

    print(
        f"\nSUCCESS: "
        f"{current_year} behavior features created."
    )

    return True


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("PHARMACY HISTORICAL BEHAVIOR FEATURE ENGINEERING")
    print("=" * 80)

    successful = 0
    failed = 0

    # --------------------------------------------------------
    # 2019 is the baseline year
    # --------------------------------------------------------

    print("\n2019 is the historical baseline.")
    print(
        "No previous-year comparison is created for 2019."
    )


    # --------------------------------------------------------
    # Compare each available year with previous available year
    # --------------------------------------------------------

    for index in range(1, len(YEARS)):

        previous_year = YEARS[index - 1]
        current_year = YEARS[index]

        result = create_behavior_features(
            current_year,
            previous_year
        )

        if result:
            successful += 1
        else:
            failed += 1


    con.close()


    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 80)
    print("BEHAVIOR FEATURE ENGINEERING SUMMARY")
    print("=" * 80)

    print(
        f"Successful comparisons : {successful}"
    )

    print(
        f"Failed comparisons     : {failed}"
    )

    print("\nBehavior directory:")
    print(BEHAVIOR_DIR)

    print("=" * 80)
    