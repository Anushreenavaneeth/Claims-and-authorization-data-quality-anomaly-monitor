import numpy as np
import pandas as pd

from sklearn.preprocessing import OrdinalEncoder


# ============================================================
# CONFIGURATION
# ============================================================

DATE_COLS = [
    "request_date",
    "approval_date",
    "valid_from_date",
    "valid_to_date"
]


CRITICAL_COLS = [
    "patient_id",
    "provider_id",
    "request_date",
    "authorization_type",
    "service_code",
    "requested_quantity",
    "charged_amount",
    "approval_status"
]


CATEGORICAL_FEATURES = [
    "authorization_type",
    "approval_status",
    "service_description"
]


# ============================================================
# MAIN PREPROCESSING FUNCTION
# ============================================================

def prepare_authorization_data(
    df,
    training=True,
    preprocessing_artifacts=None
):
    """
    Prepares authorization data for ML.

    Important:
    - Original null/missing values are NOT removed.
    - Missing values are preserved as missing flags.
    - Invalid values are retained as anomaly signals.
    - Separate ML dataframe is created for model input.
    """

    # --------------------------------------------------------
    # KEEP ORIGINAL DATA
    # --------------------------------------------------------

    df_original = df.copy()

    df_work = df.copy()


    # --------------------------------------------------------
    # DATE CONVERSION
    # --------------------------------------------------------

    dates = {}

    for col in DATE_COLS:

        if col in df_work.columns:

            dates[col] = pd.to_datetime(
                df_work[col],
                errors="coerce"
            )


    # --------------------------------------------------------
    # NUMERIC CONVERSION
    # --------------------------------------------------------

    if "requested_quantity" in df_work.columns:

        requested_quantity_num = pd.to_numeric(
            df_work["requested_quantity"],
            errors="coerce"
        )

    else:

        requested_quantity_num = pd.Series(
            np.nan,
            index=df_work.index
        )


    if "charged_amount" in df_work.columns:

        charged_amount_num = pd.to_numeric(
            df_work["charged_amount"],
            errors="coerce"
        )

    else:

        charged_amount_num = pd.Series(
            np.nan,
            index=df_work.index
        )


    # --------------------------------------------------------
    # CREATE FEATURE DATAFRAME
    # --------------------------------------------------------

    features = pd.DataFrame(
        index=df_work.index
    )


    # --------------------------------------------------------
    # MISSING CRITICAL FIELD COUNT
    # --------------------------------------------------------

    available_critical_cols = [
        col
        for col in CRITICAL_COLS
        if col in df_work.columns
    ]


    if len(available_critical_cols) > 0:

        features["missing_critical_count"] = (
            df_work[
                available_critical_cols
            ]
            .isnull()
            .sum(axis=1)
        )

    else:

        features["missing_critical_count"] = 0


    # --------------------------------------------------------
    # INVALID DATE COUNT
    # --------------------------------------------------------

    invalid_date_count = pd.Series(
        0,
        index=df_work.index,
        dtype=int
    )


    for col in DATE_COLS:

        if col not in df_work.columns:
            continue

        invalid_date = (
            df_work[col].notna()
            &
            dates[col].isna()
        )

        invalid_date_count += (
            invalid_date.astype(int)
        )


    features["invalid_date_count"] = (
        invalid_date_count
    )


    # --------------------------------------------------------
    # HELPER FOR DATE COLUMNS
    # --------------------------------------------------------

    def get_date(col):

        if col in dates:
            return dates[col]

        return pd.Series(
            pd.NaT,
            index=df_work.index
        )


    request_date = get_date(
        "request_date"
    )

    approval_date = get_date(
        "approval_date"
    )

    valid_from_date = get_date(
        "valid_from_date"
    )

    valid_to_date = get_date(
        "valid_to_date"
    )


    # --------------------------------------------------------
    # DATE FEATURE ENGINEERING
    # --------------------------------------------------------

    features["approval_delay_days"] = (
        approval_date - request_date
    ).dt.days


    features["validity_duration_days"] = (
        valid_to_date - valid_from_date
    ).dt.days


    features["request_to_valid_days"] = (
        valid_from_date - request_date
    ).dt.days


    # --------------------------------------------------------
    # NUMERIC FEATURES
    # --------------------------------------------------------

    features["requested_quantity"] = (
        requested_quantity_num
    )

    features["charged_amount"] = (
        charged_amount_num
    )


    # --------------------------------------------------------
    # MISSING FLAGS
    # --------------------------------------------------------

    for col in df_work.columns:

        features[
            f"{col}_missing_flag"
        ] = df_work[col].isnull().astype(int)


    # --------------------------------------------------------
    # CATEGORICAL FEATURES
    # --------------------------------------------------------

    for col in CATEGORICAL_FEATURES:

        if col in df_work.columns:

            features[col] = (
                df_work[col]
                .fillna("__MISSING__")
                .astype(str)
                .str.lower()
                .str.strip()
            )

        else:

            features[col] = "__MISSING__"


    # --------------------------------------------------------
    # SERVICE CODE PREFIX
    # --------------------------------------------------------

    if "service_code" in df_work.columns:

        features["service_code_prefix"] = (
            df_work["service_code"]
            .fillna("__MISSING__")
            .astype(str)
            .str.extract(
                r"^([A-Za-z]+)",
                expand=False
            )
            .fillna("OTHER")
        )

    else:

        features["service_code_prefix"] = "OTHER"


    # ========================================================
    # CREATE ML DATAFRAME
    # ========================================================

    ml_df = features.copy()


    # ========================================================
    # TRAINING MODE
    # ========================================================

    if training:

        categorical_cols = ml_df.select_dtypes(
            include=[
                "object",
                "string",
                "category"
            ]
        ).columns.tolist()


        encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=-1
        )


        if len(categorical_cols) > 0:

            ml_df[categorical_cols] = (
                encoder.fit_transform(
                    ml_df[categorical_cols]
                )
            )


        # Replace infinite values

        ml_df = ml_df.replace(
            [np.inf, -np.inf],
            np.nan
        )


        # Imputation values

        imputation_values = {}


        for col in ml_df.columns:

            if ml_df[col].isna().any():

                median_value = (
                    ml_df[col].median()
                )

                if pd.isna(median_value):
                    median_value = 0

                imputation_values[col] = float(
                    median_value
                )

                ml_df[col] = (
                    ml_df[col]
                    .fillna(median_value)
                )


        # Remove constant columns

        constant_cols = [
            col
            for col in ml_df.columns
            if ml_df[col].nunique() <= 1
        ]


        ml_df = ml_df.drop(
            columns=constant_cols
        )


        preprocessing_artifacts = {

            "encoder":
                encoder,

            "categorical_cols":
                categorical_cols,

            "imputation_values":
                imputation_values,

            "constant_cols":
                constant_cols,

            "ml_feature_columns":
                ml_df.columns.tolist()
        }


    # ========================================================
    # INFERENCE MODE
    # ========================================================

    else:

        if preprocessing_artifacts is None:

            raise ValueError(
                "preprocessing_artifacts are required "
                "when training=False"
            )


        encoder = preprocessing_artifacts[
            "encoder"
        ]

        categorical_cols = preprocessing_artifacts[
            "categorical_cols"
        ]


        for col in categorical_cols:

            if col not in ml_df.columns:

                ml_df[col] = "__MISSING__"


        if len(categorical_cols) > 0:

            ml_df[categorical_cols] = (
                encoder.transform(
                    ml_df[categorical_cols]
                )
            )


        ml_df = ml_df.replace(
            [np.inf, -np.inf],
            np.nan
        )


        expected_features = preprocessing_artifacts[
            "ml_feature_columns"
        ]


        # Add missing expected columns

        for col in expected_features:

            if col not in ml_df.columns:

                ml_df[col] = 0


        # Keep exact training order

        ml_df = ml_df[
            expected_features
        ].copy()


        imputation_values = preprocessing_artifacts[
            "imputation_values"
        ]


        for col in ml_df.columns:

            fill_value = imputation_values.get(
                col,
                0
            )

            ml_df[col] = (
                ml_df[col]
                .fillna(fill_value)
            )


    # ========================================================
    # RETURN EVERYTHING
    # ========================================================

    return {

        "df_original":
            df_original,

        "features":
            features,

        "ml_df":
            ml_df,

        "dates":
            dates,

        "requested_quantity_num":
            requested_quantity_num,

        "charged_amount_num":
            charged_amount_num,

        "preprocessing_artifacts":
            preprocessing_artifacts
    }