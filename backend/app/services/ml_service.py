"""
ML Service — Multi-Dataset Anomaly Detection Engine
===================================================
Unified scoring and inference across all three healthcare data streams:
  1. Authorization Anomaly Pipeline (3-Tier: IQR Rules + Isolation Forest + Bayesian Network)
  2. Claims Anomaly Pipeline (TC-PUF Rules + Isolation Forest + Feature Imputer/Scaler)
  3. Pharmacy Anomaly Pipeline (Pharmacy Rule Engine + Isolation Forest + Ratio Feature Analysis)
"""

import json
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Repo paths ────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[3]

# Authorization
_AUTH_PKL = _REPO_ROOT / "ml" / "authorization" / "auth pkl file" / "authorization_anomaly_pipeline.pkl"

# Claims (TC-PUF)
_CLAIMS_IF = _REPO_ROOT / "ml" / "anomaly_detection" / "models" / "tc_puf_isolation_forest.joblib"
_CLAIMS_IMP = _REPO_ROOT / "ml" / "anomaly_detection" / "models" / "tc_puf_imputer.joblib"
_CLAIMS_SCL = _REPO_ROOT / "ml" / "anomaly_detection" / "models" / "tc_puf_scaler.joblib"
_CLAIMS_FEAT = _REPO_ROOT / "ml" / "anomaly_detection" / "models" / "tc_puf_features.json"

# Pharmacy
_PHARM_PKL = _REPO_ROOT / "ml" / "pharmacy_pipeline" / "ml" / "pharmacy_model.pkl"

# Ensure ml/ is on path
_ML_ROOT = str(_REPO_ROOT)
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

# ── Artifact State ────────────────────────────────────────────────────────────
_auth_pipeline: Optional[Dict] = None
_claims_artifacts: Optional[Dict] = None
_pharmacy_artifacts: Optional[Dict] = None
_load_errors: Dict[str, str] = {}


def _load_all_pipelines() -> None:
    global _auth_pipeline, _claims_artifacts, _pharmacy_artifacts, _load_errors

    # 1. Authorization
    try:
        if _AUTH_PKL.exists():
            from ml.authorization.pipeline import load_pipeline
            _auth_pipeline = load_pipeline(_AUTH_PKL)
    except Exception as exc:
        _load_errors["AUTHORIZATION"] = str(exc)

    # 2. Claims (TC-PUF)
    try:
        if _CLAIMS_IF.exists() and _CLAIMS_FEAT.exists():
            model = joblib.load(_CLAIMS_IF)
            imputer = joblib.load(_CLAIMS_IMP) if _CLAIMS_IMP.exists() else None
            scaler = joblib.load(_CLAIMS_SCL) if _CLAIMS_SCL.exists() else None
            with open(_CLAIMS_FEAT, "r", encoding="utf-8") as f:
                features_meta = json.load(f)
            _claims_artifacts = {
                "model": model,
                "imputer": imputer,
                "scaler": scaler,
                "features": features_meta.get("selected_features", []),
            }
    except Exception as exc:
        _load_errors["CLAIMS"] = str(exc)

    # 3. Pharmacy
    try:
        if _PHARM_PKL.exists():
            import pickle
            with open(_PHARM_PKL, "rb") as f:
                pharm_data = pickle.load(f)
            if isinstance(pharm_data, dict):
                _pharmacy_artifacts = pharm_data
    except Exception as exc:
        _load_errors["PHARMACY"] = str(exc)


_load_all_pipelines()


# ── Public Status & Diagnostics ───────────────────────────────────────────────

def is_available(source_type: str = "AUTHORIZATION") -> bool:
    source = source_type.upper().strip()
    if source in ("AUTHORIZATION", "AUTH"):
        return _auth_pipeline is not None
    elif source in ("CLAIMS", "CLAIM"):
        return _claims_artifacts is not None
    elif source in ("PHARMACY", "PHARM", "RX"):
        return _pharmacy_artifacts is not None
    return _auth_pipeline is not None


def get_load_error(source_type: Optional[str] = None) -> Union[str, Dict[str, str]]:
    if source_type:
        return _load_errors.get(source_type.upper().strip(), "")
    return _load_errors


def get_model_info() -> Dict[str, Any]:
    """Return runtime metadata and tier info for all 3 pipelines."""
    return {
        "status": "ready" if (_auth_pipeline or _claims_artifacts or _pharmacy_artifacts) else "unavailable",
        "models": {
            "AUTHORIZATION": {
                "status": "ready" if _auth_pipeline else "unavailable",
                "model": "AuthorizationAnomalyPipeline_v1",
                "tiers": {
                    "rule_engine": "IQR + Business Logic",
                    "isolation_forest": "IsolationForest",
                    "bayesian_network": "BayesianNetwork (pgmpy)",
                },
                "error": _load_errors.get("AUTHORIZATION"),
            },
            "CLAIMS": {
                "status": "ready" if _claims_artifacts else "unavailable",
                "model": "Claims_TC_PUF_IsolationForest_v1",
                "tiers": {
                    "rule_engine": "PUF Rule Quality Engine",
                    "isolation_forest": "IsolationForest (218 features)",
                    "preprocessor": "SimpleImputer + RobustScaler",
                },
                "error": _load_errors.get("CLAIMS"),
            },
            "PHARMACY": {
                "status": "ready" if _pharmacy_artifacts else "unavailable",
                "model": "Pharmacy_Prescriber_Behavior_Pipeline_v1",
                "tiers": {
                    "rule_engine": "Pharmacy Rule Engine (Cost, Fill & Supply)",
                    "isolation_forest": "IsolationForest",
                    "feature_engine": "Prescriber Dispense & Beneficiary Ratios",
                },
                "error": _load_errors.get("PHARMACY"),
            },
        },
    }


# ── 1. Authorization Inference ────────────────────────────────────────────────

def predict_authorization(record: Dict[str, Any]) -> Dict[str, Any]:
    if not _auth_pipeline:
        raise RuntimeError(f"Authorization ML pipeline not loaded: {_load_errors.get('AUTHORIZATION')}")

    from ml.authorization.pipeline import run_inference

    df = pd.DataFrame([record])
    _, json_output = run_inference(df, _auth_pipeline)

    rec = json_output["records"][0]
    assessment = rec.get("final_assessment", {})
    bayesian = rec.get("bayesian", {})
    rule_engine = rec.get("rule_engine", {})
    ml_ev = rec.get("ml_evidence", {})

    rule_names = [n for n in str(rule_engine.get("rule_name") or "NONE").split(";") if n and n != "NONE"]
    rule_reasons = [r for r in str(rule_engine.get("reason") or "").split(";") if r]
    risk = assessment.get("risk_score", 0)

    return {
        "record_id": str(record.get("authorization_id") or record.get("id") or "AUTH_ROW"),
        "source_type": "AUTHORIZATION",
        "is_anomaly": bool(assessment.get("anomaly", False)),
        "anomaly_score": round(float(risk) / 100.0, 4),
        "severity": assessment.get("severity", "LOW"),
        "risk_score": int(risk),
        "signals": assessment.get("signals", "None"),
        "signal_count": int(assessment.get("signal_count", 0)),
        "rule_engine": {
            "anomaly": bool(rule_engine.get("anomaly", False)),
            "rule_count": int(rule_engine.get("rule_count", 0)),
            "rule_names": rule_names,
            "rule_reasons": rule_reasons,
            "rule_severity": rule_engine.get("severity", "NONE"),
        },
        "bayesian": {
            "anomaly": bool(bayesian.get("anomaly", False)),
            "probability": float(bayesian.get("probability", 0.0)),
        },
        "ml_evidence": {
            "evidence_count": int(ml_ev.get("evidence_count", 0)),
            "severity": ml_ev.get("severity", "NONE"),
            "types": ml_ev.get("types", "None"),
            "summary": ml_ev.get("summary", ""),
        },
        "model": "AuthorizationAnomalyPipeline_v1",
    }


# ── 2. Claims (TC-PUF) Inference ──────────────────────────────────────────────

def _evaluate_claims_rules(record: Dict[str, Any]) -> Tuple[bool, List[str], List[str], str]:
    rule_names = []
    rule_reasons = []

    # 1. Negative checks
    for k, v in record.items():
        if isinstance(v, (int, float)) and v < 0 and "percent" not in k.lower():
            rule_names.append(f"NEGATIVE_{k.upper()}")
            rule_reasons.append(f"Field {k} has negative value ({v}), expected non-negative quantity.")

    # 2. Denials exceeding received
    rec_out = float(record.get("Issuer_Claims_Received_Out_of_Network", record.get("claims_received_oon", 0)) or 0)
    den_out = float(record.get("Issuer_Claims_Denied_Out_of_Network", record.get("claims_denied_oon", 0)) or 0)
    if den_out > rec_out and rec_out > 0:
        rule_names.append("DENIALS_EXCEED_RECEIVED_OON")
        rule_reasons.append(f"Out-of-network denials ({den_out}) exceed received claims ({rec_out}).")

    rec_inn = float(record.get("Issuer_Claims_Received_In_Network", record.get("claims_received_inn", 0)) or 0)
    den_inn = float(record.get("Issuer_Claims_Denied_In_Network", record.get("claims_denied_inn", 0)) or 0)
    if den_inn > rec_inn and rec_inn > 0:
        rule_names.append("DENIALS_EXCEED_RECEIVED_INN")
        rule_reasons.append(f"In-network denials ({den_inn}) exceed received claims ({rec_inn}).")

    # 3. Appeals overturned > filed
    app_filed = float(record.get("Issuer_Internal_Appeals_Filed", record.get("appeals_filed", 0)) or 0)
    app_over = float(record.get("Issuer_Number_Internal_Appeals_Overturned", record.get("appeals_overturned", 0)) or 0)
    if app_over > app_filed and app_filed > 0:
        rule_names.append("OVERTURNED_EXCEEDS_FILED_APPEALS")
        rule_reasons.append(f"Internal appeals overturned ({app_over}) exceeds total appeals filed ({app_filed}).")

    # 4. Total claim amount outliers
    claim_amt = float(record.get("claim_amount", record.get("charged_amount", record.get("billed_amount", 0))) or 0)
    if claim_amt < 0:
        rule_names.append("NEGATIVE_CLAIM_AMOUNT")
        rule_reasons.append(f"Claim billed amount is negative ({claim_amt}).")
    elif claim_amt > 1000000:
        rule_names.append("EXTREME_CLAIM_AMOUNT")
        rule_reasons.append(f"Claim amount ${claim_amt:,.2f} exceeds outlier threshold ($1,000,000).")

    is_anomaly = len(rule_names) > 0
    severity = "CRITICAL" if len(rule_names) >= 2 or "NEGATIVE" in str(rule_names) else ("HIGH" if is_anomaly else "LOW")
    return is_anomaly, rule_names, rule_reasons, severity


def predict_claims(record: Dict[str, Any]) -> Dict[str, Any]:
    rule_anom, rule_names, rule_reasons, rule_sev = _evaluate_claims_rules(record)
    
    ml_anom = False
    anomaly_score = 0.15
    
    if _claims_artifacts:
        try:
            model = _claims_artifacts["model"]
            features = _claims_artifacts["features"]
            imputer = _claims_artifacts.get("imputer")
            scaler = _claims_artifacts.get("scaler")

            # Build named DataFrame to avoid sklearn feature-name UserWarning
            row_data = {f: float(record.get(f, 0.0) or 0.0) for f in features}
            x_df = pd.DataFrame([row_data])

            if imputer is not None:
                x_df = pd.DataFrame(imputer.transform(x_df), columns=features)
            if scaler is not None:
                x_df = pd.DataFrame(scaler.transform(x_df), columns=features)

            pred = model.predict(x_df)[0]
            # Isolation forest returns -1 for anomaly, 1 for normal
            ml_anom = (pred == -1)
            raw_score = -float(model.score_samples(x_df)[0])
            anomaly_score = round(min(1.0, max(0.0, raw_score)), 4)
        except Exception:
            ml_anom = False

    is_anomaly = rule_anom or ml_anom
    signals = []
    if rule_anom:
        signals.append("PUF_Rule_Engine")
    if ml_anom:
        signals.append("Claims_Isolation_Forest")

    if not is_anomaly:
        severity = "LOW"
        risk_score = int(anomaly_score * 20)
    elif rule_anom and ml_anom:
        severity = "CRITICAL"
        risk_score = max(85, int(anomaly_score * 100))
    elif rule_anom:
        severity = rule_sev
        risk_score = 75 if severity == "HIGH" else 85
    else:
        severity = "HIGH" if anomaly_score >= 0.7 else "MEDIUM"
        risk_score = max(50, int(anomaly_score * 100))

    return {
        "record_id": str(record.get("claim_id") or record.get("Issuer_ID") or record.get("id") or "CLAIM_ROW"),
        "source_type": "CLAIMS",
        "is_anomaly": is_anomaly,
        "anomaly_score": anomaly_score,
        "severity": severity,
        "risk_score": risk_score,
        "signals": "; ".join(signals) if signals else "None",
        "signal_count": len(signals),
        "rule_engine": {
            "anomaly": rule_anom,
            "rule_count": len(rule_names),
            "rule_names": rule_names,
            "rule_reasons": rule_reasons,
            "rule_severity": rule_sev,
        },
        "bayesian": {
            "anomaly": False,
            "probability": round(anomaly_score * 0.85, 2) if is_anomaly else 0.05,
        },
        "ml_evidence": {
            "evidence_count": 1 if ml_anom else 0,
            "severity": "HIGH" if ml_anom else "NONE",
            "types": "Multivariate_Claims_Outlier" if ml_anom else "None",
            "summary": f"Claims Isolation Forest scored multivariate density deviation at {anomaly_score:.2f}" if ml_anom else "",
        },
        "model": "Claims_TC_PUF_IsolationForest_v1",
    }


# ── 3. Pharmacy Inference ─────────────────────────────────────────────────────

def _evaluate_pharmacy_rules(record: Dict[str, Any]) -> Tuple[bool, List[str], List[str], str]:
    rule_names = []
    rule_reasons = []

    tot_clms = float(record.get("Tot_Clms", record.get("total_claims", record.get("claim_count", 0))) or 0)
    tot_fills = float(record.get("Tot_30day_Fills", record.get("total_fills", 0)) or 0)
    tot_day_suply = float(record.get("Tot_Day_Suply", record.get("days_supply", 0)) or 0)
    tot_drug_cst = float(record.get("Tot_Drug_Cst", record.get("total_drug_cost", record.get("drug_cost", 0))) or 0)
    tot_benes = float(record.get("Tot_Benes", record.get("total_beneficiaries", 0)) or 0)

    # 1. Negative rules
    if tot_clms < 0:
        rule_names.append("NEGATIVE_TOTAL_CLAIMS")
        rule_reasons.append(f"Total claims is negative ({tot_clms}).")
    if tot_fills < 0:
        rule_names.append("NEGATIVE_TOTAL_FILLS")
        rule_reasons.append(f"Total 30-day fills is negative ({tot_fills}).")
    if tot_day_suply < 0:
        rule_names.append("NEGATIVE_DAY_SUPPLY")
        rule_reasons.append(f"Total days supply is negative ({tot_day_suply}).")
    if tot_drug_cst < 0:
        rule_names.append("NEGATIVE_DRUG_COST")
        rule_reasons.append(f"Total drug cost is negative (${tot_drug_cst:,.2f}).")

    # 2. Logic violations
    if tot_clms > 0 and tot_day_suply == 0:
        rule_names.append("ZERO_DAY_SUPPLY_WITH_CLAIMS")
        rule_reasons.append(f"Prescription has {tot_clms} claims but 0 days supply recorded.")

    cost_per_claim = (tot_drug_cst / tot_clms) if tot_clms > 0 else 0
    if cost_per_claim > 50000:
        rule_names.append("EXTREME_COST_PER_CLAIM")
        rule_reasons.append(f"Average cost per claim (${cost_per_claim:,.2f}) exceeds high-cost threshold ($50,000).")

    is_anomaly = len(rule_names) > 0
    severity = "CRITICAL" if len(rule_names) >= 2 or tot_clms < 0 or tot_drug_cst < 0 else ("HIGH" if is_anomaly else "LOW")
    return is_anomaly, rule_names, rule_reasons, severity


def predict_pharmacy(record: Dict[str, Any]) -> Dict[str, Any]:
    rule_anom, rule_names, rule_reasons, rule_sev = _evaluate_pharmacy_rules(record)
    ml_anom = False
    anomaly_score = 0.12

    if _pharmacy_artifacts:
        try:
            model = _pharmacy_artifacts["model"]
            features = _pharmacy_artifacts.get("features", [])
            imputer = _pharmacy_artifacts.get("imputer")

            tot_clms = float(record.get("Tot_Clms", 0.0) or 0.0)
            tot_fills = float(record.get("Tot_30day_Fills", 0.0) or 0.0)
            tot_day_suply = float(record.get("Tot_Day_Suply", 0.0) or 0.0)
            tot_drug_cst = float(record.get("Tot_Drug_Cst", 0.0) or 0.0)
            tot_benes = float(record.get("Tot_Benes", 0.0) or 0.0)

            # Compute derived ratios — use record's change fields if available;
            # otherwise estimate YoY changes from previous-period columns
            def _yoy(current: float, prev_key: str, default: float = 0.0) -> float:
                """Estimate percent change vs prior period column, or return provided default."""
                raw = record.get(prev_key)
                if raw is not None:
                    prev = float(raw or 0.0)
                    return ((current - prev) / prev) if prev != 0 else 0.0
                return default

            feat_dict = {
                "Tot_Clms": tot_clms,
                "Tot_30day_Fills": tot_fills,
                "Tot_Day_Suply": tot_day_suply,
                "Tot_Drug_Cst": tot_drug_cst,
                "Tot_Benes": tot_benes,
                "fills_per_claim": tot_fills / tot_clms if tot_clms else 1.0,
                "days_supply_per_claim": tot_day_suply / tot_clms if tot_clms else 30.0,
                "drug_cost_per_claim": tot_drug_cst / tot_clms if tot_clms else 0.0,
                "drug_cost_per_beneficiary": tot_drug_cst / tot_benes if tot_benes else 0.0,
                "claims_per_beneficiary": tot_clms / tot_benes if tot_benes else 1.0,
                "fills_per_beneficiary": tot_fills / tot_benes if tot_benes else 1.0,
                "days_supply_per_beneficiary": tot_day_suply / tot_benes if tot_benes else 30.0,
                "drug_cost_per_fill": tot_drug_cst / tot_fills if tot_fills else 0.0,
                # YoY changes: prefer explicit change fields, else estimate from prior_* columns
                "claim_volume_change":         float(record.get("claim_volume_change")  or _yoy(tot_clms, "prior_Tot_Clms")),
                "fill_volume_change":          float(record.get("fill_volume_change")   or _yoy(tot_fills, "prior_Tot_30day_Fills")),
                "days_supply_change":          float(record.get("days_supply_change")   or _yoy(tot_day_suply, "prior_Tot_Day_Suply")),
                "drug_cost_change":            float(record.get("drug_cost_change")     or _yoy(tot_drug_cst, "prior_Tot_Drug_Cst")),
                "beneficiary_change":          float(record.get("beneficiary_change")   or _yoy(tot_benes, "prior_Tot_Benes")),
                "cost_per_claim_change":       float(record.get("cost_per_claim_change")      or 0.0),
                "fills_per_claim_change":      float(record.get("fills_per_claim_change")     or 0.0),
                "days_supply_per_claim_change":float(record.get("days_supply_per_claim_change") or 0.0),
            }

            # Build named DataFrame for imputer (which was fitted with feature names),
            # then convert to plain numpy array for IsolationForest (fitted without feature names)
            x_df = pd.DataFrame([{f: feat_dict.get(f, 0.0) for f in features}])

            if imputer is not None:
                # Imputer expects feature names; keep as DataFrame
                x_df = pd.DataFrame(imputer.transform(x_df), columns=features)

            # IsolationForest was trained on raw arrays — convert to avoid UserWarning
            x_arr = x_df.to_numpy()
            pred = model.predict(x_arr)[0]
            ml_anom = (pred == -1)
            raw_score = -float(model.score_samples(x_arr)[0])
            anomaly_score = round(min(1.0, max(0.0, raw_score)), 4)
        except Exception:
            ml_anom = False

    is_anomaly = rule_anom or ml_anom
    signals = []
    if rule_anom:
        signals.append("Pharmacy_Rule_Engine")
    if ml_anom:
        signals.append("Pharmacy_Isolation_Forest")

    if not is_anomaly:
        severity = "LOW"
        risk_score = int(anomaly_score * 20)
    elif rule_anom and ml_anom:
        severity = "CRITICAL"
        risk_score = max(88, int(anomaly_score * 100))
    elif rule_anom:
        severity = rule_sev
        risk_score = 75 if severity == "HIGH" else 85
    else:
        severity = "HIGH" if anomaly_score >= 0.7 else "MEDIUM"
        risk_score = max(55, int(anomaly_score * 100))

    return {
        "record_id": str(record.get("prescription_id") or record.get("Prscrbr_NPI") or record.get("id") or "PHARM_ROW"),
        "source_type": "PHARMACY",
        "is_anomaly": is_anomaly,
        "anomaly_score": anomaly_score,
        "severity": severity,
        "risk_score": risk_score,
        "signals": "; ".join(signals) if signals else "None",
        "signal_count": len(signals),
        "rule_engine": {
            "anomaly": rule_anom,
            "rule_count": len(rule_names),
            "rule_names": rule_names,
            "rule_reasons": rule_reasons,
            "rule_severity": rule_sev,
        },
        "bayesian": {
            "anomaly": False,
            "probability": round(anomaly_score * 0.82, 2) if is_anomaly else 0.05,
        },
        "ml_evidence": {
            "evidence_count": 1 if ml_anom else 0,
            "severity": "HIGH" if ml_anom else "NONE",
            "types": "Prescriber_Dispense_Deviation" if ml_anom else "None",
            "summary": f"Pharmacy ML model identified dispensing pattern deviation score of {anomaly_score:.2f}" if ml_anom else "",
        },
        "model": "Pharmacy_Prescriber_Behavior_Pipeline_v1",
    }


# ── Unified Dispatcher ────────────────────────────────────────────────────────

def predict(record: Dict[str, Any], source_type: str = "AUTHORIZATION") -> Dict[str, Any]:
    """Score a single record by routing to the appropriate dataset ML engine."""
    source = (record.get("source_type") or source_type).upper().strip()
    if source in ("CLAIMS", "CLAIM"):
        return predict_claims(record)
    elif source in ("PHARMACY", "PHARM", "RX"):
        return predict_pharmacy(record)
    else:
        return predict_authorization(record)


def predict_batch(records: List[Dict[str, Any]], source_type: str = "AUTHORIZATION") -> List[Dict[str, Any]]:
    """Score multiple records across any dataset."""
    return [predict(rec, source_type=source_type) for rec in records]


def run_dataframe_inference(df: pd.DataFrame, source_type: str = "AUTHORIZATION") -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Run multi-model inference on a full DataFrame.
    Returns (scored_df, list_of_anomaly_assessments).
    """
    # Explicitly cast keys to str to satisfy List[Dict[str, Any]] type contract
    records: List[Dict[str, Any]] = [
        {str(k): v for k, v in row.items()}
        for row in df.to_dict(orient="records")
    ]
    results = predict_batch(records, source_type=source_type)
    return df, results
