"""
TC-PUF Claims Data
Robust Feature Engineering for Data Quality Anomaly Detection

Pipeline position:

    Raw Excel
        ↓
    Preprocessing
        ↓
    EDA
        ↓
    THIS FEATURE ENGINEERING
        ↓
    ML preprocessing / encoding / imputation
        ↓
    Isolation Forest
        ↓
    Rule-based validation / Soda
        ↓
    Root Cause Analysis / Bayesian Network
        ↓
    JSON output

Important:
- This script does NOT impute missing values.
- This script does NOT scale features.
- This script does NOT remove anomalies.
- Invalid ratios are NOT silently clipped.
- Invalid ratios are explicitly flagged.
"""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "tc_puf_cleaned.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "tc_puf_feature_engineered.csv"
)

INVALID_RATE_THRESHOLD = 1.0

warnings.filterwarnings(
    "ignore",
    message="DataFrame is highly fragmented"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def to_numeric(series):
    """
    Convert a series to numeric safely.

    Handles:
    - numbers
    - strings containing numbers
    - '*'
    - '**'
    - blank values
    - invalid strings

    Invalid/suppressed values become NaN.
    """
    return pd.to_numeric(series, errors="coerce")


def safe_ratio(
    numerator,
    denominator,
    feature_name,
    features,
    invalid_threshold=1.0
):
    """
    Create robust ratio features.

    Outputs:

        <feature_name>
        <feature_name>_Raw
        <feature_name>_Invalid_Flag
        <feature_name>_Missing_Flag

    Logic:

        denominator <= 0
            -> rate = NaN

        numerator > denominator
            -> raw ratio retained
            -> clean rate = NaN
            -> invalid flag = 1

        numerator <= denominator
            -> clean rate = numerator / denominator

    We NEVER clip invalid ratios because they can themselves
    represent a data-quality problem.
    """

    numerator = to_numeric(numerator)
    denominator = to_numeric(denominator)

    valid_denominator = denominator > 0

    raw_ratio = pd.Series(
        np.nan,
        index=numerator.index,
        dtype="float64"
    )

    raw_ratio.loc[valid_denominator] = (
        numerator.loc[valid_denominator]
        / denominator.loc[valid_denominator]
    )

    invalid_flag = (
        raw_ratio.notna()
        & (
            (raw_ratio < 0)
            | (raw_ratio > invalid_threshold)
        )
    ).astype("int8")

    clean_rate = raw_ratio.copy()

    clean_rate.loc[invalid_flag == 1] = np.nan

    missing_flag = (
        numerator.isna()
        | denominator.isna()
        | ~valid_denominator
    ).astype("int8")

    features[f"{feature_name}_Raw"] = raw_ratio
    features[f"{feature_name}_Invalid_Flag"] = invalid_flag
    features[f"{feature_name}_Missing_Flag"] = missing_flag
    features[feature_name] = clean_rate

    return clean_rate


def numeric_sum(df, columns):
    """
    Sum numeric columns while preserving NaN when all inputs
    are unavailable.
    """

    available = [
        c for c in columns
        if c in df.columns
    ]

    if not available:
        return pd.Series(
            np.nan,
            index=df.index,
            dtype="float64"
        )

    numeric_df = df[available].apply(
        pd.to_numeric,
        errors="coerce"
    )

    result = numeric_df.sum(
        axis=1,
        min_count=1
    )

    return result


def add_missing_count(
    df,
    columns,
    feature_name,
    features
):
    """
    Count missing values across a group of important columns.
    """

    available = [
        c for c in columns
        if c in df.columns
    ]

    if not available:
        features[feature_name] = 0
        return

    features[feature_name] = (
        df[available]
        .isna()
        .sum(axis=1)
        .astype("int16")
    )


def add_exceeds_flag(
    numerator,
    denominator,
    feature_name,
    features
):
    """
    Flag impossible relationships such as:

        denied > received
        resubmitted > received
        overturned > appeals
    """

    numerator = to_numeric(numerator)
    denominator = to_numeric(denominator)

    comparable = (
        numerator.notna()
        & denominator.notna()
    )

    flag = pd.Series(
        0,
        index=numerator.index,
        dtype="int8"
    )

    flag.loc[comparable] = (
        numerator.loc[comparable]
        > denominator.loc[comparable]
    ).astype("int8")

    features[feature_name] = flag


def add_difference(
    numerator,
    denominator,
    feature_name,
    features
):
    """
    Difference between numerator and denominator.

    Useful for anomaly detection without destroying the original
    values.
    """

    numerator = to_numeric(numerator)
    denominator = to_numeric(denominator)

    features[feature_name] = numerator - denominator


# ============================================================
# MAIN FEATURE ENGINEERING
# ============================================================

def engineer_features(df):
    """
    Generate robust claims data-quality features.
    """

    features = {}

    # ========================================================
    # 1. BASIC NUMERIC CONVERSION
    # ========================================================

    numeric_columns = [
        "Issuer_ID",

        "Issuer_Claims_Received_Out_of_Network",
        "Issuer_Claims_Received_In_Network",
        "Issuer_Claims_Denied_Out_of_Network",
        "Issuer_Claims_Denied_In_Network",
        "Issuer_Claims_Resubmitted_Out_of_Network",
        "Issuer_Claims_Resubmitted_In_Network",

        "Issuer_Internal_Appeals_Filed",
        "Issuer_Number_Internal_Appeals_Overturned",
        "Issuer_Percent_Internal_Appeals_Overturned",

        "Issuer_External_Appeals_Filed",
        "Issuer_Number_External_Appeals_Overturned",
        "Issuer_Percent_External_Appeals_Overturned",

        "Plan_Number_Claims_Received_Out_of_Network",
        "Plan_Number_Claims_Received_In_Network",
        "Plan_Number_Claims_Denied_Out_of_Network",
        "Plan_Number_Claims_Denied_In_Network",
        "Plan_Number_Claims_Resubmitted_Out_of_Network",
        "Plan_Number_Claims_Resubmitted_In_Network",

        "Plan_Number_Claims_Denied_Referral_Required",
        "Plan_Number_Claims_Denied_Due_To_Out_Of_Network",
        "Plan_Number_Claims_Denied_Services_Excluded",
        "Plan_Number_Claims_Denied_Not_Medically_Necessary_Excluding_Behavioral_Health",
        "Plan_Number_Claims_Denied_Not_Medically_Necessary_Behavioral_Health_Only",
        "Plan_Number_Claims_Denied_Due_To_Enrolle_Benefit_Limit_Reached",
        "Plan_Number_Claims_Denied_Due_To_Member_Not_Covered",
        "Plan_Number_Claims_Denied_Due_To_Investigational_Experimental_Cosmetic_Proceduce",
        "Plan_Number_Claims_Denied_Due_To_Administrative_Reason",
        "Plan_Number_Claims_Denied_Other",

        "Average Monthly Enrollment",
        "Average Monthly Disenrollment",
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = to_numeric(df[col])

    # ========================================================
    # 2. ISSUER CLAIM VOLUME
    # ========================================================

    issuer_received_columns = [
        "Issuer_Claims_Received_Out_of_Network",
        "Issuer_Claims_Received_In_Network"
    ]

    issuer_denied_columns = [
        "Issuer_Claims_Denied_Out_of_Network",
        "Issuer_Claims_Denied_In_Network"
    ]

    issuer_resubmitted_columns = [
        "Issuer_Claims_Resubmitted_Out_of_Network",
        "Issuer_Claims_Resubmitted_In_Network"
    ]

    features["Issuer_Total_Claims"] = numeric_sum(
        df,
        issuer_received_columns
    )

    features["Issuer_Total_Denied_Claims"] = numeric_sum(
        df,
        issuer_denied_columns
    )

    features["Issuer_Total_Resubmitted_Claims"] = numeric_sum(
        df,
        issuer_resubmitted_columns
    )

    # ========================================================
    # 3. PLAN CLAIM VOLUME
    # ========================================================

    plan_received_columns = [
        "Plan_Number_Claims_Received_Out_of_Network",
        "Plan_Number_Claims_Received_In_Network"
    ]

    plan_denied_columns = [
        "Plan_Number_Claims_Denied_Out_of_Network",
        "Plan_Number_Claims_Denied_In_Network"
    ]

    plan_resubmitted_columns = [
        "Plan_Number_Claims_Resubmitted_Out_of_Network",
        "Plan_Number_Claims_Resubmitted_In_Network"
    ]

    features["Plan_Total_Claims"] = numeric_sum(
        df,
        plan_received_columns
    )

    features["Plan_Total_Denied_Claims"] = numeric_sum(
        df,
        plan_denied_columns
    )

    features["Plan_Total_Resubmitted_Claims"] = numeric_sum(
        df,
        plan_resubmitted_columns
    )

    # ========================================================
    # 4. ISSUER DENIAL RATES
    # ========================================================

    safe_ratio(
        df["Issuer_Claims_Denied_In_Network"],
        df["Issuer_Claims_Received_In_Network"],
        "Issuer_In_Network_Denial_Rate",
        features
    )

    safe_ratio(
        df["Issuer_Claims_Denied_Out_of_Network"],
        df["Issuer_Claims_Received_Out_of_Network"],
        "Issuer_Out_of_Network_Denial_Rate",
        features
    )

    safe_ratio(
        features["Issuer_Total_Denied_Claims"],
        features["Issuer_Total_Claims"],
        "Issuer_Overall_Denial_Rate",
        features
    )

    # ========================================================
    # 5. PLAN DENIAL RATES
    # ========================================================

    safe_ratio(
        df["Plan_Number_Claims_Denied_In_Network"],
        df["Plan_Number_Claims_Received_In_Network"],
        "Plan_In_Network_Denial_Rate",
        features
    )

    safe_ratio(
        df["Plan_Number_Claims_Denied_Out_of_Network"],
        df["Plan_Number_Claims_Received_Out_of_Network"],
        "Plan_Out_of_Network_Denial_Rate",
        features
    )

    safe_ratio(
        features["Plan_Total_Denied_Claims"],
        features["Plan_Total_Claims"],
        "Plan_Overall_Denial_Rate",
        features
    )

    # ========================================================
    # 6. ISSUER RESUBMISSION RATES
    # ========================================================

    safe_ratio(
        df["Issuer_Claims_Resubmitted_In_Network"],
        df["Issuer_Claims_Received_In_Network"],
        "Issuer_In_Network_Resubmission_Rate",
        features
    )

    safe_ratio(
        df["Issuer_Claims_Resubmitted_Out_of_Network"],
        df["Issuer_Claims_Received_Out_of_Network"],
        "Issuer_Out_of_Network_Resubmission_Rate",
        features
    )

    safe_ratio(
        features["Issuer_Total_Resubmitted_Claims"],
        features["Issuer_Total_Claims"],
        "Issuer_Overall_Resubmission_Rate",
        features
    )

    # ========================================================
    # 7. PLAN RESUBMISSION RATES
    # ========================================================

    safe_ratio(
        df["Plan_Number_Claims_Resubmitted_In_Network"],
        df["Plan_Number_Claims_Received_In_Network"],
        "Plan_In_Network_Resubmission_Rate",
        features
    )

    safe_ratio(
        df["Plan_Number_Claims_Resubmitted_Out_of_Network"],
        df["Plan_Number_Claims_Received_Out_of_Network"],
        "Plan_Out_of_Network_Resubmission_Rate",
        features
    )

    safe_ratio(
        features["Plan_Total_Resubmitted_Claims"],
        features["Plan_Total_Claims"],
        "Plan_Overall_Resubmission_Rate",
        features
    )

    # ========================================================
    # 8. CLAIM MIX / NETWORK RATIOS
    # ========================================================

    safe_ratio(
        df["Issuer_Claims_Received_In_Network"],
        features["Issuer_Total_Claims"],
        "Issuer_In_Network_Claim_Ratio",
        features
    )

    safe_ratio(
        df["Issuer_Claims_Received_Out_of_Network"],
        features["Issuer_Total_Claims"],
        "Issuer_Out_of_Network_Claim_Ratio",
        features
    )

    safe_ratio(
        df["Plan_Number_Claims_Received_In_Network"],
        features["Plan_Total_Claims"],
        "Plan_In_Network_Claim_Ratio",
        features
    )

    safe_ratio(
        df["Plan_Number_Claims_Received_Out_of_Network"],
        features["Plan_Total_Claims"],
        "Plan_Out_of_Network_Claim_Ratio",
        features
    )

    # ========================================================
    # 9. APPEALS
    # ========================================================

    features["Total_Internal_Appeals"] = numeric_sum(
        df,
        ["Issuer_Internal_Appeals_Filed"]
    )

    features["Total_External_Appeals"] = numeric_sum(
        df,
        ["Issuer_External_Appeals_Filed"]
    )

    features["Total_Appeals"] = numeric_sum(
        df,
        [
            "Issuer_Internal_Appeals_Filed",
            "Issuer_External_Appeals_Filed"
        ]
    )

    features["Total_Overturned_Appeals"] = numeric_sum(
        df,
        [
            "Issuer_Number_Internal_Appeals_Overturned",
            "Issuer_Number_External_Appeals_Overturned"
        ]
    )

    # ========================================================
    # 10. APPEAL OVERTURN RATES
    # ========================================================

    safe_ratio(
        df["Issuer_Number_Internal_Appeals_Overturned"],
        df["Issuer_Internal_Appeals_Filed"],
        "Internal_Appeal_Overturn_Rate",
        features
    )

    safe_ratio(
        df["Issuer_Number_External_Appeals_Overturned"],
        df["Issuer_External_Appeals_Filed"],
        "External_Appeal_Overturn_Rate",
        features
    )

    safe_ratio(
        features["Total_Overturned_Appeals"],
        features["Total_Appeals"],
        "Overall_Appeal_Overturn_Rate",
        features
    )

    # ========================================================
    # 11. APPEAL TO DENIAL RATIOS
    # ========================================================

    safe_ratio(
        features["Total_Internal_Appeals"],
        features["Issuer_Total_Denied_Claims"],
        "Internal_Appeal_to_Denial_Rate",
        features
    )

    safe_ratio(
        features["Total_External_Appeals"],
        features["Issuer_Total_Denied_Claims"],
        "External_Appeal_to_Denial_Rate",
        features
    )

    safe_ratio(
        features["Total_Appeals"],
        features["Issuer_Total_Denied_Claims"],
        "Total_Appeal_to_Denial_Rate",
        features
    )

    # ========================================================
    # 12. DENIAL REASON COUNTS
    # ========================================================

    denial_reason_map = {
        "Referral_Required_Denial_Count":
            "Plan_Number_Claims_Denied_Referral_Required",

        "Out_of_Network_Denial_Count":
            "Plan_Number_Claims_Denied_Due_To_Out_Of_Network",

        "Services_Excluded_Denial_Count":
            "Plan_Number_Claims_Denied_Services_Excluded",

        "Medical_Necessity_Denial_Count":
            "Plan_Number_Claims_Denied_Not_Medically_Necessary_Excluding_Behavioral_Health",

        "Behavioral_Health_Medical_Necessity_Denial_Count":
            "Plan_Number_Claims_Denied_Not_Medically_Necessary_Behavioral_Health_Only",

        "Benefit_Limit_Denial_Count":
            "Plan_Number_Claims_Denied_Due_To_Enrolle_Benefit_Limit_Reached",

        "Member_Not_Covered_Denial_Count":
            "Plan_Number_Claims_Denied_Due_To_Member_Not_Covered",

        "Investigational_Experimental_Cosmetic_Denial_Count":
            "Plan_Number_Claims_Denied_Due_To_Investigational_Experimental_Cosmetic_Proceduce",

        "Administrative_Denial_Count":
            "Plan_Number_Claims_Denied_Due_To_Administrative_Reason",

        "Other_Denial_Count":
            "Plan_Number_Claims_Denied_Other",
    }

    for feature_name, source_column in denial_reason_map.items():

        if source_column in df.columns:

            features[feature_name] = to_numeric(
                df[source_column]
            )

    # ========================================================
    # 13. DENIAL REASON RATES
    # ========================================================

    rate_mapping = {
        "Referral_Required_Denial_Rate":
            "Referral_Required_Denial_Count",

        "Out_of_Network_Denial_Rate":
            "Out_of_Network_Denial_Count",

        "Services_Excluded_Denial_Rate":
            "Services_Excluded_Denial_Count",

        "Medical_Necessity_Denial_Rate":
            "Medical_Necessity_Denial_Count",

        "Behavioral_Health_Medical_Necessity_Denial_Rate":
            "Behavioral_Health_Medical_Necessity_Denial_Count",

        "Benefit_Limit_Denial_Rate":
            "Benefit_Limit_Denial_Count",

        "Member_Not_Covered_Denial_Rate":
            "Member_Not_Covered_Denial_Count",

        "Investigational_Experimental_Cosmetic_Denial_Rate":
            "Investigational_Experimental_Cosmetic_Denial_Count",

        "Administrative_Denial_Rate":
            "Administrative_Denial_Count",

        "Other_Denial_Rate":
            "Other_Denial_Count",
    }

    for feature_name, numerator_feature in rate_mapping.items():

        safe_ratio(
            features[numerator_feature],
            features["Plan_Total_Denied_Claims"],
            feature_name,
            features
        )

    # ========================================================
    # 14. ENROLLMENT FEATURES
    # ========================================================

    enrollment = to_numeric(
        df["Average Monthly Enrollment"]
    )

    disenrollment = to_numeric(
        df["Average Monthly Disenrollment"]
    )

    safe_ratio(
        disenrollment,
        enrollment,
        "Disenrollment_Rate",
        features
    )

    safe_ratio(
        features["Plan_Total_Claims"],
        enrollment,
        "Claims_Per_Enrollee",
        features,
        invalid_threshold=np.inf
    )

    safe_ratio(
        features["Plan_Total_Denied_Claims"],
        enrollment,
        "Denied_Claims_Per_Enrollee",
        features,
        invalid_threshold=np.inf
    )

    safe_ratio(
        features["Plan_Total_Resubmitted_Claims"],
        enrollment,
        "Resubmitted_Claims_Per_Enrollee",
        features,
        invalid_threshold=np.inf
    )

    # ========================================================
    # 15. PLAN VS ISSUER COMPARISON
    # ========================================================

    safe_ratio(
        features["Plan_Total_Claims"],
        features["Issuer_Total_Claims"],
        "Plan_to_Issuer_Claim_Volume_Ratio",
        features,
        invalid_threshold=np.inf
    )

    safe_ratio(
        features["Plan_Total_Denied_Claims"],
        features["Issuer_Total_Denied_Claims"],
        "Plan_to_Issuer_Denied_Claim_Ratio",
        features,
        invalid_threshold=np.inf
    )

    # ========================================================
    # 16. DATA CONSISTENCY FLAGS
    # ========================================================

    add_exceeds_flag(
        features["Plan_Total_Denied_Claims"],
        features["Plan_Total_Claims"],
        "Plan_Denied_Exceeds_Received",
        features
    )

    add_exceeds_flag(
        features["Issuer_Total_Denied_Claims"],
        features["Issuer_Total_Claims"],
        "Issuer_Denied_Exceeds_Received",
        features
    )

    add_exceeds_flag(
        features["Plan_Total_Resubmitted_Claims"],
        features["Plan_Total_Claims"],
        "Plan_Resubmitted_Exceeds_Received",
        features
    )

    add_exceeds_flag(
        features["Issuer_Total_Resubmitted_Claims"],
        features["Issuer_Total_Claims"],
        "Issuer_Resubmitted_Exceeds_Received",
        features
    )

    add_exceeds_flag(
        df["Issuer_Number_Internal_Appeals_Overturned"],
        df["Issuer_Internal_Appeals_Filed"],
        "Internal_Overturned_Exceeds_Appeals",
        features
    )

    add_exceeds_flag(
        df["Issuer_Number_External_Appeals_Overturned"],
        df["Issuer_External_Appeals_Filed"],
        "External_Overturned_Exceeds_Appeals",
        features
    )

    # ========================================================
    # 17. DIFFERENCE FEATURES
    # ========================================================

    add_difference(
        features["Plan_Total_Claims"],
        features["Plan_Total_Denied_Claims"],
        "Plan_Received_Minus_Denied",
        features
    )

    add_difference(
        features["Issuer_Total_Claims"],
        features["Issuer_Total_Denied_Claims"],
        "Issuer_Received_Minus_Denied",
        features
    )

    add_difference(
        features["Plan_Total_Claims"],
        features["Plan_Total_Resubmitted_Claims"],
        "Plan_Received_Minus_Resubmitted",
        features
    )

    add_difference(
        features["Issuer_Total_Claims"],
        features["Issuer_Total_Resubmitted_Claims"],
        "Issuer_Received_Minus_Resubmitted",
        features
    )

    # ========================================================
    # 18. IMPORTANT MISSINGNESS
    # ========================================================

    issuer_claim_columns = [
        "Issuer_Claims_Received_Out_of_Network",
        "Issuer_Claims_Received_In_Network",
        "Issuer_Claims_Denied_Out_of_Network",
        "Issuer_Claims_Denied_In_Network",
        "Issuer_Claims_Resubmitted_Out_of_Network",
        "Issuer_Claims_Resubmitted_In_Network",
    ]

    plan_claim_columns = [
        "Plan_Number_Claims_Received_Out_of_Network",
        "Plan_Number_Claims_Received_In_Network",
        "Plan_Number_Claims_Denied_Out_of_Network",
        "Plan_Number_Claims_Denied_In_Network",
        "Plan_Number_Claims_Resubmitted_Out_of_Network",
        "Plan_Number_Claims_Resubmitted_In_Network",
    ]

    appeal_columns = [
        "Issuer_Internal_Appeals_Filed",
        "Issuer_Number_Internal_Appeals_Overturned",
        "Issuer_External_Appeals_Filed",
        "Issuer_Number_External_Appeals_Overturned",
    ]

    enrollment_columns = [
        "Average Monthly Enrollment",
        "Average Monthly Disenrollment",
    ]

    add_missing_count(
        df,
        issuer_claim_columns,
        "Issuer_Claims_Missing_Count",
        features
    )

    add_missing_count(
        df,
        plan_claim_columns,
        "Plan_Claims_Missing_Count",
        features
    )

    add_missing_count(
        df,
        appeal_columns,
        "Appeal_Data_Missing_Count",
        features
    )

    add_missing_count(
        df,
        enrollment_columns,
        "Enrollment_Data_Missing_Count",
        features
    )

    important_columns = (
        issuer_claim_columns
        + plan_claim_columns
        + appeal_columns
        + enrollment_columns
        + list(denial_reason_map.values())
    )

    add_missing_count(
        df,
        important_columns,
        "Total_Important_Missing_Count",
        features
    )

    # ========================================================
    # 19. MISSINGNESS PERCENTAGE
    # ========================================================

    total_important = len(
        [
            c for c in important_columns
            if c in df.columns
        ]
    )

    if total_important > 0:
        features["Important_Missing_Rate"] = (
            features["Total_Important_Missing_Count"]
            / total_important
        )

    # ========================================================
    # 20. SUPPRESSION / MISSINGNESS SIGNAL
    # ========================================================

    suppression_candidates = [
        c for c in df.columns
        if (
            "Claims" in c
            or "Appeals" in c
            or "Enrollment" in c
            or "Disenrollment" in c
        )
    ]

    if suppression_candidates:

        features["Suppressed_or_NonNumeric_Count"] = (
            df[suppression_candidates]
            .apply(
                lambda col: pd.to_numeric(
                    col,
                    errors="coerce"
                ).isna()
            )
            .sum(axis=1)
            .astype("int16")
        )

    # ========================================================
    # 21. FEATURE FRAME
    # ========================================================

    engineered_df = pd.DataFrame(
        features,
        index=df.index
    )

    # ========================================================
    # 22. FINAL CLEANUP OF NUMERIC FEATURES
    # ========================================================

    for col in engineered_df.columns:

        if engineered_df[col].dtype == "float64":

            engineered_df[col] = (
                engineered_df[col]
                .replace([np.inf, -np.inf], np.nan)
            )

    # ========================================================
    # 23. CONCATENATE ONCE
    # ========================================================
    #
    # This avoids the DataFrame fragmentation warning that
    # appeared in your previous implementation.

    result = pd.concat(
        [
            df,
            engineered_df
        ],
        axis=1
    )

    return result, list(engineered_df.columns)


# ============================================================
# VALIDATION
# ============================================================

def validate_features(df, engineered_columns):

    print()
    print("=" * 70)
    print("FEATURE VALIDATION REPORT")
    print("=" * 70)

    print(f"Rows    : {len(df):,}")
    print(f"Columns : {len(df.columns):,}")
    print(
        f"New engineered features: "
        f"{len(engineered_columns):,}"
    )

    # --------------------------------------------------------
    # Infinite values
    # --------------------------------------------------------

    numeric_df = df.select_dtypes(
        include=[np.number]
    )

    infinite_count = np.isinf(
        numeric_df.to_numpy()
    ).sum()

    print()
    print(
        f"Infinite values: {infinite_count:,}"
    )

    # --------------------------------------------------------
    # Invalid clean rates
    # --------------------------------------------------------

    rate_columns = [
        c for c in engineered_columns
        if (
            c.endswith("_Rate")
            and not c.endswith("_Raw")
        )
    ]

    invalid_clean_rates = []

    for col in rate_columns:

        if col not in df.columns:
            continue

        values = df[col].dropna()

        invalid_count = (
            (values < 0)
            | (values > 1)
        ).sum()

        if invalid_count > 0:

            invalid_clean_rates.append(
                (col, int(invalid_count))
            )

    print()
    print(
        "Invalid CLEAN rate values: "
        f"{sum(x[1] for x in invalid_clean_rates):,}"
    )

    if invalid_clean_rates:

        print()
        print("Problematic clean rate columns:")

        for col, count in invalid_clean_rates:
            print(
                f"  - {col}: {count}"
            )

    else:
        print(
            "All clean *_Rate features are within [0, 1]."
        )

    # --------------------------------------------------------
    # Raw invalid ratios
    # --------------------------------------------------------

    raw_ratio_columns = [
        c for c in engineered_columns
        if c.endswith("_Raw")
    ]

    total_raw_invalid = 0

    for col in raw_ratio_columns:

        values = df[col].dropna()

        total_raw_invalid += int(
            (
                (values < 0)
                | (values > 1)
            ).sum()
        )

    print()
    print(
        "Raw ratio values > 1 or < 0: "
        f"{total_raw_invalid:,}"
    )

    print(
        "These are intentionally preserved as "
        "data-quality signals."
    )

    # --------------------------------------------------------
    # Consistency flags
    # --------------------------------------------------------

    consistency_columns = [
        c for c in engineered_columns
        if (
            c.endswith("_Exceeds_Received")
            or c.endswith("_Exceeds_Appeals")
        )
    ]

    print()
    print("Consistency violations:")

    for col in consistency_columns:

        count = int(
            df[col].sum()
        )

        print(
            f"  - {col}: {count:,}"
        )

    # --------------------------------------------------------
    # Missingness
    # --------------------------------------------------------

    missing_counts = (
        df[engineered_columns]
        .isna()
        .sum()
        .sort_values(
            ascending=False
        )
    )

    print()
    print("Top missing engineered features:")

    shown = 0

    for col, count in missing_counts.items():

        if count > 0:

            print(
                f"  - {col}: "
                f"{count:,} "
                f"({count / len(df) * 100:.2f}%)"
            )

            shown += 1

            if shown >= 15:
                break


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("TC-PUF CLAIMS FEATURE ENGINEERING")
    print("=" * 70)

    print()
    print("Input file:")
    print(INPUT_FILE)

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"\nInput file not found:\n{INPUT_FILE}\n\n"
            "Make sure preprocessing has been executed first."
        )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = pd.read_csv(
        INPUT_FILE,
        low_memory=False
    )

    print()
    print(
        f"Original dataset shape: "
        f"{df.shape}"
    )

    # --------------------------------------------------------
    # Feature engineering
    # --------------------------------------------------------

    print()
    print("Creating engineered features...")

    result, engineered_columns = engineer_features(
        df
    )

    print(
        "Feature engineering completed."
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validate_features(
        result,
        engineered_columns
    )

    # --------------------------------------------------------
    # Sample
    # --------------------------------------------------------

    sample_columns = [
        "Plan_Total_Claims",
        "Plan_Total_Denied_Claims",
        "Plan_Overall_Denial_Rate",
        "Plan_Overall_Resubmission_Rate",
        "Out_of_Network_Denial_Rate",
        "Administrative_Denial_Rate",
        "Internal_Appeal_Overturn_Rate",
        "Disenrollment_Rate",
        "Total_Important_Missing_Count",
        "Important_Missing_Rate",
    ]

    sample_columns = [
        c for c in sample_columns
        if c in result.columns
    ]

    print()
    print("=" * 70)
    print("SAMPLE ENGINEERED DATA")
    print("=" * 70)

    print(
        result[
            sample_columns
        ].head(10).to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("=" * 70)
    print("FEATURE ENGINEERING COMPLETED")
    print("=" * 70)

    print()
    print(
        f"Output file : {OUTPUT_FILE}"
    )

    print(
        f"Rows        : {len(result):,}"
    )

    print(
        f"Columns     : {len(result.columns):,}"
    )

    print(
        f"New features: {len(engineered_columns):,}"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "Do NOT impute or scale the data in this script."
    )

    print(
        "That should happen in the ML preprocessing pipeline."
    )


if __name__ == "__main__":
    main()