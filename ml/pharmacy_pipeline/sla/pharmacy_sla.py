import duckdb
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DECISION_DIR = PROJECT_ROOT / "data" / "decisions"
OUTPUT_DIR = PROJECT_ROOT / "data" / "sla"

OUTPUT_DIR.mkdir(
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
# SLA RISK FUNCTION
# ============================================================

def run_sla(year):

    print("\n" + "=" * 80)
    print(f"PHARMACY SLA RISK ANALYSIS - {year}")
    print("=" * 80)

    input_file = (
        DECISION_DIR
        / f"pharmacy_{year}_decisions.parquet"
    )

    output_file = (
        OUTPUT_DIR
        / f"pharmacy_{year}_sla.parquet"
    )

    if not input_file.exists():

        print(
            f"Input file not found:\n{input_file}"
        )

        return False

    print("\nInput:")
    print(input_file)

    print("\nOutput:")
    print(output_file)

    # ========================================================
    # SLA RISK
    #
    # This is a workload/behavior-based prototype.
    #
    # It does NOT claim to predict real processing time because
    # the current dataset has no actual processing-time/SLA label.
    # ========================================================

    query = f"""

    COPY (

        SELECT

            *,
            

            ------------------------------------------------
            -- WORKLOAD RISK
            ------------------------------------------------

            CASE

                WHEN
                    Tot_Clms >= 100000

                THEN 0.30

                WHEN
                    Tot_Clms >= 50000

                THEN 0.20

                WHEN
                    Tot_Clms >= 10000

                THEN 0.10

                ELSE 0.0

            END AS workload_risk,


            ------------------------------------------------
            -- VOLUME CHANGE RISK
            ------------------------------------------------

            CASE

                WHEN
                    ABS(
                        COALESCE(
                            claim_volume_change,
                            0
                        )
                    ) >= 3

                THEN 0.30

                WHEN
                    ABS(
                        COALESCE(
                            claim_volume_change,
                            0
                        )
                    ) >= 2

                THEN 0.20

                WHEN
                    ABS(
                        COALESCE(
                            claim_volume_change,
                            0
                        )
                    ) >= 1

                THEN 0.10

                ELSE 0.0

            END AS volume_risk,


            ------------------------------------------------
            -- ML RISK
            ------------------------------------------------

            CASE

                WHEN ml_anomaly = TRUE
                THEN 0.25

                ELSE 0.0

            END AS ml_risk,


            ------------------------------------------------
            -- DATA QUALITY / RULE RISK
            ------------------------------------------------

            CASE

                WHEN rule_anomaly = TRUE
                THEN 0.15

                ELSE 0.0

            END AS quality_risk,


            ------------------------------------------------
            -- FINAL SLA SCORE
            ------------------------------------------------

            LEAST(

                1.0,

                (
                    CASE
                        WHEN Tot_Clms >= 100000
                        THEN 0.30

                        WHEN Tot_Clms >= 50000
                        THEN 0.20

                        WHEN Tot_Clms >= 10000
                        THEN 0.10

                        ELSE 0.0
                    END

                    +

                    CASE
                        WHEN
                            ABS(
                                COALESCE(
                                    claim_volume_change,
                                    0
                                )
                            ) >= 3
                        THEN 0.30

                        WHEN
                            ABS(
                                COALESCE(
                                    claim_volume_change,
                                    0
                                )
                            ) >= 2
                        THEN 0.20

                        WHEN
                            ABS(
                                COALESCE(
                                    claim_volume_change,
                                    0
                                )
                            ) >= 1
                        THEN 0.10

                        ELSE 0.0
                    END

                    +

                    CASE
                        WHEN ml_anomaly = TRUE
                        THEN 0.25
                        ELSE 0.0
                    END

                    +

                    CASE
                        WHEN rule_anomaly = TRUE
                        THEN 0.15
                        ELSE 0.0
                    END
                )

            ) AS sla_breach_probability,


            ------------------------------------------------
            -- SLA STATUS
            ------------------------------------------------

            CASE

                WHEN

                    LEAST(
                        1.0,

                        (
                            CASE
                                WHEN Tot_Clms >= 100000
                                THEN 0.30

                                WHEN Tot_Clms >= 50000
                                THEN 0.20

                                WHEN Tot_Clms >= 10000
                                THEN 0.10

                                ELSE 0.0
                            END

                            +

                            CASE
                                WHEN
                                    ABS(
                                        COALESCE(
                                            claim_volume_change,
                                            0
                                        )
                                    ) >= 3
                                THEN 0.30

                                WHEN
                                    ABS(
                                        COALESCE(
                                            claim_volume_change,
                                            0
                                        )
                                    ) >= 2
                                THEN 0.20

                                WHEN
                                    ABS(
                                        COALESCE(
                                            claim_volume_change,
                                            0
                                        )
                                    ) >= 1
                                THEN 0.10

                                ELSE 0.0
                            END

                            +

                            CASE
                                WHEN ml_anomaly = TRUE
                                THEN 0.25
                                ELSE 0.0
                            END

                            +

                            CASE
                                WHEN rule_anomaly = TRUE
                                THEN 0.15
                                ELSE 0.0
                            END
                        )
                    ) >= 0.70

                THEN 'NO'


                WHEN

                    LEAST(
                        1.0,

                        (
                            CASE
                                WHEN Tot_Clms >= 100000
                                THEN 0.30

                                WHEN Tot_Clms >= 50000
                                THEN 0.20

                                WHEN Tot_Clms >= 10000
                                THEN 0.10

                                ELSE 0.0
                            END

                            +

                            CASE
                                WHEN
                                    ABS(
                                        COALESCE(
                                            claim_volume_change,
                                            0
                                        )
                                    ) >= 3
                                THEN 0.30

                                WHEN
                                    ABS(
                                        COALESCE(
                                            claim_volume_change,
                                            0
                                        )
                                    ) >= 2
                                THEN 0.20

                                WHEN
                                    ABS(
                                        COALESCE(
                                            claim_volume_change,
                                            0
                                        )
                                    ) >= 1
                                THEN 0.10

                                ELSE 0.0
                            END

                            +

                            CASE
                                WHEN ml_anomaly = TRUE
                                THEN 0.25
                                ELSE 0.0
                            END

                            +

                            CASE
                                WHEN rule_anomaly = TRUE
                                THEN 0.15
                                ELSE 0.0
                            END
                        )
                    ) >= 0.40

                THEN 'MAYBE'


                ELSE 'YES'

            END AS sla_status


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

    try:

        print(
            "\nCalculating SLA risk..."
        )

        con.execute(query)

    except Exception as error:

        print(
            "\nERROR DURING SLA ANALYSIS:"
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

    print(
        f"\nTotal records: {total:,}"
    )

    print("\nSLA distribution:")

    result = con.execute(
        f"""
        SELECT
            sla_status,
            COUNT(*) AS count
        FROM read_parquet(
            '{output_file.as_posix()}'
        )
        GROUP BY sla_status
        ORDER BY
            CASE sla_status
                WHEN 'NO' THEN 1
                WHEN 'MAYBE' THEN 2
                WHEN 'YES' THEN 3
            END
        """
    ).fetchdf()

    print(
        result.to_string(
            index=False
        )
    )

    print(
        "\nOutput:"
    )

    print(output_file)

    print(
        f"\nSUCCESS: "
        f"{year} SLA analysis completed."
    )

    return True


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("PHARMACY SLA RISK PIPELINE")
    print("=" * 80)

    successful = 0
    failed = 0

    for year in YEARS:

        result = run_sla(year)

        if result:
            successful += 1
        else:
            failed += 1

    con.close()

    print("\n" + "=" * 80)
    print("SLA PIPELINE SUMMARY")
    print("=" * 80)

    print(
        f"Successful datasets : {successful}"
    )

    print(
        f"Failed datasets     : {failed}"
    )

    print(
        "\nSLA directory:"
    )

    print(OUTPUT_DIR)

    print("=" * 80)