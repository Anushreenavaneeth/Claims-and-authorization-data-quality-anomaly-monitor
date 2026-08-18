import pandas as pd
from pathlib import Path


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "tc_puf_cleaned.csv"
)


# ============================================================
# 2. LOAD CLEANED DATA
# ============================================================

print("=" * 70)
print("TC-PUF EXPLORATORY DATA ANALYSIS")
print("=" * 70)

print("\nLoading cleaned dataset...")

df = pd.read_csv(PROCESSED_FILE)

print("\nDataset loaded successfully.")

print("\nDataset shape:")
print(df.shape)


# ============================================================
# 3. COLUMN INFORMATION
# ============================================================

print("\n" + "=" * 70)
print("COLUMN INFORMATION")
print("=" * 70)

print("\nTotal columns:")
print(len(df.columns))

print("\nColumns:")

for column in df.columns:
    print(f" - {column}")


# ============================================================
# 4. DATA TYPES
# ============================================================

print("\n" + "=" * 70)
print("DATA TYPES")
print("=" * 70)

print(
    df.dtypes.value_counts()
)


# ============================================================
# 5. SOURCE SHEET DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("SOURCE SHEET DISTRIBUTION")
print("=" * 70)

print(
    df["source_sheet"]
    .value_counts()
)


# ============================================================
# 6. PLAN TYPE DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("PLAN TYPE DISTRIBUTION")
print("=" * 70)

if "QHP or SADP?" in df.columns:

    print(
        df["QHP or SADP?"]
        .value_counts(dropna=False)
    )


# ============================================================
# 7. STATE DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("STATE DISTRIBUTION")
print("=" * 70)

if "State" in df.columns:

    print(
        df["State"]
        .value_counts()
        .head(20)
    )


# ============================================================
# 8. MISSING VALUE ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("MISSING VALUE ANALYSIS")
print("=" * 70)

missing = (
    df.isna()
    .sum()
    .sort_values(ascending=False)
)

missing = missing[missing > 0]

print("\nColumns containing missing values:")

print(missing)


# ============================================================
# 9. MISSING VALUE PERCENTAGES
# ============================================================

print("\n" + "=" * 70)
print("MISSING VALUE PERCENTAGES")
print("=" * 70)

missing_percentage = (
    df.isna()
    .mean()
    .mul(100)
    .sort_values(ascending=False)
)

missing_percentage = (
    missing_percentage[
        missing_percentage > 0
    ]
)

print(
    missing_percentage
)


# ============================================================
# 10. SUPPRESSION ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("SUPPRESSION ANALYSIS")
print("=" * 70)

suppression_columns = [
    column
    for column in df.columns
    if column.endswith("_suppressed")
]

print(
    f"\nSuppression indicator columns: "
    f"{len(suppression_columns)}"
)

suppression_totals = {}

for column in suppression_columns:

    count = int(
        df[column].sum()
    )

    if count > 0:

        suppression_totals[column] = count


print("\nSuppressed values by field:")

for column, count in suppression_totals.items():

    print(
        f" - {column}: {count}"
    )


# ============================================================
# 11. DUPLICATE ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("DUPLICATE ANALYSIS")
print("=" * 70)

duplicate_count = df.duplicated().sum()

print(
    f"\nDuplicate rows: "
    f"{duplicate_count}"
)


# ============================================================
# 12. NUMERIC SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("NUMERIC DATA SUMMARY")
print("=" * 70)

numeric_df = df.select_dtypes(
    include="number"
)

print(
    numeric_df.describe()
    .transpose()
)


# ============================================================
# 13. ZERO VALUE ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("ZERO VALUE ANALYSIS")
print("=" * 70)

for column in numeric_df.columns:

    if column.endswith("_suppressed"):
        continue

    zero_count = (
        numeric_df[column] == 0
    ).sum()

    if zero_count > 0:

        print(
            f"{column}: "
            f"{zero_count} zero values"
        )


# ============================================================
# 14. FINAL MESSAGE
# ============================================================

print("\n" + "=" * 70)
print("EDA COMPLETED")
print("=" * 70)

print("\nNext stage:")
print("ANOMALY DETECTION")