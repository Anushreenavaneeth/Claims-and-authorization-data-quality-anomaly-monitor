import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# 1. PROJECT PATHS
# ============================================================

# Project root:
# Claims-and-authorization-data-quality-anomaly-monitor-main

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. FIND RAW TC-PUF DATASET
# ============================================================

dataset_files = list(DATA_DIR.rglob("tc_puf_raw.xlsx"))

if not dataset_files:
    raise FileNotFoundError(
        f"Could not find tc_puf_raw.xlsx inside: {DATA_DIR}"
    )

RAW_FILE = dataset_files[0]

print("=" * 70)
print("TC-PUF PREPROCESSING")
print("=" * 70)

print("\nRaw dataset found at:")
print(RAW_FILE)


# ============================================================
# 3. LOAD REQUIRED SHEETS
# ============================================================

print("\nLoading Excel sheets...")

# IMPORTANT:
# The TC-PUF Excel files contain:
# Row 1 = title
# Row 2 = legend
# Row 3 = actual column headers
#
# Therefore header=2 is required.

qhp = pd.read_excel(
    RAW_FILE,
    sheet_name="Transparency 2026 - Ind QHP",
    header=2
)

sadp = pd.read_excel(
    RAW_FILE,
    sheet_name="Transparency 2026 - Ind SADP",
    header=2
)

shop = pd.read_excel(
    RAW_FILE,
    sheet_name="Transparency 2026 - SHOP",
    header=2
)


print(f"QHP shape  : {qhp.shape}")
print(f"SADP shape : {sadp.shape}")
print(f"SHOP shape : {shop.shape}")


# ============================================================
# 4. CLEAN COLUMN NAMES
# ============================================================

def clean_column_names(df):

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # Remove accidental "Unnamed:" columns
    # if they contain no useful data.
    unnamed_columns = [
        col
        for col in df.columns
        if col.startswith("Unnamed:")
    ]

    if unnamed_columns:
        print("\nRemoving unnamed columns:")
        print(unnamed_columns)

        df = df.drop(columns=unnamed_columns)

    return df


qhp = clean_column_names(qhp)
sadp = clean_column_names(sadp)
shop = clean_column_names(shop)


# ============================================================
# 5. ADD SOURCE SHEET
# ============================================================

qhp["source_sheet"] = "Ind_QHP"
sadp["source_sheet"] = "Ind_SADP"
shop["source_sheet"] = "SHOP"


# ============================================================
# 6. COMBINE DATASETS
# ============================================================

print("\nCombining QHP, SADP and SHOP...")

tc_puf = pd.concat(
    [qhp, sadp, shop],
    ignore_index=True
)

print("\nCombined dataset shape:")
print(tc_puf.shape)


# ============================================================
# 7. REMOVE COMPLETELY EMPTY COLUMNS
# ============================================================

empty_columns = tc_puf.columns[
    tc_puf.isna().all()
].tolist()

if empty_columns:

    print("\nRemoving completely empty columns:")

    for column in empty_columns:
        print(f" - {column}")

    tc_puf = tc_puf.drop(
        columns=empty_columns
    )


# ============================================================
# 8. DEFINE NUMERIC COLUMNS
# ============================================================

numeric_columns = [

    # --------------------------------------------------------
    # Issuer-level claims
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Plan-level claims
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Enrollment
    # --------------------------------------------------------

    "Average Monthly Enrollment",

    "Average Monthly Disenrollment"
]


# ============================================================
# 9. CHECK WHICH NUMERIC COLUMNS EXIST
# ============================================================

available_numeric_columns = [
    column
    for column in numeric_columns
    if column in tc_puf.columns
]

missing_numeric_columns = [
    column
    for column in numeric_columns
    if column not in tc_puf.columns
]


print("\nNumeric columns found:")
print(
    f"{len(available_numeric_columns)} / "
    f"{len(numeric_columns)}"
)


if missing_numeric_columns:

    print("\nWARNING - Numeric columns not found:")

    for column in missing_numeric_columns:
        print(f" - {column}")


# ============================================================
# 10. CREATE SUPPRESSION INDICATORS
# ============================================================

suppression_values = [
    "*",
    "**",
    "***"
]

print("\nCreating suppression indicators...")

for column in available_numeric_columns:

    values = (
        tc_puf[column]
        .astype("string")
        .str.strip()
    )

    suppression_column = (
        column + "_suppressed"
    )

    tc_puf[suppression_column] = (
        values
        .isin(suppression_values)
        .astype(int)
    )


# ============================================================
# 11. HANDLE SUPPRESSED VALUES
# ============================================================

print("\nHandling suppressed values...")

suppression_summary = {}

for column in available_numeric_columns:

    suppression_column = (
        column + "_suppressed"
    )

    count = int(
        tc_puf[suppression_column].sum()
    )

    suppression_summary[column] = count

    tc_puf[column] = (
        tc_puf[column]
        .replace(
            ["*", "**", "***"],
            np.nan
        )
    )


# ============================================================
# 12. CONVERT NUMERIC COLUMNS
# ============================================================

print("\nConverting numeric columns...")

for column in available_numeric_columns:

    tc_puf[column] = pd.to_numeric(
        tc_puf[column],
        errors="coerce"
    )


# ============================================================
# 13. CHECK NEGATIVE VALUES
# ============================================================

print("\nChecking negative values...")

negative_report = {}

for column in available_numeric_columns:

    negative_count = int(
        (tc_puf[column] < 0).sum()
    )

    if negative_count > 0:

        negative_report[column] = (
            negative_count
        )


if negative_report:

    print("\nWARNING - Negative values found:")

    for column, count in negative_report.items():

        print(
            f" - {column}: {count}"
        )

else:

    print("No negative values found.")


# ============================================================
# 14. CHECK DUPLICATES
# ============================================================

print("\nChecking duplicate rows...")

duplicate_count = int(
    tc_puf.duplicated().sum()
)

print(
    f"Duplicate rows found: "
    f"{duplicate_count}"
)


if duplicate_count > 0:

    print(
        "Removing duplicate rows..."
    )

    tc_puf = (
        tc_puf
        .drop_duplicates()
        .reset_index(drop=True)
    )


# ============================================================
# 15. CHECK FOR UNNAMED COLUMNS
# ============================================================

print("\nChecking for accidental Unnamed columns...")

unnamed_columns_final = [
    column
    for column in tc_puf.columns
    if str(column).startswith("Unnamed:")
]


if unnamed_columns_final:

    print(
        "WARNING - Unnamed columns still exist:"
    )

    for column in unnamed_columns_final:
        print(f" - {column}")

else:

    print(
        "No accidental Unnamed columns found."
    )


# ============================================================
# 16. DATA QUALITY SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("DATA QUALITY SUMMARY")
print("=" * 70)


print("\nFinal dataset shape:")
print(tc_puf.shape)


# ------------------------------------------------------------
# Missing values
# ------------------------------------------------------------

print("\nMissing values:")

missing = (
    tc_puf
    .isna()
    .sum()
    .sort_values(ascending=False)
)

missing = missing[
    missing > 0
]

if len(missing) == 0:

    print("No missing values.")

else:

    print(missing)


# ============================================================
# 17. SUPPRESSION SUMMARY
# ============================================================

print("\nSuppressed-value summary:")

total_suppressed = 0

for column, count in suppression_summary.items():

    if count > 0:

        print(
            f" - {column}: {count}"
        )

        total_suppressed += count


print(
    f"\nTotal suppressed cells detected: "
    f"{total_suppressed}"
)


# ============================================================
# 18. DATA TYPES
# ============================================================

print("\nImportant numeric data types:")

for column in available_numeric_columns:

    print(
        f" - {column}: "
        f"{tc_puf[column].dtype}"
    )


# ============================================================
# 19. SAVE CLEANED DATASET
# ============================================================

OUTPUT_FILE = (
    PROCESSED_DIR /
    "tc_puf_cleaned.csv"
)

tc_puf.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 20. FINAL MESSAGE
# ============================================================

print("\n" + "=" * 70)
print("PREPROCESSING COMPLETED SUCCESSFULLY")
print("=" * 70)

print("\nCleaned dataset saved to:")

print(OUTPUT_FILE)

print("\nFinal dataset shape:")

print(tc_puf.shape)

print("\nFile ready for the next stage:")
print("DATA VALIDATION / EXPLORATORY DATA ANALYSIS")

print("=" * 70)