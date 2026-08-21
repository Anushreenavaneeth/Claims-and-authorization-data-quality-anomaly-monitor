def calculate_risk(
    conditions
):
    """
    Risk Score:

    Rule risk         : Maximum 50
    ML risk           : Maximum 40
    Agreement bonus   : Maximum 10

    Final risk        : 0 to 100
    """


    risk_scores = []

    risk_levels = []

    risk_reasons = []


    for _, row in conditions.iterrows():

        # ----------------------------------------------------
        # RULE RISK
        # ----------------------------------------------------

        rule_count = int(
            row[
                "rule_anomaly_count"
            ]
        )


        rule_risk = min(
            rule_count * 15,
            50
        )


        # ----------------------------------------------------
        # ML RISK
        # ----------------------------------------------------

        ml_risk = 0


        if row["ml_anomaly_flag"] == 1:

            severity = row[
                "ml_anomaly_severity"
            ]


            if severity == "HIGH":

                ml_risk = 40


            elif severity == "MEDIUM":

                ml_risk = 30


            else:

                ml_risk = 20


        # ----------------------------------------------------
        # AGREEMENT BONUS
        # ----------------------------------------------------

        agreement_bonus = 0


        if (
            row["rule_anomaly_flag"] == 1
            and
            row["ml_anomaly_flag"] == 1
        ):

            agreement_bonus = 10


        # ----------------------------------------------------
        # FINAL SCORE
        # ----------------------------------------------------

        risk_score = min(
            rule_risk
            +
            ml_risk
            +
            agreement_bonus,
            100
        )


        # ----------------------------------------------------
        # RISK LEVEL
        # ----------------------------------------------------

        if risk_score >= 70:

            risk_level = "HIGH"

        elif risk_score >= 40:

            risk_level = "MEDIUM"

        else:

            risk_level = "LOW"


        # ----------------------------------------------------
        # EXPLANATION
        # ----------------------------------------------------

        reasons = []


        if rule_count > 0:

            reasons.append(
                f"{rule_count} rule violation(s)"
            )


        if row["ml_anomaly_flag"] == 1:

            reasons.append(
                "Isolation Forest anomaly "
                f"({row['ml_anomaly_severity']})"
            )


        if agreement_bonus > 0:

            reasons.append(
                "Rule engine and ML both "
                "detected the anomaly"
            )


        if len(reasons) == 0:

            reasons.append(
                "No anomaly signal detected"
            )


        risk_scores.append(
            int(risk_score)
        )

        risk_levels.append(
            risk_level
        )

        risk_reasons.append(
            "; ".join(reasons)
        )


    conditions["risk_score"] = (
        risk_scores
    )

    conditions["risk_level"] = (
        risk_levels
    )

    conditions["risk_explanation"] = (
        risk_reasons
    )


    return conditions