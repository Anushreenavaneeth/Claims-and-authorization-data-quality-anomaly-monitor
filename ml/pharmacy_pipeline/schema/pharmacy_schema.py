import csv
from pathlib import Path


# ============================================================
# PHARMACY SCHEMA NORMALIZATION
# ============================================================

# Canonical names used by your existing Pharmacy pipeline.

CANONICAL_COLUMNS = {
    "Prscrbr_NPI",
    "Prscrbr_Last_Org_Name",
    "Prscrbr_First_Name",
    "Prscrbr_City",
    "Prscrbr_State_Abrvtn",
    "Prscrbr_State_FIPS",
    "Prscrbr_Type",
    "Prscrbr_Type_Src",
    "Brnd_Name",
    "Gnrc_Name",
    "Tot_Clms",
    "Tot_30day_Fills",
    "Tot_Day_Suply",
    "Tot_Drug_Cst",
    "Tot_Benes",
    "GE65_Sprsn_Flag",
    "GE65_Tot_Clms",
    "GE65_Tot_30day_Fills",
    "GE65_Tot_Drug_Cst",
    "GE65_Tot_Day_Suply",
    "GE65_Bene_Sprsn_Flag",
    "GE65_Tot_Benes",
}


# ============================================================
# REQUIRED CORE PHARMACY FIELDS
# ============================================================

REQUIRED_COLUMNS = {
    "Prscrbr_NPI",
    "Brnd_Name",
    "Gnrc_Name",
    "Tot_Clms",
    "Tot_30day_Fills",
    "Tot_Day_Suply",
    "Tot_Drug_Cst",
    "Tot_Benes",
}


# ============================================================
# ALTERNATIVE COLUMN NAMES
# ============================================================
#
# Add aliases here when you encounter real incoming files.
#
# The LEFT side is your standard internal column.
# The RIGHT side contains possible incoming names.
#
# We intentionally do NOT guess arbitrary columns.
# ============================================================

COLUMN_ALIASES = {

    "Prscrbr_NPI": [
        "Prscrbr_NPI",
        "NPI",
        "Prescriber_NPI",
        "Prescriber NPI",
        "Provider_NPI",
        "Provider NPI",
    ],

    "Prscrbr_Last_Org_Name": [
        "Prscrbr_Last_Org_Name",
        "Prescriber_Last_Name",
        "Prescriber Last Name",
        "Provider_Last_Name",
    ],

    "Prscrbr_First_Name": [
        "Prscrbr_First_Name",
        "Prescriber_First_Name",
        "Prescriber First Name",
        "Provider_First_Name",
    ],

    "Prscrbr_City": [
        "Prscrbr_City",
        "Prescriber_City",
        "Prescriber City",
        "Provider_City",
    ],

    "Prscrbr_State_Abrvtn": [
        "Prscrbr_State_Abrvtn",
        "Prescriber_State",
        "Prescriber State",
        "Provider_State",
        "State",
    ],

    "Prscrbr_State_FIPS": [
        "Prscrbr_State_FIPS",
        "State_FIPS",
        "State FIPS",
    ],

    "Prscrbr_Type": [
        "Prscrbr_Type",
        "Prescriber_Type",
        "Prescriber Type",
        "Provider_Type",
        "Provider Type",
    ],

    "Prscrbr_Type_Src": [
        "Prscrbr_Type_Src",
        "Prescriber_Type_Source",
        "Provider_Type_Source",
    ],

    "Brnd_Name": [
        "Brnd_Name",
        "Brand_Name",
        "Brand Name",
        "Drug_Name",
        "Drug Name",
    ],

    "Gnrc_Name": [
        "Gnrc_Name",
        "Generic_Name",
        "Generic Name",
        "Generic_Drug_Name",
    ],

    "Tot_Clms": [
        "Tot_Clms",
        "Total_Claims",
        "Total Claims",
        "Claims",
        "Claim_Count",
        "Claim Count",
    ],

    "Tot_30day_Fills": [
        "Tot_30day_Fills",
        "Total_30day_Fills",
        "Total 30day Fills",
        "Total_Fills",
        "Total Fills",
        "Fills",
    ],

    "Tot_Day_Suply": [
        "Tot_Day_Suply",
        "Tot_Day_Supply",
        "Total_Day_Supply",
        "Total Day Supply",
        "Day_Supply",
        "Day Supply",
    ],

    "Tot_Drug_Cst": [
        "Tot_Drug_Cst",
        "Total_Drug_Cost",
        "Total Drug Cost",
        "Drug_Cost",
        "Drug Cost",
        "Total_Cost",
    ],

    "Tot_Benes": [
        "Tot_Benes",
        "Total_Beneficiaries",
        "Total Beneficiaries",
        "Beneficiaries",
        "Beneficiary_Count",
        "Beneficiary Count",
    ],

    "GE65_Sprsn_Flag": [
        "GE65_Sprsn_Flag",
        "GE65_Suppression_Flag",
    ],

    "GE65_Tot_Clms": [
        "GE65_Tot_Clms",
        "GE65_Total_Claims",
    ],

    "GE65_Tot_30day_Fills": [
        "GE65_Tot_30day_Fills",
        "GE65_Total_30day_Fills",
    ],

    "GE65_Tot_Drug_Cst": [
        "GE65_Tot_Drug_Cst",
        "GE65_Total_Drug_Cost",
    ],

    "GE65_Tot_Day_Suply": [
        "GE65_Tot_Day_Suply",
        "GE65_Tot_Day_Supply",
        "GE65_Total_Day_Supply",
    ],

    "GE65_Bene_Sprsn_Flag": [
        "GE65_Bene_Sprsn_Flag",
        "GE65_Beneficiary_Suppression_Flag",
    ],

    "GE65_Tot_Benes": [
        "GE65_Tot_Benes",
        "GE65_Total_Beneficiaries",
    ],
}


# ============================================================
# NORMALIZE COLUMN TEXT
# ============================================================

def normalize_column_name(column):

    return (
        column
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


# ============================================================
# READ CSV HEADER ONLY
# ============================================================

def get_columns(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.reader(file)

        header = next(reader)

    return [
        column.strip()
        for column in header
        if column.strip()
    ]


# ============================================================
# BUILD ALIAS LOOKUP
# ============================================================

def build_alias_lookup():

    lookup = {}

    for canonical, aliases in COLUMN_ALIASES.items():

        for alias in aliases:

            lookup[
                normalize_column_name(alias)
            ] = canonical

    return lookup


# ============================================================
# MAP INCOMING COLUMNS
# ============================================================

def map_columns(incoming_columns):

    alias_lookup = build_alias_lookup()

    mapping = {}

    unmapped_columns = []

    for incoming in incoming_columns:

        normalized = normalize_column_name(
            incoming
        )

        canonical = alias_lookup.get(
            normalized
        )

        if canonical:

            if canonical in mapping:

                # Two incoming columns mapped to the
                # same canonical field.
                raise ValueError(
                    f"Multiple columns map to "
                    f"'{canonical}': "
                    f"'{mapping[canonical]}' "
                    f"and '{incoming}'"
                )

            mapping[canonical] = incoming

        else:

            unmapped_columns.append(
                incoming
            )

    return mapping, unmapped_columns


# ============================================================
# SOURCE IDENTIFICATION
# ============================================================

def identify_pharmacy(incoming_columns):

    mapping, _ = map_columns(
        incoming_columns
    )

    matched_required = (
        REQUIRED_COLUMNS
        .intersection(mapping.keys())
    )

    # Require all core Pharmacy fields.
    return (
        len(matched_required)
        == len(REQUIRED_COLUMNS)
    )


# ============================================================
# VALIDATE SCHEMA
# ============================================================

def validate_schema(incoming_columns):

    mapping, unmapped = map_columns(
        incoming_columns
    )

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in mapping
    ]

    return {
        "is_pharmacy": len(missing) == 0,
        "mapping": mapping,
        "missing_required_columns": missing,
        "unmapped_columns": unmapped,
    }


# ============================================================
# PRINT SCHEMA REPORT
# ============================================================

def print_schema_report(
    file_path,
    incoming_columns,
    result,
):

    print("=" * 80)
    print("PHARMACY SOURCE IDENTIFICATION")
    print("=" * 80)

    print(
        f"\nInput file:\n{file_path}"
    )

    print(
        f"\nIncoming column count: "
        f"{len(incoming_columns)}"
    )

    # --------------------------------------------------------
    # Source
    # --------------------------------------------------------

    if result["is_pharmacy"]:

        print(
            "\nSOURCE TYPE: PHARMACY"
        )

        print(
            "STATUS: ACCEPTED"
        )

    else:

        print(
            "\nSOURCE TYPE: UNKNOWN / INVALID PHARMACY"
        )

        print(
            "STATUS: REJECTED"
        )

    # --------------------------------------------------------
    # Mapping
    # --------------------------------------------------------

    print(
        "\nCOLUMN MAPPING"
    )

    for canonical, incoming in sorted(
        result["mapping"].items()
    ):

        if canonical == incoming:

            print(
                f"  {incoming} "
                f"-> {canonical}"
            )

        else:

            print(
                f"  {incoming} "
                f"-> {canonical}"
            )

    # --------------------------------------------------------
    # Missing
    # --------------------------------------------------------

    if result[
        "missing_required_columns"
    ]:

        print(
            "\nMISSING REQUIRED COLUMNS:"
        )

        for column in result[
            "missing_required_columns"
        ]:

            print(
                f"  - {column}"
            )

    # --------------------------------------------------------
    # Unmapped
    # --------------------------------------------------------

    if result[
        "unmapped_columns"
    ]:

        print(
            "\nUNMAPPED EXTRA COLUMNS:"
        )

        for column in result[
            "unmapped_columns"
        ]:

            print(
                f"  - {column}"
            )


# ============================================================
# MAIN
# ============================================================

def inspect_file(file_path):

    file_path = Path(file_path)

    if not file_path.exists():

        print(
            f"ERROR: File not found:\n"
            f"{file_path}"
        )

        return False

    try:

        columns = get_columns(
            file_path
        )

        result = validate_schema(
            columns
        )

        print_schema_report(
            file_path,
            columns,
            result,
        )

        return result["is_pharmacy"]

    except Exception as error:

        print(
            "\nSCHEMA INSPECTION ERROR:"
        )

        print(error)

        return False


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    import sys

    print("=" * 80)
    print("PHARMACY SCHEMA VALIDATION")
    print("=" * 80)

    if len(sys.argv) != 2:

        print(
            "\nUsage:"
        )

        print(
            "python schema/pharmacy_schema.py "
            "<csv_file>"
        )

        sys.exit(1)

    input_file = sys.argv[1]

    success = inspect_file(
        input_file
    )

    if success:

        print(
            "\nPHARMACY SCHEMA VALIDATION PASSED"
        )

        sys.exit(0)

    else:

        print(
            "\nPHARMACY SCHEMA VALIDATION FAILED"
        )

        sys.exit(1)