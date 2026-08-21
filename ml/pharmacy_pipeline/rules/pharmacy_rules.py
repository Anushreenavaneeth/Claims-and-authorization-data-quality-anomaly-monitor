import duckdb
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

BEHAVIOR_DIR = PROJECT_ROOT / "data" / "behavior"
OUTPUT_DIR = PROJECT_ROOT / "data" / "rule_results"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# AVAILABLE YEARS
# 2020 TEMPORARILY EXCLUDED
# ============================================================

YEARS = [
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
# PROCESS ONE YEAR
# ============================================================

def run_rules(year):

    print("\n" + "=" * 80)
    print(f"PHARMACY RULE-BASED ANOMALY DETECTION - {year}")
    print("=" * 80)

    input_file = (
        BEHAVIOR_DIR
        / f"pharmacy_{year}_behavior.parquet"
    )

    output_file = (
        OUTPUT_DIR
        / f"pharmacy_{year}_rule_results.parquet"
    )

    if not input_file.exists():

        print(
            f"Input file not found:\n"
            f"{input_file}"
        )

        return False

    print("\nInput:")
    print(input_file)

    print("\nOutput:")
    print(output_file)

    # ========================================================
    # RULES
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
            Prscrbr_Type,
            Brnd_Name,
            Gnrc_Name,
            data_year,


            ------------------------------------------------
            -- ORIGINAL PHARMACY VALUES
            ------------------------------------------------

            Tot_Clms,
            Tot_30day_Fills,
            Tot_Day_Suply,
            Tot_Drug_Cst,
            Tot_Benes,


            ------------------------------------------------
            -- BEHAVIOR FEATURES
            ------------------------------------------------

            claim_volume_change,
            fill_volume_change,
            days_supply_change,
            drug_cost_change,
            beneficiary_change,
            cost_per_claim_change,


            ------------------------------------------------
            -- RULE FLAGS
            ------------------------------------------------

            CASE

                WHEN Tot_Clms < 0
                THEN TRUE

                ELSE FALSE

            END AS rule_negative_claims,


            CASE

                WHEN Tot_30day_Fills < 0
                THEN TRUE

                ELSE FALSE

            END AS rule_negative_fills,


            CASE

                WHEN Tot_Day_Suply < 0
                THEN TRUE

                ELSE FALSE

            END AS rule_negative_day_supply,


            CASE

                WHEN Tot_Drug_Cst < 0
                THEN TRUE

                ELSE FALSE

            END AS rule_negative_drug_cost,


            CASE

                WHEN Tot_Benes < 0
                THEN TRUE

                ELSE FALSE

            END AS rule_negative_beneficiaries,


            ------------------------------------------------
            -- FILLS SHOULD NOT BE NEGATIVE
            -- AND normally should not be below zero
            ------------------------------------------------

            CASE

                WHEN
                    Tot_30day_Fills IS NOT NULL
                    AND Tot_Clms IS NOT NULL
                    AND Tot_30day_Fills < 0
                THEN TRUE

                ELSE FALSE

            END AS rule_invalid_fill_value,


            ------------------------------------------------
            -- DAYS SUPPLY CONSISTENCY
            ------------------------------------------------

            CASE

                WHEN
                    Tot_Day_Suply IS NOT NULL
                    AND Tot_Clms IS NOT NULL
                    AND Tot_Day_Suply < 0
                THEN TRUE

                ELSE FALSE

            END AS rule_invalid_supply_value,


            ------------------------------------------------
            -- COST CONSISTENCY
            ------------------------------------------------

            CASE

                WHEN
                    Tot_Drug_Cst IS NOT NULL
                    AND Tot_Clms IS NOT NULL
                    AND Tot_Drug_Cst < 0
                THEN TRUE

                ELSE FALSE

            END AS rule_invalid_cost_value,


            ------------------------------------------------
            -- BENEFICIARY CONSISTENCY
            ------------------------------------------------

            CASE

                WHEN
                    Tot_Benes IS NOT NULL
                    AND Tot_Benes < 0
                THEN TRUE

                ELSE FALSE

            END AS rule_invalid_beneficiary_value,


            ------------------------------------------------
            -- EXTREME CLAIM VOLUME CHANGE
            -- > 300% increase/decrease
            ------------------------------------------------

            CASE

                WHEN
                    claim_volume_change IS NOT NULL
                    AND ABS(claim_volume_change) > 3
                THEN TRUE

                ELSE FALSE

            END AS rule_extreme_claim_volume_change,


            ------------------------------------------------
            -- EXTREME DRUG COST CHANGE
            ------------------------------------------------

            CASE

                WHEN
                    drug_cost_change IS NOT NULL
                    AND ABS(drug_cost_change) > 3
                THEN TRUE

                ELSE FALSE

            END AS rule_extreme_drug_cost_change,


            ------------------------------------------------
            -- EXTREME BENEFICIARY CHANGE
            ------------------------------------------------

            CASE

                WHEN
                    beneficiary_change IS NOT NULL
                    AND ABS(beneficiary_change) > 3
                THEN TRUE

                ELSE FALSE

            END AS rule_extreme_beneficiary_change,


            ------------------------------------------------
            -- EXTREME SUPPLY CHANGE
            ------------------------------------------------

            CASE

                WHEN
                    days_supply_change IS NOT NULL
                    AND ABS(days_supply_change) > 3
                THEN TRUE

                ELSE FALSE

            END AS rule_extreme_supply_change,


            ------------------------------------------------
            -- EXTREME FILL CHANGE
            ------------------------------------------------

            CASE

                WHEN
                    fill_volume_change IS NOT NULL
                    AND ABS(fill_volume_change) > 3
                THEN TRUE

                ELSE FALSE

            END AS rule_extreme_fill_change,


            ------------------------------------------------
            -- FINAL RULE ANOMALY
            ------------------------------------------------

            (
                COALESCE(Tot_Clms < 0, FALSE)

                OR

                COALESCE(
                    Tot_30day_Fills < 0,
                    FALSE
                )

                OR

                COALESCE(
                    Tot_Day_Suply < 0,
                    FALSE
                )

                OR

                COALESCE(
                    Tot_Drug_Cst < 0,
                    FALSE
                )

                OR

                COALESCE(
                    Tot_Benes < 0,
                    FALSE
                )

                OR

                COALESCE(
                    ABS(claim_volume_change) > 3,
                    FALSE
                )

                OR

                COALESCE(
                    ABS(drug_cost_change) > 3,
                    FALSE
                )

                OR

                COALESCE(
                    ABS(beneficiary_change) > 3,
                    FALSE
                )

                OR

                COALESCE(
                    ABS(days_supply_change) > 3,
                    FALSE
                )

                OR

                COALESCE(
                    ABS(fill_volume_change) > 3,
                    FALSE
                )
            ) AS rule_anomaly,


            ------------------------------------------------
            -- RULE SEVERITY
            ------------------------------------------------

            CASE

                WHEN
                    Tot_Clms < 0
                    OR Tot_30day_Fills < 0
                    OR Tot_Day_Suply < 0
                    OR Tot_Drug_Cst < 0
                    OR Tot_Benes < 0

                THEN 'HIGH'


                WHEN
                    ABS(claim_volume_change) > 3
                    OR ABS(drug_cost_change) > 3
                    OR ABS(beneficiary_change) > 3
                    OR ABS(days_supply_change) > 3
                    OR ABS(fill_volume_change) > 3

                THEN 'MEDIUM'


                ELSE 'NORMAL'

            END AS rule_severity,


            ------------------------------------------------
            -- RULE REASON
            ------------------------------------------------

            CONCAT_WS(
                '; ',

                CASE
                    WHEN Tot_Clms < 0
                    THEN 'Negative claim count'
                END,

                CASE
                    WHEN Tot_30day_Fills < 0
                    THEN 'Negative 30-day fill count'
                END,

                CASE
                    WHEN Tot_Day_Suply < 0
                    THEN 'Negative day supply'
                END,

                CASE
                    WHEN Tot_Drug_Cst < 0
                    THEN 'Negative drug cost'
                END,

                CASE
                    WHEN Tot_Benes < 0
                    THEN 'Negative beneficiary count'
                END,

                CASE
                    WHEN ABS(claim_volume_change) > 3
                    THEN 'Extreme year-over-year claim volume change'
                END,

                CASE
                    WHEN ABS(drug_cost_change) > 3
                    THEN 'Extreme year-over-year drug cost change'
                END,

                CASE
                    WHEN ABS(beneficiary_change) > 3
                    THEN 'Extreme year-over-year beneficiary change'
                END,

                CASE
                    WHEN ABS(days_supply_change) > 3
                    THEN 'Extreme year-over-year day supply change'
                END,

                CASE
                    WHEN ABS(fill_volume_change) > 3
                    THEN 'Extreme year-over-year fill volume change'
                END

            ) AS rule_reason


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
            "\nRunning Pharmacy validation rules..."
        )

        con.execute(query)

    except Exception as error:

        print(
            "\nERROR DURING RULE DETECTION:"
        )

        print(error)

        return False


    # ========================================================
    # SUMMARY
    # ========================================================

    total = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet(
            '{output_file.as_posix()}'
        )
        """
    ).fetchone()[0]

    anomalies = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet(
            '{output_file.as_posix()}'
        )
        WHERE rule_anomaly = TRUE
        """
    ).fetchone()[0]

    print(
        f"\nTotal records : {total:,}"
    )

    print(
        f"Rule anomalies: {anomalies:,}"
    )

    if total > 0:

        print(
            f"Anomaly rate  : "
            f"{(anomalies / total) * 100:.2f}%"
        )

    print(
        "\nRule severity:"
    )

    severity = con.execute(
        f"""
        SELECT
            rule_severity,
            COUNT(*) AS count
        FROM read_parquet(
            '{output_file.as_posix()}'
        )
        GROUP BY rule_severity
        ORDER BY count DESC
        """
    ).fetchdf()

    print(
        severity.to_string(
            index=False
        )
    )

    print(
        "\nOutput:"
    )

    print(output_file)

    print(
        f"\nSUCCESS: "
        f"{year} rule detection completed."
    )

    return True


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("PHARMACY RULE-BASED ANOMALY DETECTION")
    print("=" * 80)

    successful = 0
    failed = 0

    for year in YEARS:

        result = run_rules(year)

        if result:
            successful += 1
        else:
            failed += 1

    con.close()

    print("\n" + "=" * 80)
    print("RULE DETECTION SUMMARY")
    print("=" * 80)

    print(
        f"Successful datasets : {successful}"
    )

    print(
        f"Failed datasets     : {failed}"
    )

    print(
        "\nRule result directory:"
    )

    print(OUTPUT_DIR)

    print("=" * 80)