import os
import numpy as np
import pandas as pd


# ============================================================
# TC-PUF RULE-BASED ANOMALY DETECTION
# ============================================================

print("=" * 80)
print("TC-PUF RULE-BASED DATA QUALITY ENGINE")
print("=" * 80)


# ============================================================
# 1. FILE CONFIGURATION
# ============================================================

# IMPORTANT:
# Rule engine now consumes the FEATURE-ENGINEERED dataset.
INPUT_FILE = "data/processed/tc_puf_feature_engineered.csv"

OUTPUT_FILE = "data/anomalies/tc_puf_rule_results.csv"


# ============================================================
# 2. LOAD DATA
# ============================================================

print("\nLoading feature-engineered dataset...")

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"Input file not found:\n{INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

print(f"Records loaded : {len(df)}")
print(f"Columns loaded : {len(df.columns)}")


if len(df) == 0:
    raise ValueError("Input dataset contains zero records.")


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def numeric_column(column_name):
    """
    Convert a column to numeric safely.

    Values such as:
        *
        **
        text
        empty strings

    become NaN instead of causing an error.
    """

    if column_name not in df.columns:
        return pd.Series(
            np.nan,
            index=df.index,
            dtype="float64"
        )

    return pd.to_numeric(
        df[column_name],
        errors="coerce"
    )


def boolean_column(column_name):
    """
    Convert feature-engineered anomaly flags into
    a reliable boolean Series.

    Handles:
        True / False
        1 / 0
        yes / no
        strings
        NaN
    """

    if column_name not in df.columns:
        return pd.Series(
            False,
            index=df.index,
            dtype=bool
        )

    values = df[column_name]

    if values.dtype == bool:
        return values.fillna(False)

    normalized = (
        values
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return normalized.isin(
        ["1", "true", "yes", "y"]
    )


def add_rule(
    mask,
    rule_name,
    rule_reason,
    severity
):
    """
    Add a rule violation to the dataset.

    Multiple rules can apply to the same record.
    """

    mask = (
        mask
        .fillna(False)
        .astype(bool)
    )

    if not mask.any():
        return

    df.loc[
        mask,
        "rule_anomaly"
    ] = True

    df.loc[
        mask,
        "rule_count"
    ] += 1

    # --------------------------------------------------------
    # Rule name
    # --------------------------------------------------------

    current_names = (
        df.loc[mask, "_rule_names"]
        .fillna("")
        .astype(str)
    )

    df.loc[mask, "_rule_names"] = [
        f"{old};{rule_name}" if old else rule_name
        for old in current_names
    ]

    # --------------------------------------------------------
    # Rule reason
    # --------------------------------------------------------

    current_reasons = (
        df.loc[mask, "_rule_reasons"]
        .fillna("")
        .astype(str)
    )

    df.loc[mask, "_rule_reasons"] = [
        f"{old};{rule_reason}" if old else rule_reason
        for old in current_reasons
    ]

    # --------------------------------------------------------
    # Severity
    # --------------------------------------------------------

    current_severity = (
        df.loc[mask, "_rule_severities"]
        .fillna("")
        .astype(str)
    )

    df.loc[mask, "_rule_severities"] = [
        f"{old};{severity}" if old else severity
        for old in current_severity
    ]


# ============================================================
# 4. INITIALIZE RULE OUTPUT COLUMNS
# ============================================================

df["rule_anomaly"] = False

df["rule_count"] = 0

df["rule_name"] = "NONE"

df["rule_reason"] = "No rule violation detected"

df["rule_severity"] = "NONE"


# Temporary columns used internally
df["_rule_names"] = ""
df["_rule_reasons"] = ""
df["_rule_severities"] = ""


# ============================================================
# 5. RULE 1
# NEGATIVE CLAIM COUNTS
#
# A claim count cannot logically be negative.
#
# Severity: CRITICAL
# ============================================================

claim_count_columns = [

    "Issuer_Claims_Received_Out_of_Network",
    "Issuer_Claims_Received_In_Network",

    "Issuer_Claims_Denied_Out_of_Network",
    "Issuer_Claims_Denied_In_Network",

    "Issuer_Claims_Resubmitted_Out_of_Network",
    "Issuer_Claims_Resubmitted_In_Network",

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

    "Plan_Number_Claims_Denied_Other"
]


for column in claim_count_columns:

    if column not in df.columns:
        continue

    values = numeric_column(column)

    add_rule(
        values < 0,

        "NEGATIVE_CLAIM_COUNT",

        f"{column} contains a negative value",

        "CRITICAL"
    )


# ============================================================
# 6. RULE 2
# PLAN DENIED > PLAN RECEIVED
#
# This uses the FEATURE-ENGINEERED flag.
#
# Severity: CRITICAL
# ============================================================

add_rule(
    boolean_column(
        "Plan_Denied_Exceeds_Received"
    ),

    "PLAN_DENIED_GT_RECEIVED",

    "Plan denied claims exceed plan received claims",

    "CRITICAL"
)


# ============================================================
# 7. RULE 3
# ISSUER DENIED > ISSUER RECEIVED
# ============================================================

add_rule(
    boolean_column(
        "Issuer_Denied_Exceeds_Received"
    ),

    "ISSUER_DENIED_GT_RECEIVED",

    "Issuer denied claims exceed issuer received claims",

    "CRITICAL"
)


# ============================================================
# 8. RULE 4
# PLAN RESUBMITTED > PLAN RECEIVED
# ============================================================

add_rule(
    boolean_column(
        "Plan_Resubmitted_Exceeds_Received"
    ),

    "PLAN_RESUBMITTED_GT_RECEIVED",

    "Plan resubmitted claims exceed plan received claims",

    "CRITICAL"
)


# ============================================================
# 9. RULE 5
# ISSUER RESUBMITTED > ISSUER RECEIVED
# ============================================================

add_rule(
    boolean_column(
        "Issuer_Resubmitted_Exceeds_Received"
    ),

    "ISSUER_RESUBMITTED_GT_RECEIVED",

    "Issuer resubmitted claims exceed issuer received claims",

    "CRITICAL"
)


# ============================================================
# 10. RULE 6
# INTERNAL APPEALS
#
# Overturned appeals cannot exceed appeals filed.
# ============================================================

add_rule(
    boolean_column(
        "Internal_Overturned_Exceeds_Appeals"
    ),

    "INTERNAL_OVERTURNED_GT_APPEALS",

    "Internal overturned appeals exceed internal appeals filed",

    "CRITICAL"
)


# ============================================================
# 11. RULE 7
# EXTERNAL APPEALS
# ============================================================

add_rule(
    boolean_column(
        "External_Overturned_Exceeds_Appeals"
    ),

    "EXTERNAL_OVERTURNED_GT_APPEALS",

    "External overturned appeals exceed external appeals filed",

    "CRITICAL"
)


# ============================================================
# 12. RULE 8
# INTERNAL APPEAL PERCENTAGE
#
# Valid range = 0 to 100.
# ============================================================

internal_percentage = numeric_column(
    "Issuer_Percent_Internal_Appeals_Overturned"
)

add_rule(
    internal_percentage.notna()
    & (
        (internal_percentage < 0)
        | (internal_percentage > 100)
    ),

    "INVALID_INTERNAL_APPEAL_PERCENTAGE",

    "Internal appeal overturn percentage is outside 0 to 100",

    "CRITICAL"
)


# ============================================================
# 13. RULE 9
# EXTERNAL APPEAL PERCENTAGE
# ============================================================

external_percentage = numeric_column(
    "Issuer_Percent_External_Appeals_Overturned"
)

add_rule(
    external_percentage.notna()
    & (
        (external_percentage < 0)
        | (external_percentage > 100)
    ),

    "INVALID_EXTERNAL_APPEAL_PERCENTAGE",

    "External appeal overturn percentage is outside 0 to 100",

    "CRITICAL"
)


# ============================================================
# 14. RULE 10
# NEGATIVE ENROLLMENT
# ============================================================

enrollment = numeric_column(
    "Average Monthly Enrollment"
)

add_rule(
    enrollment.notna()
    & (enrollment < 0),

    "NEGATIVE_ENROLLMENT",

    "Average monthly enrollment is negative",

    "CRITICAL"
)


# ============================================================
# 15. RULE 11
# NEGATIVE DISENROLLMENT
# ============================================================

disenrollment = numeric_column(
    "Average Monthly Disenrollment"
)

add_rule(
    disenrollment.notna()
    & (disenrollment < 0),

    "NEGATIVE_DISENROLLMENT",

    "Average monthly disenrollment is negative",

    "CRITICAL"
)


# ============================================================
# 16. RULE 12
# DISENROLLMENT > ENROLLMENT
#
# This is a logical consistency issue.
#
# Severity: HIGH
# ============================================================

add_rule(
    enrollment.notna()
    & disenrollment.notna()
    & (disenrollment > enrollment),

    "DISENROLLMENT_GT_ENROLLMENT",

    "Average monthly disenrollment exceeds average monthly enrollment",

    "HIGH"
)


# ============================================================
# 17. RULE 13
# EXCESSIVE IMPORTANT MISSINGNESS
#
# IMPORTANT:
# A single missing field is NOT an anomaly.
#
# We only flag records where >= 50% of important
# fields are missing.
#
# Severity: MEDIUM
# ============================================================

if "Important_Missing_Rate" in df.columns:

    missing_rate = numeric_column(
        "Important_Missing_Rate"
    )

    add_rule(
        missing_rate.notna()
        & (missing_rate >= 0.50),

        "EXCESSIVE_IMPORTANT_MISSINGNESS",

        "At least 50% of important fields are missing",

        "MEDIUM"
    )


# ============================================================
# 18. RULE 14
# EXCESSIVE SUPPRESSED / NON-NUMERIC VALUES
#
# We do not treat every '*' or '**' as an anomaly.
#
# Only unusually high suppression counts are flagged.
# ============================================================

if "Suppressed_or_NonNumeric_Count" in df.columns:

    suppressed_count = numeric_column(
        "Suppressed_or_NonNumeric_Count"
    )

    add_rule(
        suppressed_count.notna()
        & (suppressed_count >= 10),

        "EXCESSIVE_SUPPRESSED_VALUES",

        "Record contains 10 or more suppressed or non-numeric values",

        "MEDIUM"
    )


# ============================================================
# 19. RULE 15
# PLAN/ISSUER RECEIVED-DENIED DIFFERENCE
#
# This is an OPTIONAL consistency rule.
#
# We only activate it when both plan and issuer values
# are available and the difference is extreme.
#
# This is NOT treated as a hard business violation.
# Statistical/ML models are better suited for unusual
# differences.
#
# Therefore this rule is intentionally NOT enabled here.
# ============================================================


# ============================================================
# 20. DETERMINE HIGHEST SEVERITY
# ============================================================

severity_priority = {
    "NONE": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CRITICAL": 3
}


def get_highest_severity(value):

    if not value:
        return "NONE"

    values = [
        item.strip()
        for item in str(value).split(";")
        if item.strip()
    ]

    if not values:
        return "NONE"

    return max(
        values,
        key=lambda x: severity_priority.get(
            x,
            0
        )
    )


# ============================================================
# 21. FINALIZE RULE COLUMNS
# ============================================================

df["rule_name"] = (
    df["_rule_names"]
    .replace("", "NONE")
)

df["rule_reason"] = (
    df["_rule_reasons"]
    .replace(
        "",
        "No rule violation detected"
    )
)

df["rule_severity"] = (
    df["_rule_severities"]
    .apply(get_highest_severity)
)


# ============================================================
# 22. CLEAN TEMPORARY COLUMNS
# ============================================================

df.drop(
    columns=[
        "_rule_names",
        "_rule_reasons",
        "_rule_severities"
    ],
    inplace=True
)


# ============================================================
# 23. FINAL SAFETY CHECKS
# ============================================================

# rule_anomaly must agree with rule_count
df["rule_anomaly"] = (
    df["rule_count"] > 0
)

# Make sure severity is NONE when there is no rule violation
df.loc[
    ~df["rule_anomaly"],
    "rule_severity"
] = "NONE"


# ============================================================
# 24. SAVE RESULTS
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 25. SUMMARY
# ============================================================

total_records = len(df)

rule_anomalies = int(
    df["rule_anomaly"].sum()
)

normal_records = (
    total_records - rule_anomalies
)

anomaly_percentage = (
    rule_anomalies / total_records * 100
)


print("\n" + "=" * 80)
print("RULE DETECTION COMPLETED")
print("=" * 80)

print(
    f"Total records       : {total_records}"
)

print(
    f"Rule anomalies      : {rule_anomalies}"
)

print(
    f"Normal records      : {normal_records}"
)

print(
    f"Anomaly percentage  : {anomaly_percentage:.2f}%"
)


# ============================================================
# 26. SEVERITY BREAKDOWN
# ============================================================

print("\nSeverity breakdown:")

print(
    df["rule_severity"]
    .value_counts()
    .to_string()
)


# ============================================================
# 27. RULE COUNT DISTRIBUTION
# ============================================================

print("\nRule count distribution:")

print(
    df["rule_count"]
    .describe()
    .to_string()
)


# ============================================================
# 28. RULE BREAKDOWN
# ============================================================

print("\nRule breakdown:")

rule_breakdown = (
    df.loc[
        df["rule_anomaly"],
        "rule_name"
    ]
    .str.split(";")
    .explode()
    .value_counts()
)

if len(rule_breakdown) > 0:
    print(
        rule_breakdown.to_string()
    )
else:
    print("No rule violations detected.")


# ============================================================
# 29. SAMPLE ANOMALIES
# ============================================================

print("\nSample rule anomalies:")

sample_columns = [
    "Plan_ID",
    "rule_anomaly",
    "rule_count",
    "rule_name",
    "rule_severity",
    "rule_reason"
]

sample_columns = [
    column
    for column in sample_columns
    if column in df.columns
]

sample = df.loc[
    df["rule_anomaly"],
    sample_columns
].head(10)

if len(sample) > 0:
    print(
        sample.to_string(
            index=False
        )
    )
else:
    print("No rule anomalies found.")


# ============================================================
# 30. OUTPUT LOCATION
# ============================================================

print("\nOutput saved to:")

print(
    os.path.abspath(
        OUTPUT_FILE
    )
)

print("\n" + "=" * 80)
print("TC-PUF RULE ENGINE FINISHED")
print("=" * 80)