import numpy as np
import pandas as pd


ROOT_CAUSE_COLS = [
    "missing_data",
    "invalid_date",
    "future_request",
    "approval_before_request",
    "invalid_validity_range",
    "negative_quantity",
    "negative_amount",
    "unusual_quantity",
    "unusual_amount",
    "duplicate_record"
]


# ============================================================
# TRAIN RULE THRESHOLDS
# ============================================================

def train_rule_thresholds(
    prepared_data
):

    requested_quantity_num = (
        prepared_data[
            "requested_quantity_num"
        ]
    )

    charged_amount_num = (
        prepared_data[
            "charged_amount_num"
        ]
    )


    # --------------------------------------------------------
    # QUANTITY IQR
    # --------------------------------------------------------

    quantity_values = (
        requested_quantity_num
        .dropna()
    )


    if len(quantity_values) > 0:

        q1 = quantity_values.quantile(0.25)

        q3 = quantity_values.quantile(0.75)

        iqr = q3 - q1

        quantity_lower = q1 - 1.5 * iqr

        quantity_upper = q3 + 1.5 * iqr

    else:

        quantity_lower = -np.inf

        quantity_upper = np.inf


    # --------------------------------------------------------
    # AMOUNT IQR
    # --------------------------------------------------------

    amount_values = (
        charged_amount_num
        .dropna()
    )


    if len(amount_values) > 0:

        q1 = amount_values.quantile(0.25)

        q3 = amount_values.quantile(0.75)

        iqr = q3 - q1

        amount_lower = q1 - 1.5 * iqr

        amount_upper = q3 + 1.5 * iqr

    else:

        amount_lower = -np.inf

        amount_upper = np.inf


    return {

        "quantity_lower":
            float(quantity_lower),

        "quantity_upper":
            float(quantity_upper),

        "amount_lower":
            float(amount_lower),

        "amount_upper":
            float(amount_upper)
    }


# ============================================================
# RUN RULE CHECKS
# ============================================================

def run_rule_checks(
    prepared_data,
    rule_thresholds
):

    df = prepared_data[
        "df_original"
    ]

    features = prepared_data[
        "features"
    ]

    dates = prepared_data[
        "dates"
    ]

    requested_quantity_num = prepared_data[
        "requested_quantity_num"
    ]

    charged_amount_num = prepared_data[
        "charged_amount_num"
    ]


    conditions = pd.DataFrame(
        index=df.index
    )


    # --------------------------------------------------------
    # MISSING DATA
    # --------------------------------------------------------

    conditions["missing_data"] = np.where(
        features["missing_critical_count"] > 0,
        "yes",
        "no"
    )


    # --------------------------------------------------------
    # INVALID DATE
    # --------------------------------------------------------

    conditions["invalid_date"] = np.where(
        features["invalid_date_count"] > 0,
        "yes",
        "no"
    )


    # --------------------------------------------------------
    # DATE HELPER
    # --------------------------------------------------------

    def get_date(col):

        if col in dates:
            return dates[col]

        return pd.Series(
            pd.NaT,
            index=df.index
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
    # FUTURE REQUEST
    # --------------------------------------------------------

    today = pd.Timestamp.today().normalize()

    conditions["future_request"] = np.where(
        request_date > today,
        "yes",
        "no"
    )


    # --------------------------------------------------------
    # APPROVAL BEFORE REQUEST
    # --------------------------------------------------------

    conditions[
        "approval_before_request"
    ] = np.where(
        (
            approval_date.notna()
            &
            request_date.notna()
            &
            (
                approval_date
                <
                request_date
            )
        ),
        "yes",
        "no"
    )


    # --------------------------------------------------------
    # INVALID VALIDITY RANGE
    # --------------------------------------------------------

    conditions[
        "invalid_validity_range"
    ] = np.where(
        (
            valid_from_date.notna()
            &
            valid_to_date.notna()
            &
            (
                valid_to_date
                <
                valid_from_date
            )
        ),
        "yes",
        "no"
    )


    # --------------------------------------------------------
    # NEGATIVE QUANTITY
    # --------------------------------------------------------

    conditions[
        "negative_quantity"
    ] = np.where(
        requested_quantity_num < 0,
        "yes",
        "no"
    )


    # --------------------------------------------------------
    # NEGATIVE AMOUNT
    # --------------------------------------------------------

    conditions[
        "negative_amount"
    ] = np.where(
        charged_amount_num < 0,
        "yes",
        "no"
    )


    # --------------------------------------------------------
    # UNUSUAL QUANTITY
    # --------------------------------------------------------

    conditions[
        "unusual_quantity"
    ] = np.where(
        (
            requested_quantity_num
            <
            rule_thresholds[
                "quantity_lower"
            ]
        )
        |
        (
            requested_quantity_num
            >
            rule_thresholds[
                "quantity_upper"
            ]
        ),
        "yes",
        "no"
    )


    # --------------------------------------------------------
    # UNUSUAL AMOUNT
    # --------------------------------------------------------

    conditions[
        "unusual_amount"
    ] = np.where(
        (
            charged_amount_num
            <
            rule_thresholds[
                "amount_lower"
            ]
        )
        |
        (
            charged_amount_num
            >
            rule_thresholds[
                "amount_upper"
            ]
        ),
        "yes",
        "no"
    )


    # --------------------------------------------------------
    # DUPLICATE RECORD
    # --------------------------------------------------------

    conditions[
        "duplicate_record"
    ] = np.where(
        df.duplicated(keep=False),
        "yes",
        "no"
    )


    # --------------------------------------------------------
    # RULE COUNT
    # --------------------------------------------------------

    conditions[
        "rule_anomaly_count"
    ] = (
        conditions[
            ROOT_CAUSE_COLS
        ]
        .eq("yes")
        .sum(axis=1)
    )


    conditions[
        "rule_anomaly_flag"
    ] = np.where(
        conditions[
            "rule_anomaly_count"
        ] > 0,
        1,
        0
    )


    return conditions