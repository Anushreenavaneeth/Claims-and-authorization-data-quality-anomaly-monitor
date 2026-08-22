# run_pipeline.py

import json
import sys
import time
from pathlib import Path

import pandas as pd

from pipeline.anomaly_pipeline import (
    AnomalyPipeline,
    save_results,
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data" / "raw"

OUTPUT_DIR = BASE_DIR / "outputs"

OUTPUT_FILE = (
    OUTPUT_DIR
    / "anomaly_results.json"
)


# ============================================================
# DATASET PATHS
# ============================================================

# Historical dataset
HISTORICAL_DATASET = (
    DATA_DIR
    / "dataset_100k_2023.csv"
)

# Current dataset
CURRENT_DATASET = (
    DATA_DIR
    / "dataset_100k_2024.csv"
)


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset(
    file_path: Path,
    dataset_name: str,
) -> pd.DataFrame:

    print(
        f"\nLoading {dataset_name} dataset..."
    )

    if not file_path.exists():

        raise FileNotFoundError(
            f"{dataset_name} dataset not found:\n"
            f"{file_path}"
        )

    suffix = (
        file_path
        .suffix
        .lower()
    )

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    if suffix == ".csv":

        dataframe = pd.read_csv(
            file_path,
            low_memory=False,
        )

    # --------------------------------------------------------
    # EXCEL
    # --------------------------------------------------------

    elif suffix in {
        ".xlsx",
        ".xls",
    }:

        dataframe = pd.read_excel(
            file_path
        )

    else:

        raise ValueError(
            "Unsupported dataset format: "
            f"{suffix}"
        )

    if dataframe.empty:

        raise ValueError(
            f"{dataset_name} dataset is empty."
        )

    print(
        f"{dataset_name} dataset:",
        dataframe.shape,
    )

    return dataframe


# ============================================================
# VALIDATE DATASETS
# ============================================================

def validate_datasets(
    current_df: pd.DataFrame,
    historical_df: pd.DataFrame,
):

    print(
        "\n========== DATA VALIDATION =========="
    )

    if current_df.empty:

        raise ValueError(
            "Current dataset contains no records."
        )

    if historical_df.empty:

        raise ValueError(
            "Historical dataset contains no records."
        )

    print(
        "Current records:",
        len(current_df),
    )

    print(
        "Historical records:",
        len(historical_df),
    )

    print(
        "Current columns:",
        len(current_df.columns),
    )

    print(
        "Historical columns:",
        len(historical_df.columns),
    )

    # --------------------------------------------------------
    # Column comparison
    # --------------------------------------------------------

    current_columns = set(
        current_df.columns
    )

    historical_columns = set(
        historical_df.columns
    )

    common_columns = (
        current_columns
        & historical_columns
    )

    print(
        "Common columns:",
        len(common_columns),
    )

    if not common_columns:

        raise ValueError(
            "Current and historical datasets "
            "do not share any columns."
        )

    print(
        "Dataset validation completed."
    )


# ============================================================
# VERIFY OUTPUT
# ============================================================

def verify_output(
    output_path: Path,
):

    print(
        "\n========== OUTPUT VERIFICATION =========="
    )

    if not output_path.exists():

        raise FileNotFoundError(
            "Pipeline completed but output "
            "JSON was not created."
        )

    with open(
        output_path,
        "r",
        encoding="utf-8",
    ) as file:

        output_data = json.load(
            file
        )

    # --------------------------------------------------------
    # Required top-level structure
    # --------------------------------------------------------

    required_keys = {
        "project",
        "schema_version",
        "record_count",
        "records",
    }

    missing_keys = (
        required_keys
        - set(
            output_data.keys()
        )
    )

    if missing_keys:

        raise ValueError(
            "Output JSON is missing "
            f"required fields: {missing_keys}"
        )

    # --------------------------------------------------------
    # Validate records
    # --------------------------------------------------------

    records = output_data.get(
        "records",
        [],
    )

    if not isinstance(
        records,
        list,
    ):

        raise ValueError(
            "'records' must be a JSON array."
        )

    if (
        output_data.get(
            "record_count"
        )
        != len(records)
    ):

        raise ValueError(
            "record_count does not match "
            "the number of records."
        )

    # --------------------------------------------------------
    # Validate record structure
    # --------------------------------------------------------

    required_record_keys = {
        "record_id",
        "entity",
        "final_assessment",
        "bayesian",
        "rule_engine",
        "ml_evidence",
    }

    if records:

        sample_record = (
            records[0]
        )

        missing_record_keys = (
            required_record_keys
            - set(
                sample_record.keys()
            )
        )

        if missing_record_keys:

            raise ValueError(
                "Output record is missing "
                "required fields: "
                f"{missing_record_keys}"
            )

    print(
        "JSON structure: VALID"
    )

    print(
        "Records in JSON:",
        len(records),
    )

    return output_data


# ============================================================
# PRINT SUMMARY
# ============================================================

def print_summary(
    output_data,
):

    records = output_data.get(
        "records",
        [],
    )

    anomaly_count = sum(

        1

        for record in records

        if (
            record.get(
                "final_assessment",
                {}
            ).get(
                "anomaly",
                False,
            )
        )
    )

    normal_count = (
        len(records)
        - anomaly_count
    )

    print(
        "\n========== FINAL SUMMARY =========="
    )

    print(
        "Total output records:",
        len(records),
    )

    print(
        "Anomalies:",
        anomaly_count,
    )

    print(
        "Normal:",
        normal_count,
    )

    # --------------------------------------------------------
    # Sample anomaly
    # --------------------------------------------------------

    sample_anomaly = next(
        (
            record

            for record in records

            if (
                record.get(
                    "final_assessment",
                    {}
                ).get(
                    "anomaly",
                    False,
                )
            )
        ),
        None,
    )

    if sample_anomaly:

        print(
            "\n========== SAMPLE ANOMALY =========="
        )

        print(
            json.dumps(
                sample_anomaly,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        )


# ============================================================
# MAIN
# ============================================================

def main():

    overall_start = (
        time.time()
    )

    print(
        "\n=========================================="
    )

    print(
        " CTS V2 ANOMALY DETECTION PIPELINE"
    )

    print(
        "=========================================="
    )

    try:

        # ====================================================
        # 1. LOAD CURRENT DATA
        # ====================================================

        current_df = load_dataset(
            CURRENT_DATASET,
            "Current",
        )

        # ====================================================
        # 2. LOAD HISTORICAL DATA
        # ====================================================

        historical_df = load_dataset(
            HISTORICAL_DATASET,
            "Historical",
        )

        # ====================================================
        # 3. VALIDATE
        # ====================================================

        validate_datasets(
            current_df,
            historical_df,
        )

        # ====================================================
        # 4. CREATE PIPELINE
        # ====================================================

        print(
            "\n========== INITIALIZING PIPELINE =========="
        )

        pipeline = (
            AnomalyPipeline(
                current_df=current_df,
                historical_df=historical_df,
            )
        )

        print(
            "Pipeline initialized."
        )

        # ====================================================
        # 5. RUN COMPLETE PIPELINE
        # ====================================================

        results = (
            pipeline.run()
        )

        if results is None:

            raise RuntimeError(
                "Pipeline returned None."
            )

        if not isinstance(
            results,
            list,
        ):

            raise TypeError(
                "Pipeline output must be a list."
            )

        # ====================================================
        # 6. SAVE JSON
        # ====================================================

        print(
            "\n========== SAVING OUTPUT =========="
        )

        saved_path = (
            save_results(
                results,
                path=OUTPUT_FILE,
            )
        )

        # ====================================================
        # 7. VERIFY JSON
        # ====================================================

        output_data = (
            verify_output(
                Path(
                    saved_path
                )
            )
        )

        # ====================================================
        # 8. SUMMARY
        # ====================================================

        print_summary(
            output_data
        )

        # ====================================================
        # FINISHED
        # ====================================================

        elapsed = (
            time.time()
            - overall_start
        )

        print(
            "\n=========================================="
        )

        print(
            " END-TO-END PIPELINE COMPLETED"
        )

        print(
            "=========================================="
        )

        print(
            "Output:",
            saved_path,
        )

        print(
            "Total execution time:",
            round(
                elapsed,
                2,
            ),
            "seconds",
        )

        return 0

    except KeyboardInterrupt:

        print(
            "\nPipeline stopped by user."
        )

        return 130

    except Exception as error:

        print(
            "\n=========================================="
        )

        print(
            " PIPELINE FAILED"
        )

        print(
            "=========================================="
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        raise


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )

    