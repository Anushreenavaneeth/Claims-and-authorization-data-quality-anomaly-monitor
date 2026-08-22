# pipeline/output_builder.py

from typing import Dict, List, Any, Optional


class OutputBuilder:
    """
    Builds the final CTS_V2 anomaly output.

    Output format:

    {
        "record_id": {
            "plan_id": "...",
            "issuer_id": "..."
        },

        "entity": {
            "state": "...",
            "issuer_name": "...",
            "plan_type": "...",
            "metal_level": "...",
            "exchange_type": "...",
            "individual_or_shop": "..."
        },

        "final_assessment": {
            "anomaly": true,
            "severity": "MEDIUM",
            "signal_count": 1,
            "signals": "Rule"
        },

        "bayesian": {
            "anomaly": false,
            "score": 0.0,
            "probability": 0.0,
            "threshold": 0.0
        },

        "rule_engine": {
            "anomaly": true,
            "rule_count": 1,
            "rule_name": "...",
            "reason": "...",
            "severity": "MEDIUM"
        },

        "ml_evidence": {
            "evidence_count": 0,
            "severity": "",
            "types": "",
            "features": "",
            "details": "",
            "summary": ""
        }
    }

    Normal records return None.
    """

    PROJECT_NAME = (
        "TC-PUF Claims and Authorization "
        "Data Quality Anomaly Monitor"
    )

    SCHEMA_VERSION = "1.0"

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(
        self,
        anomaly_threshold: float = 0.50,
    ):
        self.anomaly_threshold = anomaly_threshold

    # ==========================================================
    # SAFE FLOAT
    # ==========================================================

    @staticmethod
    def _safe_float(
        value,
        default: float = 0.0,
    ) -> float:

        try:

            if value is None:
                return default

            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return default

    # ==========================================================
    # SAFE BOOL
    # ==========================================================

    @staticmethod
    def _safe_bool(
        value,
        default: bool = False,
    ) -> bool:

        if value is None:
            return default

        if isinstance(value, bool):
            return value

        if isinstance(value, str):

            return (
                value.strip().lower()
                in {
                    "true",
                    "1",
                    "yes",
                    "y",
                }
            )

        return bool(value)

    # ==========================================================
    # SAFE STRING
    # ==========================================================

    @staticmethod
    def _safe_string(
        value,
        default: str = "",
    ) -> str:

        if value is None:
            return default

        return str(value)

    # ==========================================================
    # CLEAN RULE CAUSES
    # ==========================================================

    @staticmethod
    def _clean_rule_causes(
        causes: Optional[
            List[Dict[str, Any]]
        ],
    ) -> List[Dict[str, Any]]:

        cleaned = []

        for cause in causes or []:

            if not isinstance(
                cause,
                dict,
            ):
                continue

            cleaned.append(
                {
                    "cause":
                        cause.get(
                            "cause",
                            "unknown",
                        ),

                    "description":
                        cause.get(
                            "description",
                            "",
                        ),
                }
            )

        return cleaned

    # ==========================================================
    # CLEAN BAYESIAN CAUSES
    # ==========================================================

    @staticmethod
    def _clean_bayesian_causes(
        causes: Optional[
            List[Dict[str, Any]]
        ],
    ) -> List[Dict[str, Any]]:

        cleaned = []

        for cause in causes or []:

            if not isinstance(
                cause,
                dict,
            ):
                continue

            cleaned.append(
                {
                    "cause":
                        cause.get(
                            "cause",
                            "unknown",
                        ),

                    "probability_given_anomaly":
                        round(
                            OutputBuilder._safe_float(
                                cause.get(
                                    "probability_given_anomaly",
                                    0.0,
                                )
                            ),
                            4,
                        ),

                    "baseline_probability":
                        round(
                            OutputBuilder._safe_float(
                                cause.get(
                                    "baseline_probability",
                                    0.0,
                                )
                            ),
                            4,
                        ),

                    "bayesian_lift":
                        round(
                            OutputBuilder._safe_float(
                                cause.get(
                                    "bayesian_lift",
                                    0.0,
                                )
                            ),
                            4,
                        ),
                }
            )

        return cleaned

    # ==========================================================
    # EXTRACT ENTITY
    # ==========================================================

    @staticmethod
    def _build_entity(
        record_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:

        record_data = (
            record_data
            if isinstance(
                record_data,
                dict,
            )
            else {}
        )

        return {
            "state":
                record_data.get(
                    "state",
                    record_data.get(
                        "State",
                        "",
                    ),
                ),

            "issuer_name":
                record_data.get(
                    "issuer_name",
                    record_data.get(
                        "Issuer_Name",
                        "",
                    ),
                ),

            "plan_type":
                record_data.get(
                    "plan_type",
                    record_data.get(
                        "Plan_Type",
                        "",
                    ),
                ),

            "metal_level":
                record_data.get(
                    "metal_level",
                    record_data.get(
                        "Metal_Level",
                        "",
                    ),
                ),

            "exchange_type":
                record_data.get(
                    "exchange_type",
                    record_data.get(
                        "Exchange_Type",
                        "",
                    ),
                ),

            "individual_or_shop":
                record_data.get(
                    "individual_or_shop",
                    record_data.get(
                        "Individual_or_Shop",
                        "",
                    ),
                ),
        }

    # ==========================================================
    # BUILD RECORD ID
    # ==========================================================

    @staticmethod
    def _build_record_id(
        record_id: Any,
        record_data: Optional[
            Dict[str, Any]
        ],
    ) -> Dict[str, Any]:

        record_data = (
            record_data
            if isinstance(
                record_data,
                dict,
            )
            else {}
        )

        # If record_id is already a dictionary
        if isinstance(
            record_id,
            dict,
        ):

            return {
                "plan_id":
                    record_id.get(
                        "plan_id",
                        record_id.get(
                            "Plan_ID",
                            "",
                        ),
                    ),

                "issuer_id":
                    record_id.get(
                        "issuer_id",
                        record_id.get(
                            "Issuer_ID",
                            "",
                        ),
                    ),
            }

        # Otherwise try the row
        plan_id = record_data.get(
            "plan_id",
            record_data.get(
                "Plan_ID",
                "",
            ),
        )

        issuer_id = record_data.get(
            "issuer_id",
            record_data.get(
                "Issuer_ID",
                "",
            ),
        )

        return {
            "plan_id":
                plan_id
                if plan_id
                else record_id,

            "issuer_id":
                issuer_id,
        }

    # ==========================================================
    # EXTRACT ML EVIDENCE
    # ==========================================================

    @staticmethod
    def _build_ml_evidence(
        evidence: Dict[str, Any],
    ) -> Dict[str, Any]:

        ml_evidence = evidence.get(
            "ml_evidence",
            {},
        )

        if not isinstance(
            ml_evidence,
            dict,
        ):

            ml_evidence = {}

        return {
            "evidence_count":
                ml_evidence.get(
                    "evidence_count",
                    0,
                ),

            "severity":
                ml_evidence.get(
                    "severity",
                    "",
                ),

            "types":
                ml_evidence.get(
                    "types",
                    "",
                ),

            "features":
                ml_evidence.get(
                    "features",
                    "",
                ),

            "details":
                ml_evidence.get(
                    "details",
                    "",
                ),

            "summary":
                ml_evidence.get(
                    "summary",
                    "",
                ),
        }

    # ==========================================================
    # EXTRACT BAYESIAN RESULT
    # ==========================================================

    def _build_bayesian(
        self,
        evidence: Dict[str, Any],
        bayesian_root_causes:
            List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        bayesian_data = evidence.get(
            "bayesian",
            {},
        )

        if not isinstance(
            bayesian_data,
            dict,
        ):

            bayesian_data = {}

        anomaly = self._safe_bool(
            bayesian_data.get(
                "anomaly",
                False,
            )
        )

        probability = (
            self._safe_float(
                bayesian_data.get(
                    "probability",
                    0.0,
                )
            )
        )

        score = (
            self._safe_float(
                bayesian_data.get(
                    "score",
                    0.0,
                )
            )
        )

        threshold = (
            self._safe_float(
                bayesian_data.get(
                    "threshold",
                    0.0,
                )
            )
        )

        # If explicit Bayesian root causes
        # exist, Bayesian evidence is present.
        if (
            bayesian_root_causes
            and not anomaly
        ):
            anomaly = True

        return {
            "anomaly":
                anomaly,

            "score":
                score,

            "probability":
                probability,

            "threshold":
                threshold,
        }

    # ==========================================================
    # EXTRACT RULE ENGINE RESULT
    # ==========================================================

    def _build_rule_engine(
        self,
        evidence: Dict[str, Any],
        rule_root_causes:
            List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        rule_data = evidence.get(
            "rule_engine",
            evidence.get(
                "rule_based",
                {},
            ),
        )

        if not isinstance(
            rule_data,
            dict,
        ):

            rule_data = {}

        anomaly = self._safe_bool(
            rule_data.get(
                "anomaly",
                False,
            )
        )

        if (
            rule_root_causes
            and not anomaly
        ):
            anomaly = True

        rule_names = []
        reasons = []

        for cause in (
            rule_root_causes or []
        ):

            if not isinstance(
                cause,
                dict,
            ):
                continue

            rule_name = cause.get(
                "rule",
                cause.get(
                    "cause",
                    "",
                ),
            )

            reason = cause.get(
                "description",
                cause.get(
                    "reason",
                    "",
                ),
            )

            if rule_name:
                rule_names.append(
                    str(rule_name)
                )

            if reason:
                reasons.append(
                    str(reason)
                )

        rule_name = (
            rule_data.get(
                "rule_name",
                "",
            )
        )

        reason = (
            rule_data.get(
                "reason",
                "",
            )
        )

        if (
            not rule_name
            and rule_names
        ):

            rule_name = ";".join(
                rule_names
            )

        if (
            not reason
            and reasons
        ):

            reason = ";".join(
                reasons
            )

        rule_count = (
            rule_data.get(
                "rule_count",
                len(rule_names),
            )
        )

        severity = (
            rule_data.get(
                "severity",
                "NONE",
            )
        )

        return {
            "anomaly":
                anomaly,

            "rule_count":
                rule_count,

            "rule_name":
                rule_name,

            "reason":
                reason,

            "severity":
                severity,
        }

    # ==========================================================
    # FINAL SEVERITY
    # ==========================================================

    @staticmethod
    def _calculate_severity(
        evidence: Dict[str, Any],
        rule_result: Dict[str, Any],
        bayesian_result: Dict[str, Any],
        ml_result: Dict[str, Any],
    ) -> str:

        severities = []

        rule_severity = (
            rule_result.get(
                "severity",
                "",
            )
        )

        if rule_severity:
            severities.append(
                str(rule_severity).upper()
            )

        ml_severity = (
            ml_result.get(
                "severity",
                "",
            )
        )

        if ml_severity:
            severities.append(
                str(ml_severity).upper()
            )

        for severity in (
            "HIGH",
            "MEDIUM",
            "LOW",
        ):

            if severity in severities:
                return severity

        # Fallback
        if (
            bayesian_result.get(
                "anomaly",
                False,
            )
        ):
            return "MEDIUM"

        return "LOW"

    # ==========================================================
    # BUILD ONE RECORD
    # ==========================================================

    def build_record(
        self,
        record_id: Any,
        evidence: Optional[
            Dict[str, Any]
        ] = None,
        rule_root_causes:
            Optional[
                List[Dict[str, Any]]
            ] = None,
        bayesian_root_causes:
            Optional[
                List[Dict[str, Any]]
            ] = None,
        sla_result:
            Optional[
                Dict[str, Any]
            ] = None,
        record_data:
            Optional[
                Dict[str, Any]
            ] = None,

        # Compatibility with the current
        # anomaly_pipeline implementation.
        fusion_result:
            Optional[
                Dict[str, Any]
            ] = None,

        isolation_result:
            Optional[
                Dict[str, Any]
            ] = None,
    ) -> Optional[Dict[str, Any]]:

        evidence = (
            evidence
            if isinstance(
                evidence,
                dict,
            )
            else {}
        )

        rule_root_causes = (
            rule_root_causes
            or []
        )

        bayesian_root_causes = (
            bayesian_root_causes
            or []
        )

        sla_result = (
            sla_result
            if isinstance(
                sla_result,
                dict,
            )
            else {}
        )

        record_data = (
            record_data
            if isinstance(
                record_data,
                dict,
            )
            else {}
        )

        # ------------------------------------------------------
        # Compatibility: merge supplied results
        # ------------------------------------------------------

        if (
            fusion_result
            and isinstance(
                fusion_result,
                dict,
            )
        ):

            evidence["fusion"] = (
                fusion_result
            )

        if (
            isolation_result
            and isinstance(
                isolation_result,
                dict,
            )
        ):

            evidence[
                "isolation_forest"
            ] = isolation_result

        # ------------------------------------------------------
        # Rule result
        # ------------------------------------------------------

        rule_result = (
            self._build_rule_engine(
                evidence,
                rule_root_causes,
            )
        )

        # ------------------------------------------------------
        # Bayesian result
        # ------------------------------------------------------

        bayesian_result = (
            self._build_bayesian(
                evidence,
                bayesian_root_causes,
            )
        )

        # ------------------------------------------------------
        # ML evidence
        # ------------------------------------------------------

        ml_result = (
            self._build_ml_evidence(
                evidence
            )
        )

        # ------------------------------------------------------
        # Detection sources
        # ------------------------------------------------------

        isolation = evidence.get(
            "isolation_forest",
            {},
        )

        clustering = evidence.get(
            "clustering",
            {},
        )

        behavioral = evidence.get(
            "behavioral",
            {},
        )

        isolation_anomaly = (
            self._safe_bool(
                isolation.get(
                    "anomaly",
                    isolation.get(
                        "is_anomaly",
                        False,
                    ),
                )
            )
            if isinstance(
                isolation,
                dict,
            )
            else False
        )

        clustering_anomaly = (
            self._safe_bool(
                clustering.get(
                    "anomaly",
                    clustering.get(
                        "is_anomaly",
                        False,
                    ),
                )
            )
            if isinstance(
                clustering,
                dict,
            )
            else False
        )

        behavioral_anomaly = (
            self._safe_bool(
                behavioral.get(
                    "anomaly",
                    behavioral.get(
                        "is_anomaly",
                        False,
                    ),
                )
            )
            if isinstance(
                behavioral,
                dict,
            )
            else False
        )

        rule_anomaly = (
            rule_result["anomaly"]
        )

        bayesian_anomaly = (
            bayesian_result["anomaly"]
        )

        # ------------------------------------------------------
        # Final anomaly decision
        # ------------------------------------------------------

        anomaly_detected = (
            rule_anomaly
            or isolation_anomaly
            or clustering_anomaly
            or behavioral_anomaly
            or bayesian_anomaly
        )

        # Fusion can also confirm an anomaly.
        fusion = evidence.get(
            "fusion",
            {},
        )

        if isinstance(
            fusion,
            dict,
        ):

            anomaly_detected = (
                anomaly_detected
                or self._safe_bool(
                    fusion.get(
                        "multi_source_anomaly",
                        False,
                    )
                )
                or (
                    self._safe_float(
                        fusion.get(
                            "fusion_score",
                            0.0,
                        )
                    )
                    >= self.anomaly_threshold
                )
            )

        # ------------------------------------------------------
        # IMPORTANT:
        # Normal records are NOT written to JSON.
        # ------------------------------------------------------

        if not anomaly_detected:
            return None

        # ------------------------------------------------------
        # Signal names
        # ------------------------------------------------------

        signals = []

        if rule_anomaly:
            signals.append("Rule")

        if isolation_anomaly:
            signals.append(
                "Isolation Forest"
            )

        if clustering_anomaly:
            signals.append(
                "Clustering"
            )

        if behavioral_anomaly:
            signals.append(
                "Behavioral"
            )

        if bayesian_anomaly:
            signals.append(
                "Bayesian"
            )

        if (
            ml_result.get(
                "evidence_count",
                0,
            )
            and "ML Evidence"
            not in signals
        ):

            signals.append(
                "ML Evidence"
            )

        severity = (
            self._calculate_severity(
                evidence,
                rule_result,
                bayesian_result,
                ml_result,
            )
        )

        # ------------------------------------------------------
        # Build final record
        # ------------------------------------------------------

        return {
            "record_id":
                self._build_record_id(
                    record_id,
                    record_data,
                ),

            "entity":
                self._build_entity(
                    record_data
                ),

            "final_assessment": {
                "anomaly":
                    True,

                "severity":
                    severity,

                "signal_count":
                    len(signals),

                "signals":
                    ", ".join(
                        signals
                    ),
            },

            "bayesian":
                bayesian_result,

            "rule_engine":
                rule_result,

            "ml_evidence":
                ml_result,
        }

    # ==========================================================
    # BUILD BATCH
    # ==========================================================

    def build_batch(
        self,
        records: List[
            Optional[
                Dict[str, Any]
            ]
        ],
    ) -> List[Dict[str, Any]]:

        return [
            record
            for record in records
            if isinstance(
                record,
                dict,
            )
        ]

    # ==========================================================
    # BUILD FINAL DOCUMENT
    # ==========================================================

    def build_document(
        self,
        records: List[
            Optional[
                Dict[str, Any]
            ]
        ],
    ) -> Dict[str, Any]:

        anomaly_records = (
            self.build_batch(
                records
            )
        )

        return {
            "project":
                self.PROJECT_NAME,

            "schema_version":
                self.SCHEMA_VERSION,

            "record_count":
                len(
                    anomaly_records
                ),

            "records":
                anomaly_records,
        }