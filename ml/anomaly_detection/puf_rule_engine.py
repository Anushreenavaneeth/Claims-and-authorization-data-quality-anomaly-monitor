import pandas as pd
import os

print("=" * 70)
print("PUF RULE-BASED ANOMALY DETECTION")
print("=" * 70)

# ---------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------

INPUT_FILE = "data/processed/tc_puf_cleaned.csv"
OUTPUT_FILE = "data/anomalies/tc_puf_rule_results.csv"

print("\nLoading PUF data...")

df = pd.read_csv(INPUT_FILE)

print(f"Records loaded: {len(df)}")

# ---------------------------------------------------------
# 2. HELPER FUNCTION
# ---------------------------------------------------------

def safe_numeric(column):
    return pd.to_numeric(df[column], errors="coerce")


# ---------------------------------------------------------
# 3. INITIALIZE RULE OUTPUT COLUMNS
# ---------------------------------------------------------

df["rule_anomaly"] = False
df["rule_name"] = ""
df["rule_reason"] = ""
df["rule_severity"] = ""

# ---------------------------------------------------------
# 4. RULE 1
# Denied claims cannot exceed received claims
# ---------------------------------------------------------

received_in = safe_numeric(
    "Issuer_Claims_Received_In_Network"
)

denied_in = safe_numeric(
    "Issuer_Claims_Denied_In_Network"
)

mask = (
    received_in.notna()
    & denied_in.notna()
    & (denied_in > received_in)
)

df.loc[mask, "rule_anomaly"] = True
df.loc[mask, "rule_name"] = "DENIED_GT_RECEIVED_IN_NETWORK"
df.loc[mask, "rule_reason"] = (
    "In-network denied claims exceed in-network received claims"
)
df.loc[mask, "rule_severity"] = "HIGH"


# ---------------------------------------------------------
# 5. RULE 2
# Out-of-network denied claims cannot exceed received claims
# ---------------------------------------------------------

received_out = safe_numeric(
    "Issuer_Claims_Received_Out_of_Network"
)

denied_out = safe_numeric(
    "Issuer_Claims_Denied_Out_of_Network"
)

mask = (
    received_out.notna()
    & denied_out.notna()
    & (denied_out > received_out)
)

df.loc[mask, "rule_anomaly"] = True

# Don't overwrite an existing rule
empty_rule = df["rule_name"] == ""

df.loc[mask & empty_rule, "rule_name"] = (
    "DENIED_GT_RECEIVED_OUT_NETWORK"
)

df.loc[
    mask & empty_rule,
    "rule_reason"
] = (
    "Out-of-network denied claims exceed "
    "out-of-network received claims"
)

df.loc[
    mask & empty_rule,
    "rule_severity"
] = "HIGH"


# ---------------------------------------------------------
# 6. RULE 3
# Internal appeals overturned cannot exceed appeals filed
# ---------------------------------------------------------

internal_filed = safe_numeric(
    "Issuer_Internal_Appeals_Filed"
)

internal_overturned = safe_numeric(
    "Issuer_Number_Internal_Appeals_Overturned"
)

mask = (
    internal_filed.notna()
    & internal_overturned.notna()
    & (internal_overturned > internal_filed)
)

df.loc[mask, "rule_anomaly"] = True

empty_rule = df["rule_name"] == ""

df.loc[
    mask & empty_rule,
    "rule_name"
] = "OVERTURNED_GT_INTERNAL_APPEALS"

df.loc[
    mask & empty_rule,
    "rule_reason"
] = (
    "Number of overturned internal appeals "
    "exceeds internal appeals filed"
)

df.loc[
    mask & empty_rule,
    "rule_severity"
] = "HIGH"


# ---------------------------------------------------------
# 7. RULE 4
# External appeals overturned cannot exceed appeals filed
# ---------------------------------------------------------

external_filed = safe_numeric(
    "Issuer_External_Appeals_Filed"
)

external_overturned = safe_numeric(
    "Issuer_Number_External_Appeals_Overturned"
)

mask = (
    external_filed.notna()
    & external_overturned.notna()
    & (external_overturned > external_filed)
)

df.loc[mask, "rule_anomaly"] = True

empty_rule = df["rule_name"] == ""

df.loc[
    mask & empty_rule,
    "rule_name"
] = "OVERTURNED_GT_EXTERNAL_APPEALS"

df.loc[
    mask & empty_rule,
    "rule_reason"
] = (
    "Number of overturned external appeals "
    "exceeds external appeals filed"
)

df.loc[
    mask & empty_rule,
    "rule_severity"
] = "HIGH"


# ---------------------------------------------------------
# 8. RULE 5
# Internal appeal overturn percentage
# must be between 0 and 100
# ---------------------------------------------------------

internal_percentage = safe_numeric(
    "Issuer_Percent_Internal_Appeals_Overturned"
)

mask = (
    internal_percentage.notna()
    & (
        (internal_percentage < 0)
        | (internal_percentage > 100)
    )
)

df.loc[mask, "rule_anomaly"] = True

empty_rule = df["rule_name"] == ""

df.loc[
    mask & empty_rule,
    "rule_name"
] = "INVALID_INTERNAL_APPEAL_PERCENTAGE"

df.loc[
    mask & empty_rule,
    "rule_reason"
] = (
    "Internal appeal overturn percentage "
    "is outside the valid range of 0 to 100"
)

df.loc[
    mask & empty_rule,
    "rule_severity"
] = "HIGH"


# ---------------------------------------------------------
# 9. RULE 6
# External appeal overturn percentage
# must be between 0 and 100
# ---------------------------------------------------------

external_percentage = safe_numeric(
    "Issuer_Percent_External_Appeals_Overturned"
)

mask = (
    external_percentage.notna()
    & (
        (external_percentage < 0)
        | (external_percentage > 100)
    )
)

df.loc[mask, "rule_anomaly"] = True

empty_rule = df["rule_name"] == ""

df.loc[
    mask & empty_rule,
    "rule_name"
] = "INVALID_EXTERNAL_APPEAL_PERCENTAGE"

df.loc[
    mask & empty_rule,
    "rule_reason"
] = (
    "External appeal overturn percentage "
    "is outside the valid range of 0 to 100"
)

df.loc[
    mask & empty_rule,
    "rule_severity"
] = "HIGH"


# ---------------------------------------------------------
# 10. RULE 7
# Resubmitted claims cannot exceed received claims
# ---------------------------------------------------------

resubmitted_in = safe_numeric(
    "Issuer_Claims_Resubmitted_In_Network"
)

mask = (
    received_in.notna()
    & resubmitted_in.notna()
    & (resubmitted_in > received_in)
)

df.loc[mask, "rule_anomaly"] = True

empty_rule = df["rule_name"] == ""

df.loc[
    mask & empty_rule,
    "rule_name"
] = "RESUBMITTED_GT_RECEIVED_IN_NETWORK"

df.loc[
    mask & empty_rule,
    "rule_reason"
] = (
    "In-network resubmitted claims exceed "
    "in-network received claims"
)

df.loc[
    mask & empty_rule,
    "rule_severity"
] = "MEDIUM"


# ---------------------------------------------------------
# 11. RULE 8
# Out-of-network resubmitted claims cannot exceed received
# ---------------------------------------------------------

resubmitted_out = safe_numeric(
    "Issuer_Claims_Resubmitted_Out_of_Network"
)

mask = (
    received_out.notna()
    & resubmitted_out.notna()
    & (resubmitted_out > received_out)
)

df.loc[mask, "rule_anomaly"] = True

empty_rule = df["rule_name"] == ""

df.loc[
    mask & empty_rule,
    "rule_name"
] = "RESUBMITTED_GT_RECEIVED_OUT_NETWORK"

df.loc[
    mask & empty_rule,
    "rule_reason"
] = (
    "Out-of-network resubmitted claims exceed "
    "out-of-network received claims"
)

df.loc[
    mask & empty_rule,
    "rule_severity"
] = "MEDIUM"


# ---------------------------------------------------------
# 12. RULE 9
# Disenrollment greater than enrollment
# ---------------------------------------------------------

enrollment = safe_numeric(
    "Average Monthly Enrollment"
)

disenrollment = safe_numeric(
    "Average Monthly Disenrollment"
)

mask = (
    enrollment.notna()
    & disenrollment.notna()
    & (disenrollment > enrollment)
)

df.loc[mask, "rule_anomaly"] = True

empty_rule = df["rule_name"] == ""

df.loc[
    mask & empty_rule,
    "rule_name"
] = "DISENROLLMENT_GT_ENROLLMENT"

df.loc[
    mask & empty_rule,
    "rule_reason"
] = (
    "Average monthly disenrollment exceeds "
    "average monthly enrollment"
)

df.loc[
    mask & empty_rule,
    "rule_severity"
] = "MEDIUM"


# ---------------------------------------------------------
# 13. SAVE RESULTS
# ---------------------------------------------------------

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ---------------------------------------------------------
# 14. RESULTS
# ---------------------------------------------------------

total = len(df)

anomalies = int(
    df["rule_anomaly"].sum()
)

normal = total - anomalies

percentage = (
    anomalies / total * 100
    if total > 0
    else 0
)

print("\n" + "=" * 70)
print("RULE DETECTION COMPLETED")
print("=" * 70)

print(f"Total records       : {total}")
print(f"Rule anomalies      : {anomalies}")
print(f"Normal records      : {normal}")
print(f"Anomaly percentage  : {percentage:.2f}%")

print("\nRule breakdown:")

print(
    df.loc[
        df["rule_anomaly"],
        "rule_name"
    ].value_counts().to_string()
)

print("\nSample rule anomalies:")

print(
    df.loc[
        df["rule_anomaly"],
        [
            "Plan_ID",
            "rule_name",
            "rule_reason",
            "rule_severity"
        ]
    ]
    .head(10)
    .to_string(index=False)
)

print("\nOutput saved to:")
print(os.path.abspath(OUTPUT_FILE))

print("=" * 70)