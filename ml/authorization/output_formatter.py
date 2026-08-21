import json
import pandas as pd
import numpy as np


# ============================================================
# ROOT CAUSE DESCRIPTIONS
# ============================================================

CAUSE_DESCRIPTIONS = {

    "missing_data":
        "One or more critical fields are missing",

    "invalid_date":
        "One or more date values have an invalid format",

    "future_request":
        "The request date is in the future",

    "approval_before_request":
        "The approval date occurs before the request date",

    "invalid_validity_range":
        "The validity end date occurs before the validity start date",

    "negative_quantity":
        "The requested quantity is negative",

    "negative_amount":
        "The charged amount is negative",

    "unusual_quantity":
        "The requested quantity is statistically unusual",

    "unusual_amount":
        "The charged amount is statistically unusual",

    "duplicate_record":
        "The record is duplicated"
}


ROOT_CAUSE_COLS = list(
    CAUSE_DESCRIPTIONS.keys()
)


# ============================================================
# SAFE VALUE
# ============================================================

def safe_value(value):

    # Handle None

    if value is None:
        return None


    # Handle NaN / NaT

    try:

        if pd.isna(value):
            return None

    except Exception:
        pass


    # Convert NumPy values

    if isinstance(
        value,
        (
            np.integer,
            np.int64
        )
    ):

        return int(value)


    if isinstance(
        value,
        (
            np.floating,
            np.float64
        )
    ):

        return float(value)


    if isinstance(
        value,
        np.bool_
    ):

        return bool(value)


    # Convert timestamps

    if isinstance(
        value,
        pd.Timestamp
    ):

        return value.isoformat()


    return value


# ============================================================
# RULE SEVERITY
# ============================================================

def get_rule_severity(
    rule_count
):

    if rule_count == 0:

        return "NONE"

    elif rule_count == 1:

        return "LOW"

    elif rule_count <= 3:

        return "MEDIUM"

    return "HIGH"


# ============================================================
# GET DETECTION SIGNALS
# ============================================================

def get_signals(
    row
):

    signals = []


    if row["rule_anomaly_flag"] == 1:

        signals.append(
            "Rule"
        )


    if row["ml_anomaly_flag"] == 1:

        signals.append(
            "ML"
        )


    if (
        row.get(
            "bayesian_anomaly_flag",
            0
        ) == 1
    ):

        signals.append(
            "Bayesian"
        )


    if len(signals) == 0:

        return "None"


    return ";".join(
        signals
    )


# ============================================================
# BUILD ML EVIDENCE
# ============================================================

def build_ml_evidence(
    row
):

    # --------------------------------------------------------
    # NO ML ANOMALY
    # --------------------------------------------------------

    if row["ml_anomaly_flag"] == 0:

        return {

            "evidence_count":
                0,

            "severity":
                "",

            "types":
                "",

            "features":
                "",

            "details":
                "",

            "summary":
                ""
        }


    # --------------------------------------------------------
    # GET BAYESIAN ROOT CAUSES
    # --------------------------------------------------------

    root_causes = row.get(
        "bayesian_root_causes",
        []
    )


    cause_names = []

    details = []


    for item in root_causes:

        cause = item.get(
            "cause",
            "unknown"
        )


        cause_names.append(
            cause
        )


        details.append(
            f"{cause}: "
            f"P(cause|anomaly)="
            f"{item.get('probability_given_anomaly', 0)}, "
            f"lift="
            f"{item.get('bayesian_lift', 0)}"
        )


    # --------------------------------------------------------
    # NO CONFIGURED CAUSE
    # --------------------------------------------------------

    if len(cause_names) == 0:

        feature_text = (
            "No configured rule cause identified"
        )

        detail_text = (
            "Isolation Forest detected an unusual "
            "combination of multiple feature values."
        )


    # --------------------------------------------------------
    # CAUSES AVAILABLE
    # --------------------------------------------------------

    else:

        feature_text = ";".join(
            cause_names
        )

        detail_text = "; ".join(
            details
        )


    return {

        "evidence_count":
            len(cause_names),

        "severity":
            row[
                "ml_anomaly_severity"
            ],

        "types":
            "MULTIVARIATE_ANOMALY",

        "features":
            feature_text,

        "details":
            detail_text,

        "summary":
            (
                "Isolation Forest detected an unusual "
                f"multivariate pattern with "
                f"{row['ml_anomaly_severity']} severity."
            )
    }


# ============================================================
# CREATE ONE RECORD JSON
# ============================================================

def create_record_json(
    index,
    row,
    df_original
):

    original = df_original.loc[
        index
    ]


    # --------------------------------------------------------
    # ACTIVE RULES
    # --------------------------------------------------------

    active_rules = []

    active_reasons = []


    for cause in ROOT_CAUSE_COLS:

        if row[cause] == "yes":

            active_rules.append(
                cause.upper()
            )

            active_reasons.append(
                CAUSE_DESCRIPTIONS[cause]
            )


    rule_count = len(
        active_rules
    )


    if rule_count == 0:

        rule_name = "NONE"

        reason = (
            "No rule violation detected"
        )

    else:

        rule_name = ";".join(
            active_rules
        )

        reason = ";".join(
            active_reasons
        )


    # --------------------------------------------------------
    # BAYESIAN VALUES
    # --------------------------------------------------------

    bayesian_probability = float(
        row.get(
            "bayesian_anomaly_probability",
            0.0
        )
    )


    BAYESIAN_THRESHOLD = 0.50


    bayesian_anomaly = (
        bayesian_probability
        >= BAYESIAN_THRESHOLD
    )


    bayesian_score = (
        bayesian_probability * 100
    )


    # --------------------------------------------------------
    # SIGNAL COUNT
    # --------------------------------------------------------

    signal_count = 0


    if row["rule_anomaly_flag"] == 1:

        signal_count += 1


    if row["ml_anomaly_flag"] == 1:

        signal_count += 1


    if bayesian_anomaly:

        signal_count += 1


    # --------------------------------------------------------
    # FINAL RECORD
    # --------------------------------------------------------

    record = {

        # ====================================================
        # RECORD ID
        # ====================================================

        "record_id": {

            "authorization_id":
                safe_value(
                    original.get(
                        "authorization_id"
                    )
                ),

            "reference_number":
                safe_value(
                    original.get(
                        "reference_number"
                    )
                )
        },


        # ====================================================
        # ENTITY
        # ====================================================

        "entity": {

            "patient_id":
                safe_value(
                    original.get(
                        "patient_id"
                    )
                ),

            "provider_id":
                safe_value(
                    original.get(
                        "provider_id"
                    )
                ),

            "payer_id":
                safe_value(
                    original.get(
                        "payer_id"
                    )
                ),

            "authorization_type":
                safe_value(
                    original.get(
                        "authorization_type"
                    )
                ),

            "service_code":
                safe_value(
                    original.get(
                        "service_code"
                    )
                ),

            "service_description":
                safe_value(
                    original.get(
                        "service_description"
                    )
                ),

            "approval_status":
                safe_value(
                    original.get(
                        "approval_status"
                    )
                )
        },


        # ====================================================
        # FINAL ASSESSMENT
        # ====================================================

        "final_assessment": {

            "anomaly":
                bool(
                    row[
                        "final_anomaly_flag"
                    ] == 1
                ),

            "severity":
                row[
                    "risk_level"
                ],

            "risk_score":
                int(
                    row[
                        "risk_score"
                    ]
                ),

            "signal_count":
                signal_count,

            "signals":
                get_signals(
                    row
                )
        },


        # ====================================================
        # BAYESIAN
        # ====================================================

        "bayesian": {

            "anomaly":
                bool(
                    bayesian_anomaly
                ),

            "score":
                round(
                    bayesian_score,
                    6
                ),

            "probability":
                round(
                    bayesian_probability,
                    6
                ),

            "threshold":
                BAYESIAN_THRESHOLD
        },


        # ====================================================
        # RULE ENGINE
        # ====================================================

        "rule_engine": {

            "anomaly":
                bool(
                    row[
                        "rule_anomaly_flag"
                    ] == 1
                ),

            "rule_count":
                int(
                    rule_count
                ),

            "rule_name":
                rule_name,

            "reason":
                reason,

            "severity":
                get_rule_severity(
                    rule_count
                )
        },


        # ====================================================
        # ML EVIDENCE
        # ====================================================

        "ml_evidence":
            build_ml_evidence(
                row
            )
    }


    return record


# ============================================================
# CREATE COMPLETE JSON
# ============================================================

def create_complete_json(
    conditions,
    df_original
):

    records = []


    for index, row in conditions.iterrows():

        record = create_record_json(
            index,
            row,
            df_original
        )

        records.append(
            record
        )


    output = {

        "project":
            (
                "Healthcare Data Operations Platform - "
                "Authorization Data Quality Anomaly Monitor"
            ),

        "schema_version":
            "1.0",

        "record_count":
            len(records),

        "records":
            records
    }


    return output


# ============================================================
# SAVE JSON
# ============================================================

def save_json_output(
    output,
    output_path
):

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=4,
            default=str
        )


    print(
        f"JSON saved successfully: {output_path}"
    )