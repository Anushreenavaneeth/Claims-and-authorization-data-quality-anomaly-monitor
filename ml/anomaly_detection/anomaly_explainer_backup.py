import pandas as pd
import os

print("=" * 70)
print("TC-PUF ANOMALY EXPLAINER")
print("=" * 70)

# ============================================================
# 1. FILE PATHS
# ============================================================

ANOMALY_FILE = "data/anomalies/tc_puf_anomalies.csv"
RULE_FILE = "data/anomalies/tc_puf_rule_results.csv"
OUTPUT_FILE = "data/anomalies/tc_puf_explained.csv"

# ============================================================
# 2. LOAD DATA
# ============================================================

print("\nLoading anomaly results...")

df = pd.read_csv(ANOMALY_FILE)
rules = pd.read_csv(RULE_FILE)

print(f"Anomaly records loaded: {len(df)}")
print(f"Rule records loaded   : {len(rules)}")

# ============================================================
# 3. KEEP ONLY RULE INFORMATION NEEDED
# ============================================================

rule_columns = [
    "Plan_ID",
    "rule_anomaly",
    "rule_name",
    "rule_reason",
    "rule_severity"
]

# Make sure required columns exist
available_rule_columns = [
    col for col in rule_columns
    if col in rules.columns
]

rules = rules[available_rule_columns].copy()

# ============================================================
# 4. MERGE RULE RESULTS WITH ML RESULTS
# ============================================================

print("\nCombining ML and rule-based results...")

# Remove existing rule columns if they already exist
for col in [
    "rule_anomaly",
    "rule_name",
    "rule_reason",
    "rule_severity"
]:
    if col in df.columns:
        df.drop(columns=[col], inplace=True)

df = df.merge(
    rules,
    on="Plan_ID",
    how="left"
)

# Fill missing rule results
df["rule_anomaly"] = df["rule_anomaly"].fillna(False)

df["rule_name"] = df["rule_name"].fillna("NONE")

df["rule_reason"] = df["rule_reason"].fillna("No rule violation detected")

df["rule_severity"] = df["rule_severity"].fillna("NORMAL")

# ============================================================
# 5. MAKE SURE ML COLUMNS EXIST
# ============================================================

if "ml_anomaly" not in df.columns:

    if "ml_prediction" in df.columns:
        df["ml_anomaly"] = df["ml_prediction"] == -1

    else:
        df["ml_anomaly"] = False


if "ml_anomaly_score" not in df.columns:

    df["ml_anomaly_score"] = 0.0


# ============================================================
# 6. FINAL ANOMALY
# ============================================================

df["final_anomaly"] = (
    df["rule_anomaly"] |
    df["ml_anomaly"]
)

# ============================================================
# 7. DETERMINE ANOMALY TYPE
# ============================================================

def get_anomaly_type(row):

    rule = bool(row["rule_anomaly"])
    ml = bool(row["ml_anomaly"])

    if rule and ml:
        return "RULE + ML"

    elif rule:
        return "RULE"

    elif ml:
        return "ML"

    else:
        return "NORMAL"


df["anomaly_type"] = df.apply(
    get_anomaly_type,
    axis=1
)

# ============================================================
# 8. DETERMINE SEVERITY
# ============================================================

def get_severity(row):

    anomaly_type = row["anomaly_type"]

    # Rule-based anomalies are deterministic.
    if anomaly_type == "RULE + ML":
        return "HIGH"

    elif anomaly_type == "RULE":

        if row["rule_severity"] == "HIGH":
            return "HIGH"

        elif row["rule_severity"] == "MEDIUM":
            return "MEDIUM"

        else:
            return "LOW"

    elif anomaly_type == "ML":
        return "MEDIUM"

    return "NORMAL"


df["severity"] = df.apply(
    get_severity,
    axis=1
)

# ============================================================
# 9. GENERATE EXPLANATION
# ============================================================

def generate_explanation(row):

    anomaly_type = row["anomaly_type"]

    # -----------------------------
    # NORMAL
    # -----------------------------
    if anomaly_type == "NORMAL":

        return (
            "No rule violation or significant ML anomaly "
            "was detected for this record."
        )

    # -----------------------------
    # RULE
    # -----------------------------
    elif anomaly_type == "RULE":

        return (
            f"Rule-based validation detected a data-quality "
            f"issue: {row['rule_reason']}."
        )

    # -----------------------------
    # ML
    # -----------------------------
    elif anomaly_type == "ML":

        return (
            "The record shows an unusual combination of "
            "claims, denials, resubmissions, appeals, or "
            "enrollment-related values compared with other "
            "records in the dataset."
        )

    # -----------------------------
    # RULE + ML
    # -----------------------------
    elif anomaly_type == "RULE + ML":

        return (
            f"Both deterministic rule validation and the ML "
            f"model identified this record as anomalous. "
            f"Rule finding: {row['rule_reason']}."
        )

    return "Anomaly detected."


df["explanation"] = df.apply(
    generate_explanation,
    axis=1
)

# ============================================================
# 10. LIKELY CAUSE
# ============================================================

def get_likely_cause(row):

    anomaly_type = row["anomaly_type"]

    if anomaly_type == "NORMAL":

        return "No anomaly detected."

    if anomaly_type == "RULE":

        rule_name = row["rule_name"]

        if rule_name == "DENIED_GT_RECEIVED_OUT_NETWORK":

            return (
                "Possible data-entry, aggregation, or reporting "
                "issue because denied out-of-network claims "
                "exceed received out-of-network claims."
            )

        elif rule_name == "OVERTURNED_GT_INTERNAL_APPEALS":

            return (
                "Possible data inconsistency because the number "
                "of overturned appeals exceeds the number of "
                "internal appeals filed."
            )

        elif rule_name == "INVALID_INTERNAL_APPEAL_PERCENTAGE":

            return (
                "Possible percentage calculation or source-data "
                "quality issue."
            )

        elif rule_name == "DENIAL_REASON_GT_TOTAL":

            return (
                "Possible double counting or incorrect aggregation "
                "of individual denial reasons."
            )

        return (
            "Possible data-entry, aggregation, transformation, "
            "or reporting issue."
        )

    if anomaly_type == "ML":

        return (
            "The record differs significantly from normal "
            "patterns in the dataset. Possible causes include "
            "unusual reporting volume, data-entry errors, "
            "missing values, or an unexpected operational event."
        )

    if anomaly_type == "RULE + ML":

        return (
            "A deterministic data-quality violation is present "
            "and the record also differs from normal ML patterns. "
            "This increases confidence that the record requires "
            "validation."
        )

    return "Unknown cause."


df["likely_cause"] = df.apply(
    get_likely_cause,
    axis=1
)

# ============================================================
# 11. RECOMMENDED FIX
# ============================================================

def get_recommended_fix(row):

    anomaly_type = row["anomaly_type"]

    if anomaly_type == "NORMAL":

        return "No action required."

    rule_name = row["rule_name"]

    if rule_name == "DENIED_GT_RECEIVED_OUT_NETWORK":

        return (
            "Compare received and denied out-of-network claims "
            "with the source claims system. Check for duplicate "
            "records, aggregation errors, or incorrect claim "
            "status mapping."
        )

    elif rule_name == "OVERTURNED_GT_INTERNAL_APPEALS":

        return (
            "Verify the number of internal appeals filed and "
            "overturned against the source appeals system. "
            "Check for duplicate or incorrectly mapped appeal records."
        )

    elif rule_name == "INVALID_INTERNAL_APPEAL_PERCENTAGE":

        return (
            "Recalculate the internal appeal overturn percentage "
            "using the correct filed and overturned appeal counts."
        )

    elif rule_name == "DENIAL_REASON_GT_TOTAL":

        return (
            "Check whether denial reasons are being double-counted "
            "and verify that the sum of denial categories does not "
            "exceed the total denied claims."
        )

    elif anomaly_type == "ML":

        return (
            "Compare the record with similar plans and historical "
            "records, then validate unusual fields against the "
            "source system."
        )

    elif anomaly_type == "RULE + ML":

        return (
            "Prioritize manual validation. Check the violated "
            "business rule against the source system and investigate "
            "the unusual ML pattern."
        )

    return "Review the record against the source system."


df["recommended_fix"] = df.apply(
    get_recommended_fix,
    axis=1
)

# ============================================================
# 12. SAVE OUTPUT
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
# 13. SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("ANOMALY EXPLANATION COMPLETED")
print("=" * 70)

print(f"\nTotal records       : {len(df)}")
print(
    f"Rule anomalies      : "
    f"{df['rule_anomaly'].sum()}"
)
print(
    f"ML anomalies        : "
    f"{df['ml_anomaly'].sum()}"
)
print(
    f"Final anomalies     : "
    f"{df['final_anomaly'].sum()}"
)

print("\nAnomaly types:")

print(
    df["anomaly_type"]
    .value_counts()
    .to_string()
)

print("\nSeverity:")

print(
    df["severity"]
    .value_counts()
    .to_string()
)

print("\nSample explained anomalies:")

sample_columns = [
    "Plan_ID",
    "anomaly_type",
    "severity",
    "rule_name",
    "rule_reason",
    "explanation",
    "likely_cause",
    "recommended_fix"
]

print(
    df[df["final_anomaly"] == True]
    [sample_columns]
    .head(10)
    .to_string(index=False)
)

print("\nOutput saved to:")
print(os.path.abspath(OUTPUT_FILE))

print("=" * 70)