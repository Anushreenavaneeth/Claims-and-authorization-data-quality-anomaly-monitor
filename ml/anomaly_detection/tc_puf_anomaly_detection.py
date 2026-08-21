import pandas as pd
from pathlib import Path
from sklearn.impute import SimpleImputer
from sklearn.ensemble import IsolationForest


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "tc_puf_cleaned.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "anomalies"
OUTPUT_FILE = OUTPUT_DIR / "tc_puf_anomalies.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("TC-PUF ANOMALY DETECTION")
print("=" * 70)

print("\nLoading cleaned dataset...")

df = pd.read_csv(INPUT_FILE)

print(f"Dataset shape: {df.shape}")


# ============================================================
# CLAIM / OPERATIONAL FEATURES
# ============================================================

features = [
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

features = [f for f in features if f in df.columns]

print(f"\nML features selected: {len(features)}")


# ============================================================
# RULE-BASED ANOMALIES
# ============================================================

print("\nRunning rule-based checks...")

df["rule_anomaly"] = False
df["rule_reason"] = ""


def add_rule(mask, reason):
    df.loc[mask, "rule_anomaly"] = True

    empty_reason = df["rule_reason"] == ""

    df.loc[mask & empty_reason, "rule_reason"] = reason

    df.loc[
        mask & ~empty_reason,
        "rule_reason"
    ] += "; " + reason


# Rule 1: Negative values
numeric_features = df[features].select_dtypes(include="number").columns

negative_mask = df[numeric_features].lt(0).any(axis=1)

add_rule(
    negative_mask,
    "Negative numeric value"
)


# Rule 2: Denied claims > received claims

mask = (
    df["Issuer_Claims_Denied_In_Network"]
    > df["Issuer_Claims_Received_In_Network"]
)

add_rule(
    mask,
    "Issuer denied claims exceed received claims"
)


mask = (
    df["Issuer_Claims_Denied_Out_of_Network"]
    > df["Issuer_Claims_Received_Out_of_Network"]
)

add_rule(
    mask,
    "Issuer out-of-network denied claims exceed received claims"
)


# Rule 3: Resubmitted > received

mask = (
    df["Issuer_Claims_Resubmitted_In_Network"]
    > df["Issuer_Claims_Received_In_Network"]
)

add_rule(
    mask,
    "Issuer resubmitted claims exceed received claims"
)


mask = (
    df["Issuer_Claims_Resubmitted_Out_of_Network"]
    > df["Issuer_Claims_Received_Out_of_Network"]
)

add_rule(
    mask,
    "Issuer out-of-network resubmitted claims exceed received claims"
)


# Rule 4: Overturned > appeals filed

mask = (
    df["Issuer_Number_Internal_Appeals_Overturned"]
    > df["Issuer_Internal_Appeals_Filed"]
)

add_rule(
    mask,
    "Internal overturned appeals exceed appeals filed"
)


mask = (
    df["Issuer_Number_External_Appeals_Overturned"]
    > df["Issuer_External_Appeals_Filed"]
)

add_rule(
    mask,
    "External overturned appeals exceed appeals filed"
)


# Rule 5: Invalid percentages

mask = (
    (df["Issuer_Percent_Internal_Appeals_Overturned"] < 0)
    |
    (df["Issuer_Percent_Internal_Appeals_Overturned"] > 100)
)

add_rule(
    mask,
    "Invalid internal appeal percentage"
)


mask = (
    (df["Issuer_Percent_External_Appeals_Overturned"] < 0)
    |
    (df["Issuer_Percent_External_Appeals_Overturned"] > 100)
)

add_rule(
    mask,
    "Invalid external appeal percentage"
)


print(
    f"Rule anomalies: "
    f"{df['rule_anomaly'].sum()}"
)


# ============================================================
# ISOLATION FOREST
# ============================================================

print("\nPreparing data for Isolation Forest...")

X = df[features].copy()

# Convert everything to numeric
X = X.apply(pd.to_numeric, errors="coerce")

# Median imputation
imputer = SimpleImputer(strategy="median")

X_imputed = imputer.fit_transform(X)


print("Training Isolation Forest...")

model = IsolationForest(
    n_estimators=200,
    contamination="auto",
    random_state=42,
    n_jobs=-1
)

model.fit(X_imputed)


# Predictions
predictions = model.predict(X_imputed)

scores = model.decision_function(X_imputed)


df["ml_prediction"] = predictions

df["ml_anomaly"] = predictions == -1

df["ml_anomaly_score"] = scores


print(
    f"ML anomalies: "
    f"{df['ml_anomaly'].sum()}"
)


# ============================================================
# COMBINE RULE + ML
# ============================================================

df["final_anomaly"] = (
    df["rule_anomaly"]
    |
    df["ml_anomaly"]
)


# ============================================================
# ANOMALY TYPE
# ============================================================

def anomaly_type(row):

    if row["rule_anomaly"] and row["ml_anomaly"]:
        return "RULE + ML"

    elif row["rule_anomaly"]:
        return "RULE"

    elif row["ml_anomaly"]:
        return "ML"

    return "NORMAL"


df["anomaly_type"] = df.apply(
    anomaly_type,
    axis=1
)


# ============================================================
# SEVERITY
# ============================================================

def severity(row):

    if not row["final_anomaly"]:
        return "NORMAL"

    if row["rule_anomaly"] and row["ml_anomaly"]:
        return "HIGH"

    if row["rule_anomaly"]:
        return "HIGH"

    return "MEDIUM"


df["severity"] = df.apply(
    severity,
    axis=1
)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("ANOMALY DETECTION COMPLETED")
print("=" * 70)

print(f"\nTotal records       : {len(df)}")
print(f"Rule anomalies      : {df['rule_anomaly'].sum()}")
print(f"ML anomalies        : {df['ml_anomaly'].sum()}")
print(f"Final anomalies     : {df['final_anomaly'].sum()}")

print("\nAnomaly types:")
print(df["anomaly_type"].value_counts())

print("\nSeverity:")
print(df["severity"].value_counts())

print("\nOutput saved to:")
print(OUTPUT_FILE)