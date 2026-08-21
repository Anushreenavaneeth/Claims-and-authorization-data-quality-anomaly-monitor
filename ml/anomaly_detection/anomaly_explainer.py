import pandas as pd
import numpy as np
import os

print("=" * 70)
print("TC-PUF ANOMALY EXPLAINER")
print("=" * 70)

# ============================================================
# FILES
# ============================================================

ANOMALY_FILE = "data/anomalies/tc_puf_anomalies.csv"
RULE_FILE = "data/anomalies/tc_puf_rule_results.csv"
OUTPUT_FILE = "data/anomalies/tc_puf_explained.csv"

# Original cleaned PUF data
CLEANED_FILE = "data/processed/tc_puf_cleaned.csv"

# ============================================================
# 1. LOAD DATA
# ============================================================

print("\nLoading anomaly results...")

df_anomaly = pd.read_csv(ANOMALY_FILE)
df_rule = pd.read_csv(RULE_FILE)

print(f"Anomaly records loaded: {len(df_anomaly)}")
print(f"Rule records loaded   : {len(df_rule)}")

# ============================================================
# 2. MERGE RULE INFORMATION
# ============================================================

print("\nCombining ML and rule-based results...")

rule_columns = [
    "Plan_ID",
    "rule_anomaly",
    "rule_name",
    "rule_reason",
    "rule_severity"
]

rule_columns = [
    col for col in rule_columns
    if col in df_rule.columns
]

df_rule_small = df_rule[rule_columns].copy()

df = df_anomaly.drop(
    columns=[
        "rule_anomaly",
        "rule_name",
        "rule_reason",
        "rule_severity"
    ],
    errors="ignore"
)

df = df.merge(
    df_rule_small,
    on="Plan_ID",
    how="left"
)

# ============================================================
# 3. NORMALIZE RULE VALUES
# ============================================================

df["rule_anomaly"] = (
    df["rule_anomaly"]
    .fillna(False)
    .astype(bool)
)

df["rule_name"] = df["rule_name"].fillna("NONE")
df["rule_reason"] = df["rule_reason"].fillna(
    "No rule violation detected"
)

# ============================================================
# 4. LOAD CLEANED DATA FOR ML EXPLANATION
# ============================================================

print("\nLoading cleaned PUF data for field-level explanation...")

if os.path.exists(CLEANED_FILE):

    df_clean = pd.read_csv(CLEANED_FILE)

    print(f"Cleaned dataset loaded: {df_clean.shape}")

else:

    print("WARNING: Cleaned dataset not found.")
    df_clean = df.copy()

# ============================================================
# 5. NUMERIC PUF FEATURES
# ============================================================

EXPLANATION_FEATURES = [

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
    "Average Monthly Disenrollment"
]

# Keep only columns actually present
EXPLANATION_FEATURES = [
    col for col in EXPLANATION_FEATURES
    if col in df_clean.columns
]

print(
    f"Explanation features available: "
    f"{len(EXPLANATION_FEATURES)}"
)

# ============================================================
# 6. CREATE NUMERIC DATA
# ============================================================

numeric_data = df_clean[EXPLANATION_FEATURES].copy()

for col in EXPLANATION_FEATURES:
    numeric_data[col] = pd.to_numeric(
        numeric_data[col],
        errors="coerce"
    )

# ============================================================
# 7. CALCULATE NORMAL BASELINE
# ============================================================

means = numeric_data.mean()

stds = numeric_data.std()

# Avoid division by zero
stds = stds.replace(0, np.nan)

# ============================================================
# 8. FIELD LABELS
# ============================================================

FIELD_LABELS = {

    "Issuer_Claims_Received_Out_of_Network":
        "out-of-network claims received",

    "Issuer_Claims_Received_In_Network":
        "in-network claims received",

    "Issuer_Claims_Denied_Out_of_Network":
        "out-of-network denied claims",

    "Issuer_Claims_Denied_In_Network":
        "in-network denied claims",

    "Issuer_Claims_Resubmitted_Out_of_Network":
        "out-of-network resubmitted claims",

    "Issuer_Claims_Resubmitted_In_Network":
        "in-network resubmitted claims",

    "Issuer_Internal_Appeals_Filed":
        "internal appeals filed",

    "Issuer_Number_Internal_Appeals_Overturned":
        "internal appeals overturned",

    "Issuer_Percent_Internal_Appeals_Overturned":
        "internal appeal overturn percentage",

    "Issuer_External_Appeals_Filed":
        "external appeals filed",

    "Issuer_Number_External_Appeals_Overturned":
        "external appeals overturned",

    "Issuer_Percent_External_Appeals_Overturned":
        "external appeal overturn percentage",

    "Plan_Number_Claims_Received_Out_of_Network":
        "plan-level out-of-network claims received",

    "Plan_Number_Claims_Received_In_Network":
        "plan-level in-network claims received",

    "Plan_Number_Claims_Denied_Out_of_Network":
        "plan-level out-of-network denied claims",

    "Plan_Number_Claims_Denied_In_Network":
        "plan-level in-network denied claims",

    "Plan_Number_Claims_Resubmitted_Out_of_Network":
        "plan-level out-of-network resubmitted claims",

    "Plan_Number_Claims_Resubmitted_In_Network":
        "plan-level in-network resubmitted claims",

    "Average Monthly Enrollment":
        "average monthly enrollment",

    "Average Monthly Disenrollment":
        "average monthly disenrollment"
}

# ============================================================
# 9. FIND UNUSUAL FIELDS
# ============================================================

def find_unusual_fields(row, threshold=2.0):

    unusual = []

    for col in EXPLANATION_FEATURES:

        value = pd.to_numeric(
            row.get(col),
            errors="coerce"
        )

        mean = means.get(col)
        std = stds.get(col)

        if pd.isna(value) or pd.isna(mean) or pd.isna(std):
            continue

        z_score = abs((value - mean) / std)

        if z_score >= threshold:

            direction = "high" if value > mean else "low"

            label = FIELD_LABELS.get(
                col,
                col
            )

            unusual.append({
                "field": col,
                "label": label,
                "direction": direction,
                "z_score": z_score,
                "value": value
            })

    # Highest deviations first
    unusual.sort(
        key=lambda x: x["z_score"],
        reverse=True
    )

    return unusual[:5]


# ============================================================
# 10. CREATE ML EXPLANATION
# ============================================================

def create_ml_explanation(row):

    unusual = find_unusual_fields(row)

    if len(unusual) == 0:

        return (
            "The record was identified as statistically unusual "
            "by the Isolation Forest model, but no individual "
            "field exceeded the explanation threshold."
        )

    fields = []

    for item in unusual:

        direction = item["direction"]

        fields.append(
            f"{item['label']} is unusually {direction}"
        )

    field_text = "; ".join(fields)

    return (
        "The Isolation Forest identified an unusual pattern. "
        "The following fields differ significantly from the "
        "normal PUF distribution: "
        + field_text
        + "."
    )


# ============================================================
# 11. LIKELY CAUSE FOR ML ANOMALY
# ============================================================

def create_ml_cause(row):

    unusual = find_unusual_fields(row)

    if not unusual:

        return (
            "Possible unusual reporting volume, data-entry "
            "issue, missing value, aggregation problem, or "
            "unexpected operational event."
        )

    labels = [x["label"] for x in unusual[:3]]

    return (
        "The anomaly is associated with unusual values in "
        + ", ".join(labels)
        + ". Possible causes include reporting errors, "
        "incorrect aggregation, duplicate records, or an "
        "unusual operational event."
    )


# ============================================================
# 12. RECOMMENDED FIX FOR ML
# ============================================================

def create_ml_fix(row):

    return (
        "Validate the highlighted fields against the source "
        "system. Compare the plan with similar plans and "
        "check for duplicate records, incorrect aggregation, "
        "missing values, or unusual reporting patterns."
    )


# ============================================================
# 13. GENERATE FINAL EXPLANATIONS
# ============================================================

print("\nGenerating field-level explanations...")

explanations = []
causes = []
fixes = []

for _, row in df.iterrows():

    anomaly_type = str(
        row.get("anomaly_type", "NORMAL")
    )

    rule_anomaly = bool(
        row.get("rule_anomaly", False)
    )

    # --------------------------------------------------------
    # NORMAL
    # --------------------------------------------------------

    if anomaly_type == "NORMAL":

        explanation = "No anomaly detected."
        cause = "No immediate data-quality issue identified."
        fix = "No action required."

    # --------------------------------------------------------
    # RULE ONLY
    # --------------------------------------------------------

    elif anomaly_type == "RULE":

        explanation = str(
            row.get(
                "rule_reason",
                "A predefined business rule was violated."
            )
        )

        cause = (
            "The record violates a predefined "
            "data-quality or business consistency rule."
        )

        fix = (
            "Validate the affected fields against the "
            "source claims or authorization data and "
            "correct the underlying data issue."
        )

    # --------------------------------------------------------
    # RULE + ML
    # --------------------------------------------------------

    elif anomaly_type == "RULE + ML":

        ml_explanation = create_ml_explanation(row)

        explanation = (
            str(row.get(
                "rule_reason",
                "A predefined rule was violated."
            ))
            + ". "
            + ml_explanation
        )

        cause = (
            "A known rule violation is present and the "
            "overall record also shows an unusual statistical pattern."
        )

        fix = (
            "Prioritize source-data validation. Check the "
            "rule-violating fields first, then investigate "
            "the additional unusual fields identified by ML."
        )

    # --------------------------------------------------------
    # ML ONLY
    # --------------------------------------------------------

    elif anomaly_type == "ML":

        explanation = create_ml_explanation(row)

        cause = create_ml_cause(row)

        fix = create_ml_fix(row)

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    else:

        explanation = "Anomaly detected."
        cause = "Requires further investigation."
        fix = "Validate the record against the source system."

    explanations.append(explanation)
    causes.append(cause)
    fixes.append(fix)


# ============================================================
# 14. ADD EXPLANATION COLUMNS
# ============================================================

df["explanation"] = explanations
df["likely_cause"] = causes
df["recommended_fix"] = fixes

# ============================================================
# 15. ENSURE FINAL ANOMALY FLAG
# ============================================================

if "final_anomaly" not in df.columns:

    df["final_anomaly"] = (
        df["anomaly_type"] != "NORMAL"
    )

# ============================================================
# 16. SAVE
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
# 17. SUMMARY
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
    f"{(df['anomaly_type'].isin(['ML', 'RULE + ML'])).sum()}"
)

print(
    f"Final anomalies     : "
    f"{df['final_anomaly'].sum()}"
)

print("\nAnomaly types:")

print(
    df["anomaly_type"].value_counts()
)

print("\nSeverity:")

print(
    df["severity"].value_counts()
)

# ============================================================
# 18. SAMPLE OUTPUT
# ============================================================

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

sample_columns = [
    col for col in sample_columns
    if col in df.columns
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