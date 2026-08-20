from decimal import Decimal
import duckdb
import json
import math
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DECISION_DIR = PROJECT_ROOT / "data" / "decisions"
SLA_DIR = PROJECT_ROOT / "data" / "sla"

OUTPUT_DIR = PROJECT_ROOT / "data" / "final_output"

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
# CONFIGURATION
# ============================================================

BATCH_SIZE = 50_000


# ============================================================
# DUCKDB
# ============================================================

con = duckdb.connect()


# ============================================================
# CLEAN JSON VALUES
# ============================================================

def clean(value):

    # --------------------------------------------------------
    # NULL
    # --------------------------------------------------------

    if value is None:
        return None

    # --------------------------------------------------------
    # Decimal
    # --------------------------------------------------------

    if isinstance(value, Decimal):

        if not value.is_finite():
            return None

        # Convert Decimal to float for JSON
        return float(value)

    # --------------------------------------------------------
    # NumPy / pandas scalar
    # --------------------------------------------------------

    try:

        if hasattr(value, "item"):
            value = value.item()

    except Exception:
        pass

    # --------------------------------------------------------
    # Floating point NaN / Infinity
    # --------------------------------------------------------

    if isinstance(value, float):

        if math.isnan(value):
            return None

        if math.isinf(value):
            return None

    # --------------------------------------------------------
    # JSON primitive
    # --------------------------------------------------------

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool
        )
    ):
        return value

    # --------------------------------------------------------
    # Final fallback
    # --------------------------------------------------------

    return str(value)


# ============================================================
# CREATE ONE JSON RECORD
# ============================================================

def create_json_record(row):

    return {

        "dataset_type": "pharmacy",

        "record_id": clean(
            row["Prscrbr_NPI"]
        ),

        "detection_summary": {

            "final_anomaly": bool(
                row["final_anomaly"]
            ),

            "final_severity": clean(
                row["final_severity"]
            ),

            "final_risk_score": clean(
                row["final_risk_score"]
            ),

            "rule_anomaly": bool(
                row["rule_anomaly"]
            ),

            "ml_anomaly": bool(
                row["ml_anomaly"]
            ),

            "behavior_anomaly": bool(
                row["behavior_anomaly"]
            )
        },

        "rule_based_evidence": {

            "rule_anomaly": bool(
                row["rule_anomaly"]
            ),

            "severity": clean(
                row["rule_severity"]
            ),

            "reason": clean(
                row["rule_reason"]
            )
        },

        "ml_based_evidence": {

            "model": "Isolation Forest",

            "is_anomaly": bool(
                row["ml_anomaly"]
            ),

            "anomaly_score": clean(
                row["ml_anomaly_score"]
            )
        },

        "behavior_based_evidence": {

            "claim_volume_change": clean(
                row["claim_volume_change"]
            ),

            "fill_volume_change": clean(
                row["fill_volume_change"]
            ),

            "days_supply_change": clean(
                row["days_supply_change"]
            ),

            "drug_cost_change": clean(
                row["drug_cost_change"]
            ),

            "beneficiary_change": clean(
                row["beneficiary_change"]
            ),

            "cost_per_claim_change": clean(
                row["cost_per_claim_change"]
            )
        },

        "record_context": {

            "data_year": clean(
                row["data_year"]
            ),

            "Prscrbr_NPI": clean(
                row["Prscrbr_NPI"]
            ),

            "Prscrbr_Type": clean(
                row["Prscrbr_Type"]
            ),

            "Prscrbr_State_Abrvtn": clean(
                row["Prscrbr_State_Abrvtn"]
            ),

            "Brnd_Name": clean(
                row["Brnd_Name"]
            ),

            "Gnrc_Name": clean(
                row["Gnrc_Name"]
            ),

            "Tot_Clms": clean(
                row["Tot_Clms"]
            ),

            "Tot_30day_Fills": clean(
                row["Tot_30day_Fills"]
            ),

            "Tot_Day_Suply": clean(
                row["Tot_Day_Suply"]
            ),

            "Tot_Drug_Cst": clean(
                row["Tot_Drug_Cst"]
            ),

            "Tot_Benes": clean(
                row["Tot_Benes"]
            )
        },

        "sla": {

            "status": clean(
                row["sla_status"]
            ),

            "breach_probability": clean(
                row["sla_breach_probability"]
            ),

            "workload_risk": clean(
                row["workload_risk"]
            ),

            "volume_risk": clean(
                row["volume_risk"]
            ),

            "ml_risk": clean(
                row["ml_risk"]
            ),

            "quality_risk": clean(
                row["quality_risk"]
            )
        },

        "explanation": {

            "detection_source": clean(
                row["detection_source"]
            ),

            "reason": clean(
                row["explanation"]
            )
        }
    }


# ============================================================
# GENERATE JSON FOR ONE YEAR
# ============================================================

def generate_json(year):

    print("\n" + "=" * 80)
    print(
        f"GENERATING FINAL PHARMACY JSON - {year}"
    )
    print("=" * 80)

    decision_file = (
        DECISION_DIR
        / f"pharmacy_{year}_decisions.parquet"
    )

    sla_file = (
        SLA_DIR
        / f"pharmacy_{year}_sla.parquet"
    )

    output_file = (
        OUTPUT_DIR
        / f"pharmacy_{year}_anomalies.json"
    )

    if not decision_file.exists():

        print(
            f"Decision file missing:\n"
            f"{decision_file}"
        )

        return False

    if not sla_file.exists():

        print(
            f"SLA file missing:\n"
            f"{sla_file}"
        )

        return False

    print("\nDecision input:")
    print(decision_file)

    print("\nSLA input:")
    print(sla_file)

    print("\nCounting final records...")

    # ========================================================
    # COUNT
    # ========================================================

    count_query = f"""

        SELECT COUNT(*)

        FROM read_parquet(
            '{decision_file.as_posix()}'
        ) d

        INNER JOIN read_parquet(
            '{sla_file.as_posix()}'
        ) s

        ON
            d.Prscrbr_NPI = s.Prscrbr_NPI

            AND d.Brnd_Name = s.Brnd_Name

            AND d.Gnrc_Name = s.Gnrc_Name

            AND d.data_year = s.data_year

        WHERE
            d.final_anomaly = TRUE
            OR s.sla_status IN ('MAYBE', 'NO')

    """

    total_records = con.execute(
        count_query
    ).fetchone()[0]

    print(
        f"Final JSON records: "
        f"{total_records:,}"
    )

    # ========================================================
    # QUERY
    # ========================================================

    query = f"""

        SELECT

            d.*,

            s.sla_breach_probability,
            s.sla_status,
            s.workload_risk,
            s.volume_risk,
            s.ml_risk,
            s.quality_risk

        FROM read_parquet(
            '{decision_file.as_posix()}'
        ) d

        INNER JOIN read_parquet(
            '{sla_file.as_posix()}'
        ) s

        ON
            d.Prscrbr_NPI = s.Prscrbr_NPI

            AND d.Brnd_Name = s.Brnd_Name

            AND d.Gnrc_Name = s.Gnrc_Name

            AND d.data_year = s.data_year

        WHERE
            d.final_anomaly = TRUE
            OR s.sla_status IN ('MAYBE', 'NO')

    """

    # ========================================================
    # STREAM RESULTS
    # ========================================================

    cursor = con.execute(query)

    print("\nWriting JSON incrementally...")

    processed = 0

    # Write to temporary file first.
    # This prevents an incomplete file from being treated
    # as the final result if something fails.

    temporary_file = output_file.with_suffix(
        ".json.tmp"
    )

    try:

        with open(
            temporary_file,
            "w",
            encoding="utf-8"
        ) as file:

            file.write("[\n")

            first_record = True

            while True:

                rows = cursor.fetchmany(
                    BATCH_SIZE
                )

                if not rows:
                    break

                column_names = [
                    description[0]
                    for description in cursor.description
                ]

                for values in rows:

                    row = dict(
                        zip(
                            column_names,
                            values
                        )
                    )

                    record = create_json_record(
                        row
                    )

                    if not first_record:

                        file.write(",\n")

                    json.dump(
                        record,
                        file,
                        indent=2,
                        ensure_ascii=False,
                        allow_nan=False
                    )

                    first_record = False

                    processed += 1

                print(
                    f"Written: "
                    f"{processed:,} / "
                    f"{total_records:,}"
                )

            file.write("\n]\n")

        # ====================================================
        # ATOMIC FINALIZE
        # ====================================================

        temporary_file.replace(
            output_file
        )

    except Exception as error:

        print(
            "\nERROR WHILE GENERATING JSON:"
        )

        print(error)

        if temporary_file.exists():
            temporary_file.unlink()

        return False

    # ========================================================
    # VERIFY JSON
    # ========================================================

    print(
        "\nVerifying JSON file..."
    )

    try:

        with open(
            output_file,
            "r",
            encoding="utf-8"
        ) as file:

            json.load(file)

    except Exception as error:

        print(
            "\nJSON verification failed:"
        )

        print(error)

        return False

    print(
        "\nJSON verification: SUCCESS"
    )

    print(
        f"Records written: "
        f"{processed:,}"
    )

    print(
        "\nOutput:"
    )

    print(output_file)

    print(
        f"\nSUCCESS: "
        f"{year} final JSON created."
    )

    return True


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("PHARMACY FINAL JSON GENERATOR")
    print("=" * 80)

    successful = 0
    failed = 0

    for year in YEARS:

        result = generate_json(year)

        if result:
            successful += 1
        else:
            failed += 1

    con.close()

    print("\n" + "=" * 80)
    print("FINAL JSON GENERATION COMPLETED")
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
        "\nFinal output directory:"
    )

    print(OUTPUT_DIR)

    print("=" * 80)