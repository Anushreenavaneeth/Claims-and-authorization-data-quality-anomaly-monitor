# pipeline/anomaly_pipeline.py

import json
import time
from pathlib import Path

import pandas as pd

from feature_engineering.feature_pipeline import (
    FeatureEngineeringPipeline,
)

from preprocessing.preprocessor import (
    MLPreprocessor,
)

from rules.rule_engine import (
    RuleEngine,
)

from rules.rule_classifier import (
    RuleClassifier,
)

from rules.evidence_scorer import (
    EvidenceScorer,
)

from models.isolation_forest import (
    IsolationForestDetector,
)

from models.clustering import (
    KMeansClusterDetector,
)

from models.ml_adapters import (
    MLAdapters,
)

from pipeline.adapters import (
    PipelineAdapters,
)

from pipeline.evidence_fusion import (
    EvidenceFusion,
)

from pipeline.root_cause_engine import (
    RootCauseEngine,
)

from pipeline.bayesian_root_cause import (
    BayesianRootCauseEngine,
)

from pipeline.sla_analyzer import (
    SLAAnalyzer,
)

from pipeline.output_builder import (
    OutputBuilder,
)

from models.bayesian_network import (
    BayesianAnomalyNetwork,
)


class AnomalyPipeline:
    """
    Complete pharmacy anomaly detection pipeline.

    Current + Historical Data
            ↓
    Feature Engineering
            ↓
    ML Preprocessing
            ↓
    Rule Engine
            ↓
    Rule Classification
            ↓
    Evidence Scoring
            ↓
    Isolation Forest
            ↓
    K-Means
            ↓
    Evidence Fusion
            ↓
    Bayesian Network
            ↓
    Root Cause Analysis
            ↓
    Bayesian Root Cause
            ↓
    SLA Analysis
            ↓
    Output Builder
            ↓
    Final JSON
    """

    # ==================================================
    # INITIALIZATION
    # ==================================================

    def __init__(
        self,
        current_df: pd.DataFrame,
        historical_df: pd.DataFrame,
    ):

        self.current_df = current_df.copy()

        self.historical_df = historical_df.copy()

        # ==================================================
        # ML FEATURES
        # ==================================================

        self.ml_features = [

            # Current features
            "Tot_Clms",
            "Tot_30day_Fills",
            "Tot_Day_Suply",
            "Tot_Drug_Cst",
            "Tot_Benes",

            # GE65 features
            "GE65_Tot_Clms",
            "GE65_Tot_30day_Fills",
            "GE65_Tot_Drug_Cst",
            "GE65_Tot_Day_Suply",
            "GE65_Tot_Benes",

            # Behavioral features
            "cost_per_claim",
            "claims_per_beneficiary",
            "cost_per_beneficiary",
            "day_supply_per_claim",
            "fills_per_claim",
            "cost_per_day_supply",

            # Historical features
            "claim_volume_change",
            "fill_volume_change",
            "days_supply_change",
            "drug_cost_change",
            "beneficiary_change",
            "cost_per_claim_change",
        ]

        # ==================================================
        # COMPONENTS
        # ==================================================

        self.rule_engine = RuleEngine()

        self.rule_classifier = RuleClassifier()

        self.evidence_scorer = EvidenceScorer()

        self.isolation_model = (
            IsolationForestDetector(
                contamination=0.01,
                n_estimators=200,
                random_state=42,
            )
        )

        self.cluster_model = (
            KMeansClusterDetector(
                n_clusters=5,
                n_init=10,
                max_iter=300,
                random_state=42,
            )
        )

        self.evidence_fusion = EvidenceFusion()

        self.root_cause_engine = RootCauseEngine()

        self.bayesian_root_cause = (
            BayesianRootCauseEngine()
        )

        self.sla_analyzer = SLAAnalyzer()

        self.output_builder = OutputBuilder()

        self.bayesian_network = (
            BayesianAnomalyNetwork()
        )

    # ==================================================
    # FEATURE ENGINEERING
    # ==================================================

    def build_features(self):

        pipeline = FeatureEngineeringPipeline(
            current_df=self.current_df,
            historical_df=self.historical_df,
        )

        return pipeline.create_features()

    # ==================================================
    # ML PREPROCESSING
    # ==================================================

    def preprocess(
        self,
        features_df: pd.DataFrame,
    ) -> pd.DataFrame:

        missing = [
            feature
            for feature in self.ml_features
            if feature not in features_df.columns
        ]

        if missing:

            raise ValueError(
                "Required ML features are missing: "
                f"{missing}"
            )

        preprocessor = MLPreprocessor(
            dataframe=features_df,
            feature_columns=self.ml_features,
        )

        return preprocessor.fit_transform()

    # ==================================================
    # MAIN PIPELINE
    # ==================================================

    def run(self):

        start_time = time.time()

        # ==================================================
        # 1. FEATURE ENGINEERING
        # ==================================================

        print(
            "\n========== FEATURE ENGINEERING =========="
        )

        features_df = self.build_features()

        print(
            "Feature shape:",
            features_df.shape,
        )

        # ==================================================
        # 2. ML PREPROCESSING
        # ==================================================

        print(
            "\n========== ML PREPROCESSING =========="
        )

        X = self.preprocess(
            features_df
        )

        print(
            "ML shape:",
            X.shape,
        )

        # ==================================================
        # 3. RULE ENGINE
        # ==================================================

        print(
            "\n========== RULE ENGINE =========="
        )

        rule_results = (
            self.rule_engine
            .evaluate_dataframe(
                features_df
            )
        )

        print(
            "Rule results:",
            rule_results.shape,
        )

        # ==================================================
        # 4. RULE ADAPTER
        # ==================================================

        normalized_rules = (
            PipelineAdapters
            .normalize_rule_results(
                rule_results
            )
        )

        # ==================================================
        # 5. ISOLATION FOREST
        # ==================================================

        print(
            "\n========== ISOLATION FOREST =========="
        )

        isolation_results = (
            self.isolation_model
            .fit_predict(X)
        )

        normalized_isolation = (
            MLAdapters
            .normalize_isolation_results(
                isolation_results,
                expected_records=len(
                    features_df
                ),
            )
        )

        print(
            "Isolation Forest completed."
        )

        # ==================================================
        # 6. K-MEANS
        # ==================================================

        print(
            "\n========== K-MEANS =========="
        )

        cluster_results = (
            self.cluster_model
            .fit_predict(X)
        )

        normalized_clusters = (
            MLAdapters
            .normalize_cluster_results(
                cluster_results,
                expected_records=len(
                    features_df
                ),
            )
        )

        print(
            "K-Means completed."
        )

        # ==================================================
        # 7. MERGE ML RESULTS
        # ==================================================

        ml_results = (
            MLAdapters.merge_ml_results(
                normalized_isolation,
                normalized_clusters,
            )
        )

        # ==================================================
        # 8. BAYESIAN NETWORK
        # ==================================================

        print(
            "\n========== BAYESIAN NETWORK =========="
        )

        self.bayesian_network.build()

        print(
            "Bayesian Network built."
        )

        # ==================================================
        # 9. RECORD PROCESSING
        # ==================================================

        print(
            "\n========== RECORD PROCESSING =========="
        )

        final_results = []

        total_records = len(
            features_df
        )

        for i in range(
            total_records
        ):

            # ==================================================
            # RULE RESULT
            # ==================================================

            rule_result = (
                normalized_rules[i]
            )

            # ==================================================
            # RULE CLASSIFICATION
            # ==================================================

            classified_rule = (
                self.rule_classifier
                .classify_result(
                    rule_result
                )
            )

            # ==================================================
            # EVIDENCE SCORING
            # ==================================================

            rule_evidence = (
                self.evidence_scorer
                .calculate(
                    classified_rule
                )
            )

            # ==================================================
            # ML RESULTS
            # ==================================================

            ml_result = ml_results[i]

            isolation = (
                ml_result[
                    "isolation_forest"
                ]
            )

            clustering = (
                ml_result[
                    "clustering"
                ]
            )

            # ==================================================
            # BEHAVIORAL EVIDENCE
            # ==================================================

            behavior_anomaly = (
                classified_rule.get(
                    "behavior_anomaly",
                    False,
                )
            )

            behavior_score = (
                rule_evidence.get(
                    "behavior_evidence_score",
                    0.0,
                )
            )

            # ==================================================
            # DATA QUALITY
            # ==================================================

            data_quality_issue = (
                classified_rule.get(
                    "data_quality_issue",
                    False,
                )
            )

            data_quality_score = (
                rule_evidence.get(
                    "data_quality_score",
                    0.0,
                )
            )

            # ==================================================
            # EVIDENCE FUSION
            # ==================================================

            fusion_rule_result = {

                **rule_result,

                "rule_evidence_score":
                    rule_evidence.get(
                        "rule_evidence_score",
                        0.0,
                    ),
            }

            behavioral_result = {

                "behavior_anomaly":
                    behavior_anomaly,

                "behavior_score":
                    behavior_score,
            }

            data_quality_result = {

                "data_quality_issue":
                    data_quality_issue,

                "data_quality_score":
                    data_quality_score,
            }

            fused = (
                self.evidence_fusion
                .fuse_record(

                    rule_result=
                        fusion_rule_result,

                    isolation_result=
                        isolation,

                    cluster_result=
                        clustering,

                    behavioral_result=
                        behavioral_result,

                    data_quality_result=
                        data_quality_result,
                )
            )

            # ==================================================
            # BAYESIAN NETWORK
            # ==================================================

            bayesian_probability = (
                self.bayesian_network
                .predict_probability(
                    {
                        "ML_Anomaly":
                            bool(
                                isolation.get(
                                    "is_anomaly",
                                    False,
                                )
                            ),

                        "Rule_Anomaly":
                            bool(
                                rule_result.get(
                                    "rule_anomaly",
                                    False,
                                )
                            ),

                        "Behavior_Anomaly":
                            bool(
                                behavior_anomaly
                            ),

                        "Cluster_Anomaly":
                            bool(
                                clustering.get(
                                    "is_anomaly",
                                    False,
                                )
                            ),

                        "Data_Quality_Issue":
                            bool(
                                data_quality_issue
                            ),

                        "SLA_Risk":
                            False,
                    }
                )
            )

            # ==================================================
            # RULE ROOT CAUSES
            # ==================================================

            root_cause_result = (
                self.root_cause_engine.build(
                    classified_rule
                )
            )

            root_causes = (
                root_cause_result.get(
                    "rule_based_root_causes",
                    [],
                )
            )

            # ==================================================
            # BAYESIAN ROOT CAUSES
            # ==================================================

            bayesian_probabilities = {

                "ML_Anomaly": {
                    "posterior": (
                        0.91
                        if isolation.get(
                            "is_anomaly",
                            False,
                        )
                        else 0.05
                    ),
                    "baseline": 0.15,
                },

                "Rule_Anomaly": {
                    "posterior": (
                        0.75
                        if rule_result.get(
                            "rule_anomaly",
                            False,
                        )
                        else 0.05
                    ),
                    "baseline": 0.15,
                },

                "Behavior_Anomaly": {
                    "posterior": (
                        0.75
                        if behavior_anomaly
                        else 0.05
                    ),
                    "baseline": 0.20,
                },

                "Cluster_Anomaly": {
                    "posterior": (
                        0.75
                        if clustering.get(
                            "is_anomaly",
                            False,
                        )
                        else 0.05
                    ),
                    "baseline": 0.20,
                },

                "Data_Quality_Issue": {
                    "posterior": (
                        0.65
                        if data_quality_issue
                        else 0.05
                    ),
                    "baseline": 0.25,
                },

                "SLA_Risk": {
                    "posterior": 0.05,
                    "baseline": 0.10,
                },
            }

            bayesian_causes = (
                self.bayesian_root_cause
                .build(
                    bayesian_probabilities
                )
            )

            # ==================================================
            # SLA ANALYSIS
            # ==================================================

            processing_time = (
                time.time()
                - start_time
            )

            sla_result = (
                self.sla_analyzer.analyze(
                    fused,
                    dataset_size=
                        total_records,
                    processing_time_seconds=
                        processing_time,
                )
            )

            # ==================================================
            # RECORD ID
            # ==================================================

            record_id = (
                features_df.iloc[i]
                .get(
                    "record_id",
                    features_df.iloc[i].get(
                        "Prscrbr_NPI",
                        i,
                    ),
                )
            )

            # ==================================================
            # FINAL OUTPUT
            # ==================================================

            final_record = (
                self.output_builder
                .build_record(

                    record_id=
                        record_id,

                    evidence=
                        fused,

                    rule_root_causes=
                        root_causes,

                    bayesian_root_causes=
                        bayesian_causes,

                    sla_result=
                        sla_result,
                )
            )

            final_results.append(
                final_record
            )

            # ==================================================
            # PROGRESS
            # ==================================================

            if (
                (i + 1) % 10000 == 0
            ):

                print(
                    f"Processed "
                    f"{i + 1:,}/"
                    f"{total_records:,}"
                )

        # ==================================================
        # COMPLETION
        # ==================================================

        total_time = (
            time.time()
            - start_time
        )

        anomaly_count = sum(
            1
            for record in final_results
            if record.get(
                "anomaly_detected",
                False,
            )
        )

        print(
            "\n========== PIPELINE COMPLETED =========="
        )

        print(
            "Total records:",
            len(final_results),
        )

        print(
            "Anomalies detected:",
            anomaly_count,
        )

        print(
            "Normal records:",
            len(final_results)
            - anomaly_count,
        )

        print(
            "Processing time:",
            round(
                total_time,
                2,
            ),
            "seconds",
        )

        return final_results


# ======================================================
# SAVE JSON
# ======================================================

def save_results(
    results,
    path="outputs/anomaly_results.json",
):
    """
    Save ONLY anomalous records.

    The pipeline processes every record internally,
    but normal records are excluded from the final
    JSON output.
    """

    output_path = Path(path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ==================================================
    # FILTER ANOMALIES ONLY
    # ==================================================

    anomaly_results = [
        record
        for record in results
        if record.get(
            "anomaly_detected",
            False,
        ) is True
    ]

    # ==================================================
    # SAVE JSON
    # ==================================================

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            anomaly_results,
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    # ==================================================
    # OUTPUT SUMMARY
    # ==================================================

    print(
        "\n========== JSON OUTPUT =========="
    )

    print(
        "Total pipeline records:",
        len(results),
    )

    print(
        "Anomaly records saved:",
        len(anomaly_results),
    )

    print(
        "Normal records excluded:",
        len(results)
        - len(anomaly_results),
    )

    print(
        "Results saved to:",
        output_path,
    )

    return output_path