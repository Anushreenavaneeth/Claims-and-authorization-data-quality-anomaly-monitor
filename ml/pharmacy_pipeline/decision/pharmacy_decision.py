import duckdb
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RULE_DIR = PROJECT_ROOT / "data" / "rule_results"
ML_DIR = PROJECT_ROOT / "data" / "outputs"

DECISION_DIR = PROJECT_ROOT / "data" / "decisions"

DECISION_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# YEARS
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

def create_decision(year):

    print("\n" + "=" * 80)
    print(f"PHARMACY ANOMALY DECISION - {year}")
    print("=" * 80)

    rule_file = (
        RULE_DIR
        / f"pharmacy_{year}_rule_results.parquet"
    )

    ml_file = (
        ML_DIR
        / f"pharmacy_{year}_anomalies.parquet"
    )

    output_file = (
        DECISION_DIR
        / f"pharmacy_{year}_decisions.parquet"
    )

    # ========================================================
    # CHECK INPUTS
    # ========================================================

    print("\nRule input:")
    print(rule_file)

    print("\nML input:")
    print(ml_file)

    if not rule_file.exists():

        print(
            f"\nERROR: Rule result not found:\n"
            f"{rule_file}"
        )

        return False

    if not ml_file.exists():

        print(
            f"\nERROR: ML result not found:\n"
            f"{ml_file}"
        )

        return False

    # ========================================================
    # CREATE DECISION DATASET
    # ========================================================

    query = f"""

    COPY (

        SELECT

            ------------------------------------------------
            -- RECORD CONTEXT
            ------------------------------------------------

            r.Prscrbr_NPI,
            r.Prscrbr_Last_Org_Name,
            r.Prscrbr_First_Name,
            r.Prscrbr_City,
            r.Prscrbr_State_Abrvtn,
            r.Prscrbr_Type,
            r.Brnd_Name,
            r.Gnrc_Name,
            r.data_year,

            r.Tot_Clms,
            r.Tot_30day_Fills,
            r.Tot_Day_Suply,
            r.Tot_Drug_Cst,
            r.Tot_Benes,


            ------------------------------------------------
            -- RULE RESULTS
            ------------------------------------------------

            r.rule_anomaly,

            r.rule_severity,

            r.rule_reason,


            ------------------------------------------------
            -- ML RESULTS
            ------------------------------------------------

            m.ml_prediction,

            m.ml_anomaly,

            m.ml_anomaly_score,


            ------------------------------------------------
            -- BEHAVIOR RESULTS
            ------------------------------------------------

            r.claim_volume_change,

            r.fill_volume_change,

            r.days_supply_change,

            r.drug_cost_change,

            r.beneficiary_change,

            r.cost_per_claim_change,


            ------------------------------------------------
            -- BEHAVIOR ANOMALY
            ------------------------------------------------

            CASE

                WHEN
                    ABS(
                        COALESCE(
                            r.claim_volume_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.fill_volume_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.days_supply_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.drug_cost_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.beneficiary_change,
                            0
                        )
                    ) > 3

                THEN TRUE

                ELSE FALSE

            END AS behavior_anomaly,


            ------------------------------------------------
            -- RULE + ML + BEHAVIOR
            ------------------------------------------------

            (
                COALESCE(
                    r.rule_anomaly,
                    FALSE
                )

                OR

                COALESCE(
                    m.ml_anomaly,
                    FALSE
                )

                OR

                (
                    ABS(
                        COALESCE(
                            r.claim_volume_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.fill_volume_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.days_supply_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.drug_cost_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.beneficiary_change,
                            0
                        )
                    ) > 3
                )
            ) AS final_anomaly,


            ------------------------------------------------
            -- RISK SCORE
            --
            -- Rule       = 0.40
            -- ML         = 0.40
            -- Behavior   = 0.20
            ------------------------------------------------

            (
                CASE
                    WHEN r.rule_anomaly
                    THEN 0.40
                    ELSE 0.0
                END

                +

                CASE
                    WHEN m.ml_anomaly
                    THEN 0.40
                    ELSE 0.0
                END

                +

                CASE
                    WHEN
                        ABS(
                            COALESCE(
                                r.claim_volume_change,
                                0
                            )
                        ) > 3

                        OR

                        ABS(
                            COALESCE(
                                r.fill_volume_change,
                                0
                            )
                        ) > 3

                        OR

                        ABS(
                            COALESCE(
                                r.days_supply_change,
                                0
                            )
                        ) > 3

                        OR

                        ABS(
                            COALESCE(
                                r.drug_cost_change,
                                0
                            )
                        ) > 3

                        OR

                        ABS(
                            COALESCE(
                                r.beneficiary_change,
                                0
                            )
                        ) > 3

                    THEN 0.20

                    ELSE 0.0

                END
            ) AS final_risk_score,


            ------------------------------------------------
            -- FINAL SEVERITY
            ------------------------------------------------

            CASE

                WHEN
                    r.rule_anomaly
                    AND m.ml_anomaly
                THEN 'CRITICAL'


                WHEN
                    r.rule_anomaly
                    OR m.ml_anomaly
                THEN 'HIGH'


                WHEN

                    ABS(
                        COALESCE(
                            r.claim_volume_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.fill_volume_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.days_supply_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.drug_cost_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.beneficiary_change,
                            0
                        )
                    ) > 3

                THEN 'MEDIUM'


                ELSE 'NORMAL'

            END AS final_severity,


            ------------------------------------------------
            -- DETECTION SOURCE
            ------------------------------------------------

            CASE

                WHEN
                    r.rule_anomaly
                    AND m.ml_anomaly
                THEN 'RULE + ML'


                WHEN
                    r.rule_anomaly
                THEN 'RULE'


                WHEN
                    m.ml_anomaly
                THEN 'ML'


                WHEN

                    ABS(
                        COALESCE(
                            r.claim_volume_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.fill_volume_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.days_supply_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.drug_cost_change,
                            0
                        )
                    ) > 3

                    OR

                    ABS(
                        COALESCE(
                            r.beneficiary_change,
                            0
                        )
                    ) > 3

                THEN 'BEHAVIOR'


                ELSE 'NORMAL'

            END AS detection_source,


            ------------------------------------------------
            -- EXPLANATION
            ------------------------------------------------

            CONCAT_WS(
                '; ',

                CASE
                    WHEN r.rule_anomaly
                    THEN r.rule_reason
                END,

                CASE
                    WHEN m.ml_anomaly
                    THEN
                        'Isolation Forest identified unusual pharmacy behavior'
                END,

                CASE
                    WHEN
                        ABS(
                            COALESCE(
                                r.claim_volume_change,
                                0
                            )
                        ) > 3
                    THEN
                        'Extreme year-over-year claim volume change'
                END,

                CASE
                    WHEN
                        ABS(
                            COALESCE(
                                r.drug_cost_change,
                                0
                            )
                        ) > 3
                    THEN
                        'Extreme year-over-year drug cost change'
                END,

                CASE
                    WHEN
                        ABS(
                            COALESCE(
                                r.beneficiary_change,
                                0
                            )
                        ) > 3
                    THEN
                        'Extreme year-over-year beneficiary change'
                END

            ) AS explanation


        FROM read_parquet(
            '{rule_file.as_posix()}'
        ) r

        INNER JOIN read_parquet(
            '{ml_file.as_posix()}'
        ) m

        ON
            r.Prscrbr_NPI = m.Prscrbr_NPI

            AND

            r.Brnd_Name = m.Brnd_Name

            AND

            r.Gnrc_Name = m.Gnrc_Name

            AND

            r.data_year = m.data_year

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
            "\nCombining Rule + Behavior + ML..."
        )

        con.execute(query)

    except Exception as error:

        print(
            "\nERROR DURING DECISION ENGINE:"
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
        WHERE final_anomaly = TRUE
        """
    ).fetchone()[0]

    print(
        f"\nDecision records : {total:,}"
    )

    print(
        f"Final anomalies  : {anomalies:,}"
    )

    if total > 0:

        print(
            f"Anomaly rate     : "
            f"{(anomalies / total) * 100:.2f}%"
        )

    # ========================================================
    # SEVERITY
    # ========================================================

    print("\nSeverity distribution:")

    severity = con.execute(
        f"""
        SELECT
            final_severity,
            COUNT(*) AS count
        FROM read_parquet(
            '{output_file.as_posix()}'
        )
        GROUP BY final_severity
        ORDER BY count DESC
        """
    ).fetchdf()

    print(
        severity.to_string(
            index=False
        )
    )

    # ========================================================
    # DETECTION SOURCE
    # ========================================================

    print(
        "\nDetection source:"
    )

    source = con.execute(
        f"""
        SELECT
            detection_source,
            COUNT(*) AS count
        FROM read_parquet(
            '{output_file.as_posix()}'
        )
        GROUP BY detection_source
        ORDER BY count DESC
        """
    ).fetchdf()

    print(
        source.to_string(
            index=False
        )
    )

    print(
        "\nOutput:"
    )

    print(output_file)

    print(
        f"\nSUCCESS: "
        f"{year} decision dataset created."
    )

    return True


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("PHARMACY ANOMALY DECISION ENGINE")
    print("=" * 80)

    successful = 0
    failed = 0

    for year in YEARS:

        result = create_decision(year)

        if result:
            successful += 1
        else:
            failed += 1

    con.close()

    print("\n" + "=" * 80)
    print("DECISION ENGINE SUMMARY")
    print("=" * 80)

    print(
        f"Successful datasets : "
        f"{successful}"
    )

    print(
        f"Failed datasets     : "
        f"{failed}"
    )

    print(
        "\nDecision directory:"
    )

    print(
        DECISION_DIR
    )

    print("=" * 80)