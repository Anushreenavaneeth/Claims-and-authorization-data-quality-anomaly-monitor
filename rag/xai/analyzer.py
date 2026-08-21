"""
XAI / RCA / Recommendation Engine

Flow:

ML Output
    ↓
Dataset Adapter
    ↓
Normalized Evidence
    ↓
RAG Retrieval
    ↓
Retrieved Knowledge
    ↓
XAI Analyzer
    ↓
Root Cause Analysis
    ↓
Resolution
    ↓
Recommendation
"""

from typing import Any, Dict, List


class XAIAnalyzer:
    """
    Explainable AI layer for the healthcare
    data-quality anomaly platform.

    Responsibilities:
        1. Interpret normalized ML evidence
        2. Combine evidence with retrieved knowledge
        3. Generate likely root cause
        4. Generate remediation procedure
        5. Generate admin summary
        6. Generate employee action
        7. Generate final recommendation

    Important:
        XAI does not independently claim a root cause
        as confirmed fact. Root causes are expressed
        as likely and require verification.
    """

    # =====================================================
    # RULE → REASON MAPPING
    # =====================================================

    RULE_REASON_MAP = {

        "EXCESSIVE_IMPORTANT_MISSINGNESS":
            "At least 50% of important fields are missing.",

        "EXCESSIVE_SUPPRESSED_VALUES":
            "Record contains 10 or more suppressed or "
            "non-numeric values.",

        "unusual_cost_per_claim_change":
            "Cost per claim changed unusually compared "
            "with historical behavior."
    }

    # =====================================================
    # MAIN ANALYSIS
    # =====================================================

    def analyze(
        self,
        anomaly: Dict[str, Any],
        retrieved_knowledge
    ) -> Dict[str, Any]:

        # -------------------------------------------------
        # Dataset
        # -------------------------------------------------

        dataset_type = str(
            anomaly.get(
                "dataset_type",
                "unknown"
            )
        ).lower()

        record_id = anomaly.get(
            "record_id",
            "unknown"
        )

        # -------------------------------------------------
        # Detection Summary
        # -------------------------------------------------

        detection = anomaly.get(
            "detection_summary",
            {}
        )

        if not isinstance(
            detection,
            dict
        ):
            detection = {}

        final_anomaly = bool(
            detection.get(
                "final_anomaly",
                False
            )
        )

        severity = str(
            detection.get(
                "final_severity",
                "LOW"
            )
        ).upper()

        risk_score = self._get_risk_score(
            anomaly
        )

        # =================================================
        # NO ANOMALY
        #
        # No RCA / no remediation for clean records.
        # =================================================

        if not final_anomaly:

            return self._build_no_anomaly_result(
                dataset_type=dataset_type,
                record_id=record_id,
                severity=severity,
                risk_score=risk_score
            )

        # =================================================
        # EXTRACT EVIDENCE
        # =================================================

        rule_evidence = (
            self._get_rule_evidence(
                anomaly
            )
        )

        ml_evidence = (
            self._get_ml_evidence(
                anomaly
            )
        )

        bayesian_evidence = (
            self._get_bayesian_evidence(
                anomaly
            )
        )

        behavioral_evidence = (
            self._get_behavioral_evidence(
                anomaly
            )
        )

        source_explanation = (
            self._get_source_explanation(
                anomaly
            )
        )

        # =================================================
        # ANOMALY DESCRIPTION
        # =================================================

        anomaly_description = (
            self._build_anomaly_description(
                dataset_type=dataset_type,
                anomaly=anomaly,
                severity=severity,
                rule_evidence=rule_evidence,
                ml_evidence=ml_evidence,
                bayesian_evidence=bayesian_evidence,
                behavioral_evidence=behavioral_evidence,
                source_explanation=source_explanation
            )
        )

        # =================================================
        # RETRIEVED KNOWLEDGE
        #
        # Normalize both possible retriever formats:
        #
        # FORMAT A:
        #
        # [
        #     {
        #         "metadata": {...},
        #         "text": "..."
        #     }
        # ]
        #
        # FORMAT B:
        #
        # {
        #     "record_count": 1,
        #     "records": [
        #         {
        #             "results": [...]
        #         }
        #     ]
        # }
        # =================================================

        normalized_retrieved_knowledge = (
            self._normalize_retrieved_knowledge(
                retrieved_knowledge
            )
        )

        knowledge_analysis = (
            self._analyze_knowledge(
                normalized_retrieved_knowledge
            )
        )

        supporting_sources = (
            knowledge_analysis[
                "supporting_sources"
            ]
        )

        knowledge_text = (
            knowledge_analysis[
                "knowledge_text"
            ]
        )

        # =================================================
        # ROOT CAUSE
        # =================================================

        root_cause = (
            self._build_root_cause(
                dataset_type=dataset_type,
                anomaly=anomaly,
                rule_evidence=rule_evidence,
                ml_evidence=ml_evidence,
                bayesian_evidence=bayesian_evidence,
                behavioral_evidence=behavioral_evidence,
                source_explanation=source_explanation,
                knowledge_text=knowledge_text,
                supporting_sources=supporting_sources
            )
        )

        # =================================================
        # RESOLUTION
        # =================================================

        resolution = (
            self._build_resolution(
                dataset_type=dataset_type,
                anomaly=anomaly,
                rule_evidence=rule_evidence,
                ml_evidence=ml_evidence,
                behavioral_evidence=behavioral_evidence,
                source_explanation=source_explanation,
                knowledge_text=knowledge_text
            )
        )

        # =================================================
        # ADMIN SUMMARY
        # =================================================

        admin_summary = (
            self._build_admin_summary(
                dataset_type=dataset_type,
                record_id=record_id,
                severity=severity,
                anomaly_description=anomaly_description,
                root_cause=root_cause
            )
        )

        # =================================================
        # EMPLOYEE ACTION
        # =================================================

        employee_action = resolution.get(
            "procedure",
            ""
        )

        # =================================================
        # FINAL RECOMMENDATION
        # =================================================

        recommendation = (
            self._build_recommendation(
                dataset_type=dataset_type,
                anomaly_description=anomaly_description,
                severity=severity,
                root_cause=root_cause,
                resolution=resolution
            )
        )

        # =================================================
        # FINAL STRUCTURED OUTPUT
        # =================================================

        return {

            "record_id":
                record_id,

            "dataset_type":
                dataset_type,

            "anomaly":
                anomaly_description,

            "severity":
                severity,

            "risk_score":
                risk_score,

            "explanation":
                self._build_explanation(
                    anomaly_description=anomaly_description,
                    rule_evidence=rule_evidence,
                    ml_evidence=ml_evidence,
                    bayesian_evidence=bayesian_evidence,
                    behavioral_evidence=behavioral_evidence,
                    source_explanation=source_explanation
                ),

            "evidence_matching": {

                "evidence_terms":
                    self._build_evidence_terms(
                        dataset_type=dataset_type,
                        rule_evidence=rule_evidence,
                        ml_evidence=ml_evidence,
                        bayesian_evidence=bayesian_evidence,
                        behavioral_evidence=behavioral_evidence,
                        source_explanation=source_explanation
                    ),

                "match_count":
                    self._calculate_match_count(
                        dataset_type=dataset_type,
                        rule_evidence=rule_evidence,
                        ml_evidence=ml_evidence,
                        bayesian_evidence=bayesian_evidence,
                        behavioral_evidence=behavioral_evidence,
                        source_explanation=source_explanation
                    ),

                "matched_sources":
                    supporting_sources
            },

            "root_cause":
                root_cause,

            "resolution":
                resolution,

            "admin_summary":
                admin_summary,

            "employee_action":
                employee_action,

            "recommendation":
                recommendation
        }

    # =====================================================
    # NORMALIZE RETRIEVED KNOWLEDGE
    # =====================================================

    def _normalize_retrieved_knowledge(
        self,
        retrieved_knowledge
    ) -> List[Dict[str, Any]]:

        normalized_results = []

        # -------------------------------------------------
        # Case 1:
        # Direct list of knowledge chunks
        # -------------------------------------------------

        if isinstance(
            retrieved_knowledge,
            list
        ):

            for item in retrieved_knowledge:

                if isinstance(
                    item,
                    dict
                ):

                    normalized_results.append(
                        item
                    )

        # -------------------------------------------------
        # Case 2:
        # Complete retriever response
        # -------------------------------------------------

        elif isinstance(
            retrieved_knowledge,
            dict
        ):

            records = (
                retrieved_knowledge.get(
                    "records",
                    []
                )
            )

            if isinstance(
                records,
                list
            ):

                for record in records:

                    if not isinstance(
                        record,
                        dict
                    ):
                        continue

                    results = (
                        record.get(
                            "results",
                            []
                        )
                    )

                    if not isinstance(
                        results,
                        list
                    ):
                        continue

                    for item in results:

                        if isinstance(
                            item,
                            dict
                        ):

                            normalized_results.append(
                                item
                            )

        return normalized_results

    # =====================================================
    # KNOWLEDGE ANALYSIS
    # =====================================================

    def _analyze_knowledge(
        self,
        retrieved_knowledge
    ) -> Dict[str, Any]:

        supporting_sources = []

        knowledge_text_parts = []

        # =================================================
        # Normalize again defensively
        # =================================================

        normalized_results = (
            self._normalize_retrieved_knowledge(
                retrieved_knowledge
            )
        )

        # =================================================
        # Extract source + text
        # =================================================

        for item in normalized_results:

            if not isinstance(
                item,
                dict
            ):
                continue

            metadata = item.get(
                "metadata",
                {}
            )

            if not isinstance(
                metadata,
                dict
            ):

                metadata = {}

            # -------------------------------------------------
            # Primary source location
            # -------------------------------------------------

            source = metadata.get(
                "source"
            )

            if source:

                source = str(
                    source
                ).strip()

                if (
                    source
                    and source not in supporting_sources
                ):

                    supporting_sources.append(
                        source
                    )

            # -------------------------------------------------
            # Knowledge text
            # -------------------------------------------------

            text = item.get(
                "text",
                ""
            )

            if text:

                knowledge_text_parts.append(
                    str(text).strip()
                )

        # =================================================
        # FALLBACK SOURCE EXTRACTION
        #
        # Handles different metadata conventions.
        # =================================================

        if not supporting_sources:

            for item in normalized_results:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                metadata = item.get(
                    "metadata",
                    {}
                )

                if not isinstance(
                    metadata,
                    dict
                ):

                    metadata = {}

                possible_sources = [

                    item.get(
                        "source"
                    ),

                    item.get(
                        "document_source"
                    ),

                    metadata.get(
                        "file"
                    ),

                    metadata.get(
                        "filename"
                    ),

                    metadata.get(
                        "file_name"
                    ),

                    metadata.get(
                        "document"
                    )
                ]

                for source in possible_sources:

                    if not source:
                        continue

                    source = str(
                        source
                    ).strip()

                    if (
                        source
                        and source not in supporting_sources
                    ):

                        supporting_sources.append(
                            source
                        )

        # =================================================
        # Combined knowledge text
        # =================================================

        knowledge_text = "\n\n".join(
            knowledge_text_parts
        )

        return {

            "supporting_sources":
                supporting_sources,

            "knowledge_text":
                knowledge_text
        }

    # =====================================================
    # RISK SCORE
    # =====================================================

    def _get_risk_score(
        self,
        anomaly
    ):

        detection = anomaly.get(
            "detection_summary",
            {}
        )

        if not isinstance(
            detection,
            dict
        ):
            return None

        value = detection.get(
            "final_risk_score"
        )

        if value is None:
            return None

        try:

            return float(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            return None

    # =====================================================
    # RULE EVIDENCE
    # =====================================================

    def _get_rule_evidence(
        self,
        anomaly
    ) -> List[Dict[str, Any]]:

        evidence = anomaly.get(
            "rule_based_evidence",
            []
        )

        if not isinstance(
            evidence,
            list
        ):

            return []

        return evidence

    # =====================================================
    # ML EVIDENCE
    # =====================================================

    def _get_ml_evidence(
        self,
        anomaly
    ) -> Dict[str, Any]:

        evidence = anomaly.get(
            "ml_based_evidence",
            {}
        )

        if not isinstance(
            evidence,
            dict
        ):

            return {}

        return evidence

    # =====================================================
    # BAYESIAN EVIDENCE
    # =====================================================

    def _get_bayesian_evidence(
        self,
        anomaly
    ) -> Dict[str, Any]:

        evidence = anomaly.get(
            "bayesian_evidence",
            {}
        )

        if not isinstance(
            evidence,
            dict
        ):

            return {}

        return evidence

    # =====================================================
    # BEHAVIORAL EVIDENCE
    # =====================================================

    def _get_behavioral_evidence(
        self,
        anomaly
    ) -> List[Dict[str, Any]]:

        evidence = anomaly.get(
            "behavioral_evidence",
            []
        )

        if not isinstance(
            evidence,
            list
        ):

            return []

        return evidence

    # =====================================================
    # SOURCE EXPLANATION
    # =====================================================

    def _get_source_explanation(
        self,
        anomaly
    ) -> str:

        source_explanation = anomaly.get(
            "source_explanation",
            {}
        )

        if isinstance(
            source_explanation,
            dict
        ):

            value = source_explanation.get(
                "explanation",
                ""
            )

            if value:

                return str(
                    value
                )

        if isinstance(
            source_explanation,
            str
        ):

            return source_explanation

        return ""

    # =====================================================
    # ANOMALY DESCRIPTION
    # =====================================================

    def _build_anomaly_description(
        self,
        dataset_type,
        anomaly,
        severity,
        rule_evidence,
        ml_evidence,
        bayesian_evidence,
        behavioral_evidence,
        source_explanation
    ) -> str:

        # -------------------------------------------------
        # Claims
        # -------------------------------------------------

        if dataset_type == "claims":

            rule_names = []

            for evidence in rule_evidence:

                rule_name = evidence.get(
                    "rule_name"
                )

                if rule_name:

                    rule_names.append(
                        str(
                            rule_name
                        )
                    )

            if rule_names:

                return (
                    "Claims data quality anomaly: "
                    + ", ".join(
                        rule_names
                    )
                )

            if source_explanation:

                return (
                    "Claims anomaly: "
                    + source_explanation
                )

            return (
                "Claims data quality anomaly"
            )

        # -------------------------------------------------
        # Pharmacy
        # -------------------------------------------------

        if dataset_type == "pharmacy":

            if source_explanation:

                return source_explanation

            rule_names = []

            for evidence in rule_evidence:

                rule_name = evidence.get(
                    "rule_name"
                )

                if rule_name:

                    rule_names.append(
                        str(
                            rule_name
                        )
                    )

            if rule_names:

                return (
                    "Pharmacy anomaly: "
                    + ", ".join(
                        rule_names
                    )
                )

            return (
                "Pharmacy data quality anomaly"
            )

        # -------------------------------------------------
        # Authorization
        # -------------------------------------------------

        if dataset_type == "authorization":

            if source_explanation:

                return source_explanation

            return (
                "Authorization data quality anomaly"
            )

        return (
            f"{dataset_type.capitalize()} "
            "data quality anomaly"
        )

    # =====================================================
    # EXPLANATION
    # =====================================================

    def _build_explanation(
        self,
        anomaly_description,
        rule_evidence,
        ml_evidence,
        bayesian_evidence,
        behavioral_evidence,
        source_explanation
    ) -> str:

        parts = [
            anomaly_description
        ]

        # -------------------------------------------------
        # Rule evidence
        # -------------------------------------------------

        rule_names = []

        for evidence in rule_evidence:

            rule_name = evidence.get(
                "rule_name"
            )

            if rule_name:

                rule_names.append(
                    str(
                        rule_name
                    )
                )

        if rule_names:

            parts.append(
                "Rule evidence: "
                + ", ".join(
                    rule_names
                )
            )

        # -------------------------------------------------
        # ML evidence
        # -------------------------------------------------

        ml_anomaly = ml_evidence.get(
            "is_anomaly",
            ml_evidence.get(
                "anomaly",
                False
            )
        )

        if ml_anomaly:

            parts.append(
                "ML evidence indicates "
                "anomalous behavior."
            )

        # -------------------------------------------------
        # Bayesian evidence
        # -------------------------------------------------

        if bayesian_evidence.get(
            "anomaly",
            False
        ):

            parts.append(
                "Bayesian evidence also "
                "indicates anomalous behavior."
            )

        # -------------------------------------------------
        # Behavioral evidence
        # -------------------------------------------------

        if behavioral_evidence:

            detected = any(
                bool(
                    item.get(
                        "detected",
                        False
                    )
                )
                for item in behavioral_evidence
                if isinstance(
                    item,
                    dict
                )
            )

            if detected:

                parts.append(
                    "Behavioral evidence indicates "
                    "a deviation from expected behavior."
                )

        # -------------------------------------------------
        # Source explanation
        # -------------------------------------------------

        if (
            source_explanation
            and source_explanation
            not in parts
        ):

            # Avoid unnecessary duplication
            pass

        return " ".join(
            parts
        )

    # =====================================================
    # EVIDENCE TERMS
    # =====================================================

    def _build_evidence_terms(
        self,
        dataset_type,
        rule_evidence,
        ml_evidence,
        bayesian_evidence,
        behavioral_evidence,
        source_explanation
    ) -> List[str]:

        terms = []

        # -------------------------------------------------
        # Dataset
        # -------------------------------------------------

        if dataset_type:

            terms.append(
                dataset_type
            )

        # -------------------------------------------------
        # Signal types
        # -------------------------------------------------

        if rule_evidence:

            terms.append(
                "Rule"
            )

        if behavioral_evidence:

            terms.append(
                "Behavioral"
            )

        if bayesian_evidence.get(
            "anomaly",
            False
        ):

            terms.append(
                "Bayesian"
            )

        # -------------------------------------------------
        # Rule names
        # -------------------------------------------------

        for evidence in rule_evidence:

            rule_name = evidence.get(
                "rule_name"
            )

            if rule_name:

                terms.append(
                    str(
                        rule_name
                    )
                )

        # -------------------------------------------------
        # Semantic terms from evidence
        # -------------------------------------------------

        text = (
            source_explanation
            or ""
        ).lower()

        semantic_terms = [

            "bayesian",
            "behavioral",
            "cost_per_claim",
            "historical_behavior",
            "behavior",
            "claims",
            "missing",
            "suppressed",
            "provider",
            "payer",
            "authorization",
            "pharmacy"
        ]

        for term in semantic_terms:

            if term in text:

                terms.append(
                    term
                )

        # -------------------------------------------------
        # Deduplicate
        # -------------------------------------------------

        unique_terms = []

        for term in terms:

            if (
                term
                and term not in unique_terms
            ):

                unique_terms.append(
                    term
                )

        return unique_terms

    # =====================================================
    # MATCH COUNT
    # =====================================================

    def _calculate_match_count(
        self,
        dataset_type,
        rule_evidence,
        ml_evidence,
        bayesian_evidence,
        behavioral_evidence,
        source_explanation
    ) -> int:

        return len(
            self._build_evidence_terms(
                dataset_type=dataset_type,
                rule_evidence=rule_evidence,
                ml_evidence=ml_evidence,
                bayesian_evidence=bayesian_evidence,
                behavioral_evidence=behavioral_evidence,
                source_explanation=source_explanation
            )
        )

    # =====================================================
    # ROOT CAUSE
    # =====================================================

    def _build_root_cause(
        self,
        dataset_type,
        anomaly,
        rule_evidence,
        ml_evidence,
        bayesian_evidence,
        behavioral_evidence,
        source_explanation,
        knowledge_text,
        supporting_sources
    ) -> Dict[str, Any]:

        causes = []

        basis = []

        # -------------------------------------------------
        # Rule causes
        # -------------------------------------------------

        for evidence in rule_evidence:

            rule_name = evidence.get(
                "rule_name"
            )

            reason = evidence.get(
                "reason"
            )

            if not reason:

                reason = self.RULE_REASON_MAP.get(
                    rule_name,
                    "Rule violation detected."
                )

            if rule_name:

                causes.append(
                    f"{rule_name}: {reason}"
                )

                if "rule_evidence" not in basis:

                    basis.append(
                        "rule_evidence"
                    )

        # -------------------------------------------------
        # ML cause
        # -------------------------------------------------

        ml_anomaly = ml_evidence.get(
            "is_anomaly",
            ml_evidence.get(
                "anomaly",
                False
            )
        )

        if ml_anomaly:

            ml_summary = (
                ml_evidence.get(
                    "summary"
                )
                or ml_evidence.get(
                    "details"
                )
                or "ML model identified anomalous behavior."
            )

            causes.append(
                str(
                    ml_summary
                )
            )

            basis.append(
                "ml_evidence"
            )

        # -------------------------------------------------
        # Bayesian cause
        # -------------------------------------------------

        if bayesian_evidence.get(
            "anomaly",
            False
        ):

            probability = bayesian_evidence.get(
                "probability"
            )

            causes.append(
                "Bayesian evidence indicates "
                f"anomalous behavior "
                f"(probability={probability})."
            )

            basis.append(
                "bayesian_evidence"
            )

        # -------------------------------------------------
        # Behavioral cause
        # -------------------------------------------------

        for evidence in behavioral_evidence:

            if not isinstance(
                evidence,
                dict
            ):
                continue

            if evidence.get(
                "detected",
                False
            ):

                description = evidence.get(
                    "description",
                    "Behavioral deviation detected."
                )

                causes.append(
                    "Possible abnormal change in "
                    "historical pharmacy cost behavior."
                    if dataset_type == "pharmacy"
                    else str(
                        description
                    )
                )

                basis.append(
                    "behavioral_evidence"
                )

                break

        # -------------------------------------------------
        # Knowledge-supported fallback
        # -------------------------------------------------

        if (
            not causes
            and knowledge_text
        ):

            causes.append(
                "The retrieved knowledge base contains "
                "relevant guidance for the detected "
                f"{dataset_type} data-quality anomaly."
            )

            basis.append(
                "knowledge_base"
            )

        # -------------------------------------------------
        # Generic fallback
        # -------------------------------------------------

        if not causes:

            causes.append(
                f"The {dataset_type} record shows "
                "anomalous data-quality behavior "
                "requiring investigation."
            )

            basis.append(
                "source_evidence"
            )

        # -------------------------------------------------
        # Confidence
        # -------------------------------------------------

        evidence_count = len(
            basis
        )

        if evidence_count >= 3:

            confidence = "High"

        elif evidence_count == 2:

            confidence = "Medium"

        else:

            confidence = "Medium"

        return {

            "status":
                "likely",

            "cause":
                "; ".join(
                    causes
                ),

            "basis":
                list(
                    dict.fromkeys(
                        basis
                    )
                ),

            "supporting_sources":
                supporting_sources,

            "confidence":
                confidence,

            "verification_required":
                True
        }

    # =====================================================
    # RESOLUTION
    # =====================================================

    def _build_resolution(
        self,
        dataset_type,
        anomaly,
        rule_evidence,
        ml_evidence,
        behavioral_evidence,
        source_explanation,
        knowledge_text
    ) -> Dict[str, Any]:

        # -------------------------------------------------
        # Claims
        # -------------------------------------------------

        if dataset_type == "claims":

            procedure = (
                "Review the affected Claims record "
                "for missing or null important fields. "
                "Validate schema requirements, "
                "source-system transmission, field "
                "mapping, and transformation logic. "
                "Correct missing values where valid "
                "source data exists, revalidate the "
                "record, and reprocess only after "
                "validation succeeds."
            )

            pattern = (
                "Excessive important-field missingness"
            )

        # -------------------------------------------------
        # Pharmacy
        # -------------------------------------------------

        elif dataset_type == "pharmacy":

            procedure = (
                "Review the affected Pharmacy record "
                "against the source system and its "
                "historical baseline. Validate cost "
                "per claim, claim volume, related "
                "pharmacy metrics, and the detected "
                "behavioral change. Confirm whether "
                "the rule-based and Bayesian signals "
                "represent a genuine data-quality "
                "issue. Correct the underlying data "
                "if required, revalidate, and reprocess "
                "only after validation succeeds."
            )

            pattern = (
                "Unusual pharmacy "
                "cost-per-claim behavior"
            )

        # -------------------------------------------------
        # Authorization
        # -------------------------------------------------

        elif dataset_type == "authorization":

            procedure = (
                "Review the affected Authorization "
                "record against the source system and "
                "applicable authorization validation "
                "rules. Correct the underlying issue, "
                "revalidate the record, and reprocess "
                "only after validation succeeds."
            )

            pattern = (
                "Authorization data-quality anomaly"
            )

        # -------------------------------------------------
        # Generic
        # -------------------------------------------------

        else:

            procedure = (
                f"Review the affected {dataset_type} "
                "record against the source system and "
                "applicable healthcare data-quality "
                "procedures. Correct the underlying "
                "issue, revalidate the record, and "
                "reprocess only after validation "
                "succeeds."
            )

            pattern = (
                f"{dataset_type} data-quality anomaly"
            )

        return {

            "status":
                "review_required",

            "procedure":
                procedure,

            "basis":
                "evidence_and_knowledge_base",

            "anomaly_pattern":
                pattern,

            "verification_required":
                True
        }

    # =====================================================
    # ADMIN SUMMARY
    # =====================================================

    def _build_admin_summary(
        self,
        dataset_type,
        record_id,
        severity,
        anomaly_description,
        root_cause
    ) -> str:

        cause = root_cause.get(
            "cause",
            ""
        )

        return (
            f"{dataset_type.capitalize()} anomaly "
            f"detected for record {record_id} "
            f"with {severity} severity. "
            f"{anomaly_description} "
            f"Likely root cause: {cause} "
            "Operational action: review and "
            "validate before reprocessing."
        )

    # =====================================================
    # RECOMMENDATION
    # =====================================================

    def _build_recommendation(
        self,
        dataset_type,
        anomaly_description,
        severity,
        root_cause,
        resolution
    ) -> str:

        cause = root_cause.get(
            "cause",
            ""
        )

        procedure = resolution.get(
            "procedure",
            ""
        )

        return (
            f"The record contains a "
            f"{dataset_type.capitalize()} "
            f"data-quality issue: "
            f"{anomaly_description} "
            f"Likely cause: {cause} "
            f"Recommended action: {procedure} "
            f"This issue should be handled with "
            f"{severity.capitalize()} priority."
        )

    # =====================================================
    # NO ANOMALY RESULT
    # =====================================================

    def _build_no_anomaly_result(
        self,
        dataset_type,
        record_id,
        severity,
        risk_score
    ) -> Dict[str, Any]:

        return {

            "record_id":
                record_id,

            "dataset_type":
                dataset_type,

            "anomaly":
                False,

            "severity":
                severity,

            "risk_score":
                risk_score
                if risk_score is not None
                else 0.0,

            "explanation":
                f"No significant "
                f"{dataset_type.capitalize()} "
                "data-quality anomaly was detected.",

            "evidence_matching": {

                "evidence_terms":
                    [],

                "match_count":
                    0,

                "matched_sources":
                    []
            },

            "root_cause":
                None,

            "resolution":
                None,

            "admin_summary":
                f"{dataset_type.capitalize()} "
                f"record {record_id} does not "
                "currently show a final anomaly. "
                "No remediation is required.",

            "employee_action":
                "No action required. "
                "Continue normal processing.",

            "recommendation":
                "No remediation required. "
                "The record passed the current "
                "data-quality anomaly checks."
        }