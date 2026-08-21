from pathlib import Path
import pickle

import numpy as np
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
)


DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "authorization"
)


MODEL_DIR = (
    PROJECT_ROOT
    / "ml"
    / "authorization"
    / "auth pkl file"
)


# ============================================================
# INPUT / OUTPUT FILES
# ============================================================

INPUT_FILE = (
    DATA_DIR
    / "preprocessed_authorization_data.csv"
)


RESULT_FILE = (
    DATA_DIR
    / "authorization_anomaly_results.csv"
)


RAG_JSON_FILE = (
    PROJECT_ROOT
    / "ml"
    / "authorization"
    / "authorization.json"
)


PIPELINE_FILE = (
    MODEL_DIR
    / "authorization_anomaly_pipeline.pkl"
)


# ============================================================
# IMPORT MODULES
# ============================================================

from ml.authorization.preprocessing import (
    prepare_authorization_data
)


from ml.authorization.rule_engine import (
    train_rule_thresholds,
    run_rule_checks
)


from ml.authorization.isolation_forest_model import (
    train_isolation_forest,
    detect_ml_anomalies
)


from ml.authorization.bayesian_root_cause import (
    train_bayesian_model,
    get_bayesian_results
)


from ml.authorization.risk_scoring import (
    calculate_risk
)


from ml.authorization.output_formatter import (
    create_complete_json,
    save_json_output,
    CAUSE_DESCRIPTIONS
)


# ============================================================
# TRAIN COMPLETE PIPELINE
# ============================================================

def train_pipeline(
    df
):

    # --------------------------------------------------------
    # STEP 1: PREPROCESSING
    # --------------------------------------------------------

    print(
        "\nSTEP 1: PREPROCESSING"
    )


    prepared_data = prepare_authorization_data(
        df,
        training=True
    )


    preprocessing_artifacts = prepared_data[
        "preprocessing_artifacts"
    ]


    # --------------------------------------------------------
    # STEP 2: TRAIN RULE THRESHOLDS
    # --------------------------------------------------------

    print(
        "STEP 2: TRAINING RULE THRESHOLDS"
    )


    rule_thresholds = train_rule_thresholds(
        prepared_data
    )


    # --------------------------------------------------------
    # STEP 3: RULE ENGINE
    # --------------------------------------------------------

    print(
        "STEP 3: RUNNING RULE ENGINE"
    )


    conditions = run_rule_checks(
        prepared_data,
        rule_thresholds
    )


    # --------------------------------------------------------
    # STEP 4: ISOLATION FOREST
    # --------------------------------------------------------

    print(
        "STEP 4: TRAINING ISOLATION FOREST"
    )


    isolation_artifacts = train_isolation_forest(
        prepared_data["ml_df"],
        contamination=0.05,
        n_estimators=300,
        random_state=42
    )


    ml_results = detect_ml_anomalies(
        prepared_data["ml_df"],
        isolation_artifacts
    )


    conditions[
        "ml_anomaly_flag"
    ] = ml_results[
        "ml_anomaly_flag"
    ]


    conditions[
        "ml_anomaly_score"
    ] = ml_results[
        "ml_anomaly_score"
    ]


    conditions[
        "ml_anomaly_severity"
    ] = ml_results[
        "ml_anomaly_severity"
    ]


    # --------------------------------------------------------
    # STEP 5: FINAL ANOMALY FLAG
    # --------------------------------------------------------

    print(
        "STEP 5: COMBINING RULE + ML RESULTS"
    )


    conditions[
        "final_anomaly_flag"
    ] = np.where(
        (
            conditions[
                "rule_anomaly_flag"
            ] == 1
        )
        |
        (
            conditions[
                "ml_anomaly_flag"
            ] == 1
        ),
        1,
        0
    )


    # --------------------------------------------------------
    # STEP 6: BAYESIAN MODEL
    # --------------------------------------------------------

    print(
        "STEP 6: TRAINING BAYESIAN MODEL"
    )


    bayesian_artifacts = train_bayesian_model(
        conditions
    )


    # --------------------------------------------------------
    # STEP 7: BAYESIAN RESULTS
    # --------------------------------------------------------

    print(
        "STEP 7: BAYESIAN ROOT CAUSE ANALYSIS"
    )


    bayesian_results = get_bayesian_results(
        conditions,
        bayesian_artifacts,
        top_n=3
    )


    conditions[
        "bayesian_anomaly_probability"
    ] = [
        item["anomaly_probability"]
        for item in bayesian_results
    ]


    conditions[
        "bayesian_root_causes"
    ] = [
        item["probable_root_causes"]
        for item in bayesian_results
    ]


    conditions[
        "bayesian_anomaly_flag"
    ] = (
        conditions[
            "bayesian_anomaly_probability"
        ]
        >= 0.50
    ).astype(int)


    # --------------------------------------------------------
    # STEP 8: RISK SCORING
    # --------------------------------------------------------

    print(
        "STEP 8: CALCULATING RISK SCORE"
    )


    conditions = calculate_risk(
        conditions
    )


    # --------------------------------------------------------
    # PIPELINE ARTIFACTS
    # --------------------------------------------------------

    pipeline_artifacts = {

        "preprocessing_artifacts":
            preprocessing_artifacts,

        "rule_thresholds":
            rule_thresholds,

        "isolation_artifacts":
            isolation_artifacts,

        "bayesian_artifacts":
            bayesian_artifacts,

        "cause_descriptions":
            CAUSE_DESCRIPTIONS
    }


    return (
        pipeline_artifacts,
        prepared_data,
        conditions
    )


# ============================================================
# SAVE PIPELINE
# ============================================================

def save_pipeline(
    pipeline_artifacts,
    path=PIPELINE_FILE
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    with open(
        path,
        "wb"
    ) as f:

        pickle.dump(
            pipeline_artifacts,
            f
        )


    print(
        f"\nPipeline saved successfully:\n{path}"
    )


# ============================================================
# LOAD PIPELINE
# ============================================================

def load_pipeline(
    path=PIPELINE_FILE
):

    with open(
        path,
        "rb"
    ) as f:

        pipeline_artifacts = pickle.load(
            f
        )


    return pipeline_artifacts


# ============================================================
# RUN INFERENCE ON NEW DATA
# ============================================================

def run_inference(
    df,
    pipeline_artifacts
):

    # --------------------------------------------------------
    # PREPROCESS
    # --------------------------------------------------------

    prepared_data = prepare_authorization_data(
        df,
        training=False,
        preprocessing_artifacts=
            pipeline_artifacts[
                "preprocessing_artifacts"
            ]
    )


    # --------------------------------------------------------
    # RULE ENGINE
    # --------------------------------------------------------

    conditions = run_rule_checks(
        prepared_data,
        pipeline_artifacts[
            "rule_thresholds"
        ]
    )


    # --------------------------------------------------------
    # ISOLATION FOREST
    # --------------------------------------------------------

    ml_results = detect_ml_anomalies(
        prepared_data[
            "ml_df"
        ],
        pipeline_artifacts[
            "isolation_artifacts"
        ]
    )


    conditions[
        "ml_anomaly_flag"
    ] = ml_results[
        "ml_anomaly_flag"
    ]


    conditions[
        "ml_anomaly_score"
    ] = ml_results[
        "ml_anomaly_score"
    ]


    conditions[
        "ml_anomaly_severity"
    ] = ml_results[
        "ml_anomaly_severity"
    ]


    # --------------------------------------------------------
    # FINAL ANOMALY
    # --------------------------------------------------------

    conditions[
        "final_anomaly_flag"
    ] = np.where(
        (
            conditions[
                "rule_anomaly_flag"
            ] == 1
        )
        |
        (
            conditions[
                "ml_anomaly_flag"
            ] == 1
        ),
        1,
        0
    )


    # --------------------------------------------------------
    # BAYESIAN ANALYSIS
    # --------------------------------------------------------

    bayesian_results = get_bayesian_results(
        conditions,
        pipeline_artifacts[
            "bayesian_artifacts"
        ],
        top_n=3
    )


    conditions[
        "bayesian_anomaly_probability"
    ] = [
        item["anomaly_probability"]
        for item in bayesian_results
    ]


    conditions[
        "bayesian_root_causes"
    ] = [
        item["probable_root_causes"]
        for item in bayesian_results
    ]


    conditions[
        "bayesian_anomaly_flag"
    ] = (
        conditions[
            "bayesian_anomaly_probability"
        ]
        >= 0.50
    ).astype(int)


    # --------------------------------------------------------
    # RISK SCORE
    # --------------------------------------------------------

    conditions = calculate_risk(
        conditions
    )


    # --------------------------------------------------------
    # FINAL CSV DATAFRAME
    # --------------------------------------------------------

    final_df = pd.concat(
        [

            prepared_data[
                "df_original"
            ],

            prepared_data[
                "features"
            ].add_prefix(
                "feature_"
            ),

            conditions

        ],
        axis=1
    )


    # --------------------------------------------------------
    # FINAL JSON
    # --------------------------------------------------------

    json_output = create_complete_json(
        conditions,
        prepared_data[
            "df_original"
        ]
    )


    return (
        final_df,
        json_output
    )


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():

    print("\n" + "=" * 70)

    print(
        "AUTHORIZATION ANOMALY DETECTION PIPELINE"
    )

    print("=" * 70)


    # --------------------------------------------------------
    # CREATE FOLDERS
    # --------------------------------------------------------

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    RAG_JSON_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    # --------------------------------------------------------
    # CHECK INPUT FILE
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"\nInput file not found:\n"
            f"{INPUT_FILE}\n\n"
            "Check the filename in pipeline.py."
        )


    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    print(
        "\nLoading authorization data..."
    )


    df = pd.read_csv(
        INPUT_FILE
    )


    print(
        "Dataset shape:",
        df.shape
    )


    print(
        "Columns:"
    )


    print(
        df.columns.tolist()
    )


    # --------------------------------------------------------
    # TRAIN PIPELINE
    # --------------------------------------------------------

    (
        pipeline_artifacts,
        prepared_data,
        conditions
    ) = train_pipeline(
        df
    )


    # --------------------------------------------------------
    # SAVE PKL
    # --------------------------------------------------------

    save_pipeline(
        pipeline_artifacts
    )


    # --------------------------------------------------------
    # CREATE FINAL DATAFRAME
    # --------------------------------------------------------

    final_df = pd.concat(
        [

            prepared_data[
                "df_original"
            ],

            prepared_data[
                "features"
            ].add_prefix(
                "feature_"
            ),

            conditions

        ],
        axis=1
    )


    # --------------------------------------------------------
    # SAVE CSV RESULTS
    # --------------------------------------------------------

    final_df.to_csv(
        RESULT_FILE,
        index=False
    )


    print(
        f"\nResults CSV saved:\n{RESULT_FILE}"
    )


    # --------------------------------------------------------
    # CREATE COMPLETE JSON
    # --------------------------------------------------------

    json_output = create_complete_json(
        conditions,
        prepared_data[
            "df_original"
        ]
    )


    # --------------------------------------------------------
    # SAVE JSON
    # --------------------------------------------------------

    save_json_output(
        json_output,
        RAG_JSON_FILE
    )


    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)

    print(
        "PIPELINE COMPLETED SUCCESSFULLY"
    )

    print("=" * 70)


    print(
        "\nTOTAL RECORDS:",
        len(final_df)
    )


    print(
        "RULE ANOMALIES:",
        int(
            conditions[
                "rule_anomaly_flag"
            ].sum()
        )
    )


    print(
        "ML ANOMALIES:",
        int(
            conditions[
                "ml_anomaly_flag"
            ].sum()
        )
    )


    print(
        "BAYESIAN HIGH-PROBABILITY:",
        int(
            conditions[
                "bayesian_anomaly_flag"
            ].sum()
        )
    )


    print(
        "FINAL ANOMALIES:",
        int(
            conditions[
                "final_anomaly_flag"
            ].sum()
        )
    )


    print(
        "\nRISK DISTRIBUTION:"
    )


    print(
        conditions[
            "risk_level"
        ].value_counts()
    )


    print(
        "\nOUTPUTS:"
    )


    print(
        "Results CSV:"
    )

    print(
        RESULT_FILE
    )


    print(
        "\nRAG JSON:"
    )

    print(
        RAG_JSON_FILE
    )


    print(
        "\nPipeline PKL:"
    )

    print(
        PIPELINE_FILE
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()