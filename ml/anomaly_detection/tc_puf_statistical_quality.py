"""
TC-PUF Statistical Quality / Anomaly Detection
================================================

Purpose
-------
Detect statistically unusual records in the TC-PUF claims dataset.

Input
-----
data/processed/tc_puf_feature_engineered.csv

Outputs
-------
data/processed/tc_puf_statistical_quality.csv
data/processed/tc_puf_statistical_quality.json
data/processed/tc_puf_statistical_metadata.json

Design
------
1. Select meaningful numeric statistical features.
2. Exclude identifiers, missing flags, suppressed indicators,
   missing-count features and binary/constant features.
3. Detect:
      - Z-score outliers
      - IQR outliers
      - 1st percentile anomalies
      - 99th percentile anomalies
4. Keep missingness separate from statistical outliers.
5. Do NOT make a record HIGH merely because many values are missing.
6. Require stronger evidence before assigning HIGH severity.
7. Produce row-level anomaly explanations.
"""

import os
import json
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


# ================================================================
# CONFIGURATION
# ================================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "tc_puf_feature_engineered.csv"
)

OUTPUT_CSV = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "tc_puf_statistical_quality.csv"
)

OUTPUT_JSON = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "tc_puf_statistical_quality.json"
)

OUTPUT_METADATA = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "tc_puf_statistical_metadata.json"
)


# Statistical thresholds
Z_THRESHOLD = 3.0

LOW_PERCENTILE = 0.01
HIGH_PERCENTILE = 0.99

# A feature must have enough non-null values to calculate statistics.
MIN_NON_NULL_VALUES = 20

# Very small IQRs can cause excessive IQR outliers.
MIN_IQR = 1e-12

# Missingness thresholds
MISSING_LOW_THRESHOLD = 0.25
MISSING_HIGH_THRESHOLD = 0.75

# Severity thresholds
HIGH_OUTLIER_COUNT = 5
MEDIUM_OUTLIER_COUNT = 2

# Fraction of statistical features that need to be anomalous
HIGH_OUTLIER_RATIO = 0.10
MEDIUM_OUTLIER_RATIO = 0.03


# ================================================================
# PRINT HEADER
# ================================================================

print("=" * 70)
print("TC-PUF STATISTICAL QUALITY CHECK")
print("=" * 70)

print()
print("Input file:")
print(INPUT_FILE)

print()
print("Output CSV:")
print(OUTPUT_CSV)

print()
print("Output JSON:")
print(OUTPUT_JSON)

print()
print("Metadata:")
print(OUTPUT_METADATA)


# ================================================================
# CHECK INPUT
# ================================================================

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"\nInput dataset was not found:\n{INPUT_FILE}\n"
        f"\nPlease make sure tc_puf_feature_engineered.csv exists "
        f"in data/processed/"
    )


# ================================================================
# LOAD DATA
# ================================================================

print()
print("=" * 70)
print("LOADING DATASET")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print()
print(f"Dataset shape : {df.shape}")
print(f"Rows          : {df.shape[0]}")
print(f"Columns       : {df.shape[1]}")


# ================================================================
# BASIC COLUMN INFORMATION
# ================================================================

numeric_columns = df.select_dtypes(
    include=[np.number]
).columns.tolist()

print()
print("Numeric columns found:")
print(len(numeric_columns))


# ================================================================
# IDENTIFY COLUMNS TO EXCLUDE
# ================================================================

print()
print("=" * 70)
print("STATISTICAL FEATURE SELECTION")
print("=" * 70)


identifier_columns = []
missing_flag_columns = []
suppressed_columns = []
missing_count_columns = []
binary_constant_columns = []


for col in numeric_columns:

    col_lower = col.lower()

    # ------------------------------------------------------------
    # Identifier columns
    # ------------------------------------------------------------

    if any(
        key in col_lower
        for key in [
            "issuer_id",
            "plan_id",
            "id"
        ]
    ):
        identifier_columns.append(col)
        continue

    # ------------------------------------------------------------
    # Missing flag columns
    # ------------------------------------------------------------

    if (
        "missing_flag" in col_lower
        or col_lower.endswith("_missing")
        or "_missing_" in col_lower
    ):
        missing_flag_columns.append(col)
        continue

    # ------------------------------------------------------------
    # Suppressed columns
    # ------------------------------------------------------------

    if (
        "suppressed" in col_lower
        or "suppression" in col_lower
    ):
        suppressed_columns.append(col)
        continue

    # ------------------------------------------------------------
    # Missing-count columns
    # ------------------------------------------------------------

    if (
        "missing_count" in col_lower
        or "null_count" in col_lower
        or "na_count" in col_lower
    ):
        missing_count_columns.append(col)
        continue

    # ------------------------------------------------------------
    # Binary / constant columns
    # ------------------------------------------------------------

    non_null_unique = df[col].dropna().nunique()

    if non_null_unique <= 2:

        binary_constant_columns.append(col)


# ================================================================
# CREATE INITIAL STATISTICAL FEATURE LIST
# ================================================================

statistical_features = []

for col in numeric_columns:

    if col in identifier_columns:
        continue

    if col in missing_flag_columns:
        continue

    if col in suppressed_columns:
        continue

    if col in missing_count_columns:
        continue

    if col in binary_constant_columns:
        continue

    statistical_features.append(col)


print()
print(
    f"Numeric columns found                 : "
    f"{len(numeric_columns)}"
)

print(
    f"Excluded identifier columns           : "
    f"{len(identifier_columns)}"
)

print(
    f"Excluded missing flag columns         : "
    f"{len(missing_flag_columns)}"
)

print(
    f"Excluded suppressed columns           : "
    f"{len(suppressed_columns)}"
)

print(
    f"Excluded missing count columns        : "
    f"{len(missing_count_columns)}"
)

print(
    f"Excluded binary/constant columns      : "
    f"{len(binary_constant_columns)}"
)


# ================================================================
# REMOVE FEATURES WITH TOO FEW OBSERVATIONS
# ================================================================

valid_statistical_features = []

low_information_features = []

for col in statistical_features:

    non_null_count = df[col].notna().sum()

    if non_null_count >= MIN_NON_NULL_VALUES:

        # Require non-zero variance
        variance = df[col].dropna().var()

        if pd.notna(variance) and variance > 0:
            valid_statistical_features.append(col)
        else:
            low_information_features.append(col)

    else:
        low_information_features.append(col)


statistical_features = valid_statistical_features


print(
    f"Excluded low-information features    : "
    f"{len(low_information_features)}"
)

print()
print(
    f"Statistical features analyzed         : "
    f"{len(statistical_features)}"
)


print()
print("Statistical features:")

for feature in statistical_features:
    print(f" - {feature}")


# ================================================================
# PREPARE NUMERIC DATA
# ================================================================

work_df = df.copy()

for col in statistical_features:

    work_df[col] = pd.to_numeric(
        work_df[col],
        errors="coerce"
    )


# ================================================================
# STORAGE FOR RESULTS
# ================================================================

n_rows = len(work_df)
n_features = len(statistical_features)


# Per-row counts
z_outlier_count = np.zeros(n_rows, dtype=int)
iqr_outlier_count = np.zeros(n_rows, dtype=int)
below_percentile_count = np.zeros(n_rows, dtype=int)
above_percentile_count = np.zeros(n_rows, dtype=int)

missing_count = np.zeros(n_rows, dtype=int)
invalid_count = np.zeros(n_rows, dtype=int)

# Feature-level explanation
outlier_features = [[] for _ in range(n_rows)]


# ================================================================
# STATISTICAL CHECKS
# ================================================================

print()
print("=" * 70)
print("RUNNING STATISTICAL CHECKS")
print("=" * 70)

print()
print(
    f"Statistical feature columns analyzed : "
    f"{len(statistical_features)}"
)


for feature in statistical_features:

    print()
    print(f"Analyzing: {feature}")

    values = work_df[feature]

    # ------------------------------------------------------------
    # Missing values
    # ------------------------------------------------------------

    missing_mask = values.isna()

    missing_count += missing_mask.astype(int).values

    # ------------------------------------------------------------
    # Valid values
    # ------------------------------------------------------------

    valid = values.dropna()

    if len(valid) < MIN_NON_NULL_VALUES:
        continue

    # ------------------------------------------------------------
    # Mean / standard deviation
    # ------------------------------------------------------------

    mean_value = valid.mean()
    std_value = valid.std()

    # ------------------------------------------------------------
    # Z-SCORE
    # ------------------------------------------------------------

    if (
        pd.notna(std_value)
        and std_value > 0
    ):

        z_scores = (
            (values - mean_value)
            / std_value
        )

        z_mask = (
            z_scores.abs() >= Z_THRESHOLD
        )

        z_mask = z_mask.fillna(False)

        z_indices = np.where(
            z_mask.to_numpy()
        )[0]

        for idx in z_indices:

            z_outlier_count[idx] += 1

            value = values.iloc[idx]

            outlier_features[idx].append(
                f"{feature}={value:.4f} [Z={z_scores.iloc[idx]:.2f}]"
            )

    # ------------------------------------------------------------
    # IQR
    # ------------------------------------------------------------

    q1 = valid.quantile(0.25)
    q3 = valid.quantile(0.75)

    iqr = q3 - q1

    if (
        pd.notna(iqr)
        and iqr > MIN_IQR
    ):

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        iqr_mask = (
            (values < lower_bound)
            |
            (values > upper_bound)
        )

        iqr_mask = iqr_mask.fillna(False)

        iqr_indices = np.where(
            iqr_mask.to_numpy()
        )[0]

        for idx in iqr_indices:

            iqr_outlier_count[idx] += 1

            # Avoid duplicating the same feature repeatedly
            already_added = any(
                item.startswith(
                    f"{feature}="
                )
                for item in outlier_features[idx]
            )

            if not already_added:

                value = values.iloc[idx]

                outlier_features[idx].append(
                    f"{feature}={value:.4f} [IQR]"
                )

    # ------------------------------------------------------------
    # PERCENTILE CHECK
    # ------------------------------------------------------------

    lower_percentile = valid.quantile(
        LOW_PERCENTILE
    )

    upper_percentile = valid.quantile(
        HIGH_PERCENTILE
    )

    below_mask = (
        values < lower_percentile
    ).fillna(False)

    above_mask = (
        values > upper_percentile
    ).fillna(False)

    below_indices = np.where(
        below_mask.to_numpy()
    )[0]

    above_indices = np.where(
        above_mask.to_numpy()
    )[0]

    for idx in below_indices:

        below_percentile_count[idx] += 1

    for idx in above_indices:

        above_percentile_count[idx] += 1


# ================================================================
# INVALID VALUE CHECK
# ================================================================

print()
print("=" * 70)
print("RUNNING INVALID VALUE CHECKS")
print("=" * 70)


# ---------------------------------------------------------------
# Percentage / rate columns
# ---------------------------------------------------------------

rate_keywords = [
    "rate",
    "percent",
    "percentage"
]

for feature in statistical_features:

    feature_lower = feature.lower()

    if any(
        keyword in feature_lower
        for keyword in rate_keywords
    ):

        values = work_df[feature]

        invalid_mask = (
            (values < 0)
            |
            (values > 100)
        )

        invalid_mask = invalid_mask.fillna(False)

        invalid_indices = np.where(
            invalid_mask.to_numpy()
        )[0]

        for idx in invalid_indices:

            invalid_count[idx] += 1

            value = values.iloc[idx]

            outlier_features[idx].append(
                f"{feature}={value:.4f} [INVALID_RATE]"
            )


# ---------------------------------------------------------------
# Count / volume columns
# ---------------------------------------------------------------

count_keywords = [
    "claims",
    "appeals",
    "enrollment",
    "disenrollment",
    "denied",
    "resubmitted"
]

for feature in statistical_features:

    feature_lower = feature.lower()

    if any(
        keyword in feature_lower
        for keyword in count_keywords
    ):

        values = work_df[feature]

        # Counts cannot be negative.
        invalid_mask = (
            values < 0
        ).fillna(False)

        invalid_indices = np.where(
            invalid_mask.to_numpy()
        )[0]

        for idx in invalid_indices:

            invalid_count[idx] += 1

            value = values.iloc[idx]

            outlier_features[idx].append(
                f"{feature}={value:.4f} [INVALID_NEGATIVE]"
            )


# ================================================================
# CONVERT RESULTS TO DATAFRAME
# ================================================================

result = df.copy()


result["Stat_Z_Outlier_Count"] = (
    z_outlier_count
)

result["Stat_IQR_Outlier_Count"] = (
    iqr_outlier_count
)

result["Stat_Below_1st_Percentile"] = (
    below_percentile_count
)

result["Stat_Above_99th_Percentile"] = (
    above_percentile_count
)

result["Stat_Outlier_Count"] = (
    z_outlier_count
    + iqr_outlier_count
)

result["Stat_Missing_Count"] = (
    missing_count
)

result["Stat_Invalid_Count"] = (
    invalid_count
)


# ================================================================
# CALCULATE OUTLIER RATIO
# ================================================================

if n_features > 0:

    result["Stat_Outlier_Ratio"] = (
        result["Stat_Outlier_Count"]
        / n_features
    )

else:

    result["Stat_Outlier_Ratio"] = 0.0


# ================================================================
# MISSING RATIO
# ================================================================

if n_features > 0:

    result["Stat_Missing_Ratio"] = (
        result["Stat_Missing_Count"]
        / n_features
    )

else:

    result["Stat_Missing_Ratio"] = 0.0


# ================================================================
# STATISTICAL QUALITY SCORE
# ================================================================

result["Stat_Total_Quality_Issues"] = (
    result["Stat_Outlier_Count"]
    + result["Stat_Invalid_Count"]
)


# ================================================================
# SEVERITY LOGIC
# ================================================================

severity = []

for idx, row in result.iterrows():

    outliers = int(
        row["Stat_Outlier_Count"]
    )

    invalids = int(
        row["Stat_Invalid_Count"]
    )

    outlier_ratio = float(
        row["Stat_Outlier_Ratio"]
    )

    missing_ratio = float(
        row["Stat_Missing_Ratio"]
    )

    # ------------------------------------------------------------
    # HIGH
    # ------------------------------------------------------------
    # Invalid values are serious.
    #
    # OR many independent statistical outliers.
    #
    # OR a high proportion of features are statistical outliers.
    # ------------------------------------------------------------

    if (
        invalids > 0
        or
        outliers >= HIGH_OUTLIER_COUNT
        or
        outlier_ratio >= HIGH_OUTLIER_RATIO
    ):

        severity.append("HIGH")

    # ------------------------------------------------------------
    # MEDIUM
    # ------------------------------------------------------------

    elif (
        outliers >= MEDIUM_OUTLIER_COUNT
        or
        outlier_ratio >= MEDIUM_OUTLIER_RATIO
    ):

        severity.append("MEDIUM")

    # ------------------------------------------------------------
    # LOW
    # ------------------------------------------------------------
    # Important:
    # Missingness alone does NOT make the record HIGH.
    #
    # A record with substantial missingness is LOW unless
    # statistical/invalid evidence also exists.
    # ------------------------------------------------------------

    elif (
        missing_ratio >= MISSING_HIGH_THRESHOLD
        or
        outliers == 1
    ):

        severity.append("LOW")

    # ------------------------------------------------------------
    # NORMAL
    # ------------------------------------------------------------

    else:

        severity.append("NORMAL")


result["Statistical_Severity"] = severity


# ================================================================
# RECORD LEVEL ANOMALY FLAG
# ================================================================

result["Statistical_Anomaly"] = (
    result["Statistical_Severity"]
    != "NORMAL"
)


# ================================================================
# ADD FEATURE EXPLANATIONS
# ================================================================

result["Stat_Outlier_Features"] = [
    " | ".join(features)
    for features in outlier_features
]


# ================================================================
# ENSURE KEY COLUMNS EXIST
# ================================================================

preferred_identity_columns = [
    "Plan_ID",
    "Issuer_ID",
    "State"
]

identity_columns = [
    col
    for col in preferred_identity_columns
    if col in result.columns
]


# ================================================================
# REORDER IMPORTANT COLUMNS
# ================================================================

quality_columns = [
    "Statistical_Severity",
    "Statistical_Anomaly",
    "Stat_Total_Quality_Issues",
    "Stat_Outlier_Count",
    "Stat_Z_Outlier_Count",
    "Stat_IQR_Outlier_Count",
    "Stat_Below_1st_Percentile",
    "Stat_Above_99th_Percentile",
    "Stat_Outlier_Ratio",
    "Stat_Missing_Count",
    "Stat_Missing_Ratio",
    "Stat_Invalid_Count",
    "Stat_Outlier_Features"
]


remaining_columns = [
    col
    for col in result.columns
    if col not in identity_columns
    and col not in quality_columns
]


result = result[
    identity_columns
    + quality_columns
    + remaining_columns
]


# ================================================================
# SUMMARY STATISTICS
# ================================================================

total_rows = len(result)

anomaly_rows = int(
    result["Statistical_Anomaly"].sum()
)

normal_rows = (
    total_rows
    - anomaly_rows
)

total_z_outliers = int(
    result["Stat_Z_Outlier_Count"].sum()
)

total_iqr_outliers = int(
    result["Stat_IQR_Outlier_Count"].sum()
)

total_below_percentile = int(
    result["Stat_Below_1st_Percentile"].sum()
)

total_above_percentile = int(
    result["Stat_Above_99th_Percentile"].sum()
)

total_missing = int(
    result["Stat_Missing_Count"].sum()
)

total_invalid = int(
    result["Stat_Invalid_Count"].sum()
)


severity_distribution = (
    result["Statistical_Severity"]
    .value_counts()
    .to_dict()
)


# Make sure all categories appear.
for category in [
    "HIGH",
    "MEDIUM",
    "LOW",
    "NORMAL"
]:

    severity_distribution.setdefault(
        category,
        0
    )


# ================================================================
# PRINT REPORT
# ================================================================

print()
print("=" * 70)
print("STATISTICAL QUALITY REPORT")
print("=" * 70)

print()
print(
    f"Rows analyzed                         : "
    f"{total_rows:,}"
)

print(
    f"Features analyzed                     : "
    f"{n_features}"
)

print(
    f"Records with statistical anomalies    : "
    f"{anomaly_rows:,}"
)

print(
    f"Normal records                        : "
    f"{normal_rows:,}"
)

print()
print(
    f"Z-score outliers                      : "
    f"{total_z_outliers:,}"
)

print(
    f"IQR outliers                          : "
    f"{total_iqr_outliers:,}"
)

print(
    f"Below 1st percentile                  : "
    f"{total_below_percentile:,}"
)

print(
    f"Above 99th percentile                 : "
    f"{total_above_percentile:,}"
)

print(
    f"Missing values                        : "
    f"{total_missing:,}"
)

print(
    f"Invalid values                        : "
    f"{total_invalid:,}"
)

print()
print("Severity distribution:")

print(
    f"HIGH      : "
    f"{severity_distribution['HIGH']:,}"
)

print(
    f"MEDIUM    : "
    f"{severity_distribution['MEDIUM']:,}"
)

print(
    f"LOW       : "
    f"{severity_distribution['LOW']:,}"
)

print(
    f"NORMAL    : "
    f"{severity_distribution['NORMAL']:,}"
)


# ================================================================
# TOP STATISTICAL ANOMALIES
# ================================================================

print()
print("=" * 70)
print("TOP STATISTICAL ANOMALIES")
print("=" * 70)


top_anomalies = result[
    result["Statistical_Anomaly"]
].copy()


top_anomalies = top_anomalies.sort_values(
    by=[
        "Statistical_Severity",
        "Stat_Total_Quality_Issues",
        "Stat_Outlier_Count",
        "Stat_Missing_Count"
    ],
    ascending=[
        True,
        False,
        False,
        False
    ]
)


display_columns = []

for col in [
    "Plan_ID",
    "Issuer_ID",
    "State",
    "Statistical_Severity",
    "Statistical_Anomaly",
    "Stat_Total_Quality_Issues",
    "Stat_Outlier_Count",
    "Stat_Missing_Count",
    "Stat_Invalid_Count",
    "Stat_Outlier_Features"
]:

    if col in top_anomalies.columns:
        display_columns.append(col)


if len(top_anomalies) > 0:

    print(
        top_anomalies[
            display_columns
        ]
        .head(20)
        .to_string(index=False)
    )

else:

    print()
    print("No statistical anomalies detected.")


# ================================================================
# SAVE CSV
# ================================================================

print()
print("=" * 70)
print("SAVING OUTPUT FILES")
print("=" * 70)


os.makedirs(
    os.path.dirname(OUTPUT_CSV),
    exist_ok=True
)


result.to_csv(
    OUTPUT_CSV,
    index=False
)


# ================================================================
# SAVE JSON
# ================================================================

json_records = result.to_dict(
    orient="records"
)


# Convert NumPy values into standard Python values.
def convert_for_json(value):

    if isinstance(
        value,
        (np.integer,)
    ):
        return int(value)

    if isinstance(
        value,
        (np.floating,)
    ):
        if np.isnan(value):
            return None
        return float(value)

    if isinstance(
        value,
        (np.bool_,)
    ):
        return bool(value)

    if pd.isna(value):
        return None

    return value


clean_json_records = []

for record in json_records:

    clean_record = {}

    for key, value in record.items():

        clean_record[key] = convert_for_json(
            value
        )

    clean_json_records.append(
        clean_record
    )


with open(
    OUTPUT_JSON,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        clean_json_records,
        f,
        indent=2,
        ensure_ascii=False
    )


# ================================================================
# METADATA
# ================================================================

metadata = {

    "dataset": {
        "input_file": INPUT_FILE,
        "rows": total_rows,
        "columns": int(df.shape[1])
    },

    "statistical_analysis": {
        "numeric_columns_found": len(
            numeric_columns
        ),
        "identifier_columns_excluded": len(
            identifier_columns
        ),
        "missing_flag_columns_excluded": len(
            missing_flag_columns
        ),
        "suppressed_columns_excluded": len(
            suppressed_columns
        ),
        "missing_count_columns_excluded": len(
            missing_count_columns
        ),
        "binary_constant_columns_excluded": len(
            binary_constant_columns
        ),
        "low_information_features_excluded": len(
            low_information_features
        ),
        "features_analyzed": n_features
    },

    "thresholds": {
        "z_score": Z_THRESHOLD,
        "lower_percentile": LOW_PERCENTILE,
        "upper_percentile": HIGH_PERCENTILE,
        "iqr_multiplier": 1.5,
        "minimum_non_null_values": MIN_NON_NULL_VALUES,
        "high_outlier_count": HIGH_OUTLIER_COUNT,
        "medium_outlier_count": MEDIUM_OUTLIER_COUNT,
        "high_outlier_ratio": HIGH_OUTLIER_RATIO,
        "medium_outlier_ratio": MEDIUM_OUTLIER_RATIO,
        "missing_low_threshold": MISSING_LOW_THRESHOLD,
        "missing_high_threshold": MISSING_HIGH_THRESHOLD
    },

    "summary": {
        "rows_analyzed": total_rows,
        "features_analyzed": n_features,
        "records_with_anomalies": anomaly_rows,
        "normal_records": normal_rows,
        "z_score_outliers": total_z_outliers,
        "iqr_outliers": total_iqr_outliers,
        "below_1st_percentile": total_below_percentile,
        "above_99th_percentile": total_above_percentile,
        "missing_values": total_missing,
        "invalid_values": total_invalid,
        "severity_distribution": severity_distribution
    },

    "excluded_columns": {
        "identifiers": identifier_columns,
        "missing_flags": missing_flag_columns,
        "suppressed": suppressed_columns,
        "missing_counts": missing_count_columns,
        "binary_or_constant": binary_constant_columns,
        "low_information": low_information_features
    },

    "statistical_features": statistical_features,

    "severity_definition": {
        "HIGH": (
            "Invalid values, or at least "
            f"{HIGH_OUTLIER_COUNT} statistical outliers, "
            "or at least "
            f"{HIGH_OUTLIER_RATIO * 100:.1f}% "
            "of statistical features are outliers."
        ),
        "MEDIUM": (
            "At least "
            f"{MEDIUM_OUTLIER_COUNT} statistical outliers, "
            "or at least "
            f"{MEDIUM_OUTLIER_RATIO * 100:.1f}% "
            "of statistical features are outliers."
        ),
        "LOW": (
            "One statistical outlier or substantial "
            "missingness without stronger statistical evidence."
        ),
        "NORMAL": (
            "No statistical or invalid-value anomaly detected."
        )
    }

}


with open(
    OUTPUT_METADATA,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        metadata,
        f,
        indent=2,
        ensure_ascii=False
    )


# ================================================================
# FINAL OUTPUT
# ================================================================

print()
print("CSV:")
print(OUTPUT_CSV)

print()
print("JSON:")
print(OUTPUT_JSON)

print()
print("Metadata:")
print(OUTPUT_METADATA)

print()
print("=" * 70)
print("STATISTICAL QUALITY CHECK COMPLETED")
print("=" * 70)