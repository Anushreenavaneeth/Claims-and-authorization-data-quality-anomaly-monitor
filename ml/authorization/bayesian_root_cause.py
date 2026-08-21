import numpy as np


try:

    from pgmpy.models import (
        DiscreteBayesianNetwork
    )

except ImportError:

    from pgmpy.models import (
        BayesianNetwork as DiscreteBayesianNetwork
    )


from pgmpy.estimators import BayesianEstimator

from pgmpy.inference import VariableElimination


# ============================================================
# ROOT CAUSE COLUMNS
# ============================================================

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
# TRAIN BAYESIAN MODEL
# ============================================================

def train_bayesian_model(
    conditions
):

    # --------------------------------------------------------
    # CREATE TRAINING DATA
    # --------------------------------------------------------

    bayesian_data = conditions[
        ROOT_CAUSE_COLS
    ].copy()


    bayesian_data["anomaly"] = np.where(
        conditions[
            "ml_anomaly_flag"
        ] == 1,
        "yes",
        "no"
    )


    # --------------------------------------------------------
    # NETWORK STRUCTURE
    # --------------------------------------------------------

    edges = [

        ("missing_data", "anomaly"),

        ("invalid_date", "anomaly"),

        ("future_request", "anomaly"),

        (
            "approval_before_request",
            "anomaly"
        ),

        (
            "invalid_validity_range",
            "anomaly"
        ),

        (
            "negative_quantity",
            "anomaly"
        ),

        (
            "negative_amount",
            "anomaly"
        ),

        (
            "unusual_quantity",
            "anomaly"
        ),

        (
            "unusual_amount",
            "anomaly"
        ),

        (
            "duplicate_record",
            "anomaly"
        )
    ]


    model = DiscreteBayesianNetwork(
        edges
    )


    # --------------------------------------------------------
    # TRAIN MODEL
    # --------------------------------------------------------

    model.fit(
        bayesian_data,
        estimator=BayesianEstimator,
        prior_type="BDeu",
        equivalent_sample_size=10
    )


    inference = VariableElimination(
        model
    )


    # --------------------------------------------------------
    # BASELINE CAUSE PROBABILITIES
    # --------------------------------------------------------

    baseline_probabilities = {}


    for cause in ROOT_CAUSE_COLS:

        result = inference.query(
            variables=[cause],
            show_progress=False
        )


        states = list(
            result.state_names[cause]
        )


        if "yes" in states:

            yes_index = states.index(
                "yes"
            )

            baseline_probabilities[cause] = float(
                result.values[yes_index]
            )

        else:

            baseline_probabilities[cause] = 0.0


    # --------------------------------------------------------
    # BASELINE ANOMALY PROBABILITY
    # --------------------------------------------------------

    result = inference.query(
        variables=["anomaly"],
        show_progress=False
    )


    states = list(
        result.state_names["anomaly"]
    )


    if "yes" in states:

        yes_index = states.index(
            "yes"
        )

        baseline_anomaly_probability = float(
            result.values[yes_index]
        )

    else:

        baseline_anomaly_probability = 0.0


    return {

        "bayesian_network":
            model,

        "baseline_probabilities":
            baseline_probabilities,

        "baseline_anomaly_probability":
            baseline_anomaly_probability
    }


# ============================================================
# GET BAYESIAN RESULTS
# ============================================================

def get_bayesian_results(
    conditions,
    bayesian_artifacts,
    top_n=3
):

    model = bayesian_artifacts[
        "bayesian_network"
    ]

    baseline_probabilities = bayesian_artifacts[
        "baseline_probabilities"
    ]


    baseline_anomaly_probability = (
        bayesian_artifacts[
            "baseline_anomaly_probability"
        ]
    )


    inference = VariableElimination(
        model
    )


    all_results = []


    for _, row in conditions.iterrows():

        # ----------------------------------------------------
        # ACTIVE RULE EVIDENCE
        # ----------------------------------------------------

        active_evidence = {}


        for cause in ROOT_CAUSE_COLS:

            if row[cause] == "yes":

                active_evidence[cause] = "yes"


        # ----------------------------------------------------
        # BAYESIAN ANOMALY PROBABILITY
        # ----------------------------------------------------

        if len(active_evidence) > 0:

            try:

                result = inference.query(
                    variables=["anomaly"],
                    evidence=active_evidence,
                    show_progress=False
                )


                states = list(
                    result.state_names[
                        "anomaly"
                    ]
                )


                if "yes" in states:

                    yes_index = states.index(
                        "yes"
                    )

                    anomaly_probability = float(
                        result.values[yes_index]
                    )

                else:

                    anomaly_probability = 0.0


            except Exception:

                anomaly_probability = (
                    baseline_anomaly_probability
                )

        else:

            anomaly_probability = (
                baseline_anomaly_probability
            )


        # ----------------------------------------------------
        # ROOT CAUSE ANALYSIS
        # ----------------------------------------------------

        probable_causes = []


        for cause in ROOT_CAUSE_COLS:

            # Only causes active in current record

            if row[cause] != "yes":
                continue


            try:

                result = inference.query(
                    variables=[cause],
                    evidence={
                        "anomaly": "yes"
                    },
                    show_progress=False
                )


                states = list(
                    result.state_names[cause]
                )


                if "yes" not in states:
                    continue


                yes_index = states.index(
                    "yes"
                )


                probability_given_anomaly = float(
                    result.values[yes_index]
                )


                baseline_probability = float(
                    baseline_probabilities.get(
                        cause,
                        0.0
                    )
                )


                if baseline_probability > 0:

                    lift = (
                        probability_given_anomaly
                        /
                        baseline_probability
                    )

                else:

                    lift = 0.0


                probable_causes.append({

                    "cause":
                        cause,

                    "probability_given_anomaly":
                        round(
                            probability_given_anomaly,
                            6
                        ),

                    "baseline_probability":
                        round(
                            baseline_probability,
                            6
                        ),

                    "bayesian_lift":
                        round(
                            lift,
                            4
                        )
                })


            except Exception:

                continue


        # ----------------------------------------------------
        # SORT TOP CAUSES
        # ----------------------------------------------------

        probable_causes = sorted(
            probable_causes,
            key=lambda x: (
                x["bayesian_lift"],
                x[
                    "probability_given_anomaly"
                ]
            ),
            reverse=True
        )[:top_n]


        all_results.append({

            "anomaly_probability":
                round(
                    anomaly_probability,
                    6
                ),

            "probable_root_causes":
                probable_causes
        })


    return all_results