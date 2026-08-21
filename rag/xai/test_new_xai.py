"""
Claims / Pharmacy / Authorization
ML -> Adapter -> Retrieval -> XAI

Full integration test.

Flow:

ML Output
    ↓
Adapter
    ↓
Normalized Evidence
    ↓
Query Builder / Retriever
    ↓
Knowledge Base
    ↓
XAI Analyzer
    ↓
Root Cause
    ↓
Resolution
    ↓
Admin Summary
    ↓
Employee Action
    ↓
Recommendation
"""

import json
import traceback

from rag.ingestion.adapters.claims_adapter import ClaimsAdapter
from rag.ingestion.adapters.pharmacy_adapter import PharmacyAdapter
from rag.ingestion.adapters.authorization_adapter import AuthorizationAdapter

from rag.retrieval.retriever import Retriever

from rag.xai.analyzer import XAIAnalyzer


# =========================================================
# CONFIGURATION
# =========================================================

CLAIMS_FILE = "tc_puf_final_anomaly_results.json"
PHARMACY_FILE = "anomaly_results.json"
AUTHORIZATION_FILE = "authorization.json"


CLAIMS_TARGET = {
    "plan_id": "10091OR0770001",
    "issuer_id": "10091"
}

PHARMACY_TARGET = {
    "plan_id": "1336143163",
    "issuer_id": ""
}

AUTHORIZATION_TARGET = {
    "authorization_id": "AUTH00001-2026A",
    "reference_number": "REF-PA-350001"
}


# =========================================================
# HEADER
# =========================================================

print("=" * 70)
print("CLAIMS / PHARMACY / AUTHORIZATION")
print("ML → ADAPTER → RETRIEVAL → XAI")
print("=" * 70)


# =========================================================
# INITIALIZE RETRIEVER
# =========================================================

print("\nInitializing Retriever...")

retriever = Retriever(
    top_k=5,
    similarity_threshold=0.35
)

print("Retriever initialized successfully.")


# =========================================================
# INITIALIZE XAI
# =========================================================

print("\nInitializing XAI Analyzer...")

xai_analyzer = XAIAnalyzer()


# =========================================================
# GENERIC JSON LOADER
# =========================================================

def load_json_file(
    file_path
):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    return data


# =========================================================
# FIND CLAIMS RECORD
# =========================================================

def find_claims_record(
    records,
    target
):

    for record in records:

        record_id = record.get(
            "record_id",
            {}
        )

        if not isinstance(
            record_id,
            dict
        ):

            continue

        if (
            record_id.get("plan_id")
            == target.get("plan_id")
            and
            record_id.get("issuer_id")
            == target.get("issuer_id")
        ):

            return record

    return None


# =========================================================
# FIND PHARMACY RECORD
# =========================================================

def find_pharmacy_record(
    records,
    target
):

    for record in records:

        record_id = record.get(
            "record_id",
            {}
        )

        if not isinstance(
            record_id,
            dict
        ):

            continue

        if (
            record_id.get("plan_id")
            == target.get("plan_id")
            and
            record_id.get("issuer_id", "")
            == target.get("issuer_id", "")
        ):

            return record

    return None


# =========================================================
# FIND AUTHORIZATION RECORD
# =========================================================

def find_authorization_record(
    records,
    target
):

    for record in records:

        record_id = record.get(
            "record_id",
            {}
        )

        if not isinstance(
            record_id,
            dict
        ):

            continue

        if (
            record_id.get("authorization_id")
            == target.get("authorization_id")
            and
            record_id.get("reference_number")
            == target.get("reference_number")
        ):

            return record

    return None


# =========================================================
# DISPLAY NORMALIZED EVIDENCE
# =========================================================

def display_normalized_evidence(
    adapted_record
):

    detection = adapted_record.get(
        "detection_summary",
        {}
    )

    print(
        f"Final anomaly: "
        f"{detection.get('final_anomaly')}"
    )

    print(
        f"Severity: "
        f"{detection.get('final_severity')}"
    )

    print(
        f"Anomaly type: "
        f"{detection.get('anomaly_type')}"
    )

    print(
        f"Bayesian anomaly: "
        f"{detection.get('bayesian_anomaly')}"
    )

    probability = detection.get(
        "bayesian_probability"
    )

    if probability is not None:

        print(
            f"Bayesian probability: "
            f"{probability}"
        )

    # -----------------------------------------------------
    # Rule evidence
    # -----------------------------------------------------

    rule_evidence = adapted_record.get(
        "rule_based_evidence",
        []
    )

    print(
        "\nRule evidence:"
    )

    if rule_evidence:

        for evidence in rule_evidence:

            print(
                f"- Rule: "
                f"{evidence.get('rule_name')}"
            )

            print(
                f"  Status: "
                f"{evidence.get('status')}"
            )

            print(
                f"  Reason: "
                f"{evidence.get('reason')}"
            )

            print(
                f"  Severity: "
                f"{evidence.get('severity')}"
            )

    else:

        print(
            "No rule evidence."
        )

    # -----------------------------------------------------
    # Behavioral evidence
    # -----------------------------------------------------

    behavioral_evidence = adapted_record.get(
        "behavioral_evidence",
        []
    )

    if behavioral_evidence:

        print(
            "\nBehavioral evidence:"
        )

        for evidence in behavioral_evidence:

            print(
                f"- Type: "
                f"{evidence.get('type')}"
            )

            print(
                f"  Detected: "
                f"{evidence.get('detected')}"
            )

            print(
                f"  Description: "
                f"{evidence.get('description')}"
            )

    # -----------------------------------------------------
    # Bayesian evidence
    # -----------------------------------------------------

    bayesian_evidence = adapted_record.get(
        "bayesian_evidence"
    )

    if bayesian_evidence:

        print(
            "\nBayesian evidence:"
        )

        print(
            f"- Anomaly: "
            f"{bayesian_evidence.get('anomaly')}"
        )

        print(
            f"- Score: "
            f"{bayesian_evidence.get('score')}"
        )

        print(
            f"- Probability: "
            f"{bayesian_evidence.get('probability')}"
        )

        print(
            f"- Threshold: "
            f"{bayesian_evidence.get('threshold')}"
        )

    # -----------------------------------------------------
    # Source explanation
    # -----------------------------------------------------

    source_explanation = adapted_record.get(
        "source_explanation",
        {}
    )

    explanation = source_explanation.get(
        "explanation"
    )

    if explanation:

        print(
            "\nSource explanation:"
        )

        print(
            explanation
        )


# =========================================================
# DISPLAY RETRIEVAL
# =========================================================

def display_retrieval(
    retrieval_result
):

    records = retrieval_result.get(
        "records",
        []
    )

    print(
        f"\nKnowledge chunks retrieved: "
        f"{len(records[0].get('results', [])) if records else 0}"
    )

    if not records:

        return

    retrieval_record = records[0]

    evidence_terms = retrieval_record.get(
        "evidence_terms",
        []
    )

    print(
        "\nEvidence terms:"
    )

    if evidence_terms:

        for term in evidence_terms:

            print(
                f"- {term}"
            )

    else:

        print(
            "No evidence terms."
        )


# =========================================================
# DISPLAY XAI RESULT
# =========================================================

def display_xai_result(
    xai_result
):

    print(
        "\n"
        + "=" * 70
    )

    print(
        "FINAL XAI RESULT"
    )

    print(
        "=" * 70
    )

    print(
        json.dumps(
            xai_result,
            indent=2,
            ensure_ascii=False
        )
    )


# =========================================================
# DISPLAY ROOT CAUSE
# =========================================================

def display_root_cause(
    xai_result
):

    print(
        "\n"
        + "=" * 70
    )

    print(
        "ROOT CAUSE"
    )

    print(
        "=" * 70
    )

    root_cause = xai_result.get(
        "root_cause"
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # Authorization with no anomaly can return None.
    # -----------------------------------------------------

    if root_cause is None:

        print(
            "No root cause analysis required."
        )

        return

    print(
        f"Status: "
        f"{root_cause.get('status', 'unknown')}"
    )

    print(
        f"Confidence: "
        f"{root_cause.get('confidence', 'unknown')}"
    )

    print(
        f"Cause: "
        f"{root_cause.get('cause', 'unknown')}"
    )

    print(
        "\nBasis:"
    )

    basis = root_cause.get(
        "basis",
        []
    )

    if basis:

        for item in basis:

            print(
                f"- {item}"
            )

    else:

        print(
            "No basis available."
        )

    print(
        "\nSupporting Sources:"
    )

    sources = root_cause.get(
        "supporting_sources",
        []
    )

    if sources:

        for source in sources:

            print(
                f"- {source}"
            )

    else:

        print(
            "No supporting sources."
        )


# =========================================================
# DISPLAY RESOLUTION
# =========================================================

def display_resolution(
    xai_result
):

    print(
        "\n"
        + "=" * 70
    )

    print(
        "RESOLUTION"
    )

    print(
        "=" * 70
    )

    resolution = xai_result.get(
        "resolution"
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # Authorization with no anomaly can return None.
    # -----------------------------------------------------

    if resolution is None:

        print(
            "No remediation required."
        )

        return

    print(
        f"Status: "
        f"{resolution.get('status', 'unknown')}"
    )

    print(
        f"Procedure: "
        f"{resolution.get('procedure', 'unknown')}"
    )

    print(
        f"Verification required: "
        f"{resolution.get('verification_required', False)}"
    )


# =========================================================
# DISPLAY ADMIN SUMMARY
# =========================================================

def display_admin_summary(
    xai_result
):

    print(
        "\n"
        + "=" * 70
    )

    print(
        "ADMIN SUMMARY"
    )

    print(
        "=" * 70
    )

    print(
        xai_result.get(
            "admin_summary",
            "No admin summary available."
        )
    )


# =========================================================
# DISPLAY EMPLOYEE ACTION
# =========================================================

def display_employee_action(
    xai_result
):

    print(
        "\n"
        + "=" * 70
    )

    print(
        "EMPLOYEE ACTION"
    )

    print(
        "=" * 70
    )

    print(
        xai_result.get(
            "employee_action",
            "No employee action required."
        )
    )


# =========================================================
# DISPLAY FINAL RECOMMENDATION
# =========================================================

def display_recommendation(
    xai_result
):

    print(
        "\n"
        + "=" * 70
    )

    print(
        "FINAL RECOMMENDATION"
    )

    print(
        "=" * 70
    )

    print(
        xai_result.get(
            "recommendation",
            "No remediation required."
        )
    )


# =========================================================
# PROCESS ONE DATASET
# =========================================================

def process_dataset(
    dataset_name,
    input_file,
    adapter,
    target,
    finder
):

    print(
        "\n"
        + "=" * 70
    )

    print(
        f"{dataset_name.upper()} XAI TEST"
    )

    print(
        "=" * 70
    )

    try:

        # =================================================
        # 1. LOAD ML OUTPUT
        # =================================================

        print(
            "\n[1] Loading ML output..."
        )

        data = load_json_file(
            input_file
        )

        if not isinstance(
            data,
            dict
        ):

            raise ValueError(
                f"{dataset_name} ML output "
                f"must be a JSON object."
            )

        records = data.get(
            "records",
            []
        )

        print(
            f"Total records: "
            f"{len(records)}"
        )

        if not records:

            raise ValueError(
                f"No records found in "
                f"{input_file}"
            )

        # =================================================
        # 2. FIND TARGET
        # =================================================

        target_record = finder(
            records,
            target
        )

        if target_record is None:

            raise ValueError(
                f"Target record not found "
                f"for {dataset_name}."
            )

        print(
            "\nTarget record:"
        )

        print(
            target_record.get(
                "record_id"
            )
        )

        # =================================================
        # 3. ADAPT RECORD
        # =================================================

        print(
            "\n[2] Adapting record..."
        )

        adapted_record = adapter.adapt_record(
            target_record
        )

        print(
            f"Dataset: "
            f"{adapted_record.get('dataset_type')}"
        )

        print(
            f"Record ID: "
            f"{adapted_record.get('record_id')}"
        )

        # =================================================
        # 4. NORMALIZED EVIDENCE
        # =================================================

        print(
            "\n[3] Normalized Evidence"
        )

        display_normalized_evidence(
            adapted_record
        )

        # =================================================
        # 5. RETRIEVAL
        # =================================================

        print(
            "\n[4] Running knowledge retrieval..."
        )

        retrieval_result = retriever.retrieve(
            adapted_record
        )

        if not isinstance(
            retrieval_result,
            dict
        ):

            raise ValueError(
                "Retriever returned invalid result."
            )

        print(
            f"Knowledge chunks retrieved: "
            f"{sum(len(r.get('results', [])) for r in retrieval_result.get('records', []))}"
        )

        # =================================================
        # 6. RETRIEVAL EVIDENCE
        # =================================================

        retrieval_records = retrieval_result.get(
            "records",
            []
        )

        if retrieval_records:

            retrieval_record = retrieval_records[0]

            evidence_terms = retrieval_record.get(
                "evidence_terms",
                []
            )

            print(
                "\nEvidence terms:"
            )

            if evidence_terms:

                for term in evidence_terms:

                    print(
                        f"- {term}"
                    )

            else:

                print(
                    "No evidence terms."
                )

        # =================================================
        # 7. XAI
        # =================================================

        print(
            "\n[5] Running XAI analysis..."
        )

        # -------------------------------------------------
        # IMPORTANT:
        # Use the XAI analyzer with the normalized record
        # and retrieved knowledge.
        # -------------------------------------------------

        xai_result = xai_analyzer.analyze(
            adapted_record,
            retrieval_result
        )

        if not isinstance(
            xai_result,
            dict
        ):

            raise ValueError(
                "XAI analyzer returned "
                "an invalid result."
            )

        print(
            "XAI analysis completed."
        )

        # =================================================
        # 8. FINAL RESULT
        # =================================================

        print(
            "\n"
            + "=" * 70
        )

        print(
            f"FINAL {dataset_name.upper()} XAI RESULT"
        )

        print(
            "=" * 70
        )

        print(
            json.dumps(
                xai_result,
                indent=2,
                ensure_ascii=False
            )
        )

        # =================================================
        # 9. ROOT CAUSE
        # =================================================

        display_root_cause(
            xai_result
        )

        # =================================================
        # 10. RESOLUTION
        # =================================================

        display_resolution(
            xai_result
        )

        # =================================================
        # 11. ADMIN SUMMARY
        # =================================================

        display_admin_summary(
            xai_result
        )

        # =================================================
        # 12. EMPLOYEE ACTION
        # =================================================

        display_employee_action(
            xai_result
        )

        # =================================================
        # 13. FINAL RECOMMENDATION
        # =================================================

        display_recommendation(
            xai_result
        )

        # =================================================
        # SUCCESS
        # =================================================

        print(
            "\n"
            + "=" * 70
        )

        print(
            f"{dataset_name.upper()} XAI TEST PASSED"
        )

        print(
            "=" * 70
        )

        return xai_result

    except Exception as error:

        print(
            "\n"
            + "=" * 70
        )

        print(
            f"{dataset_name.upper()} XAI TEST FAILED"
        )

        print(
            "=" * 70
        )

        print(
            f"ERROR: {error}"
        )

        traceback.print_exc()

        return None


# =========================================================
# CLAIMS
# =========================================================

claims_result = process_dataset(
    dataset_name="Claims",
    input_file=CLAIMS_FILE,
    adapter=ClaimsAdapter(),
    target=CLAIMS_TARGET,
    finder=find_claims_record
)


# =========================================================
# PHARMACY
# =========================================================

pharmacy_result = process_dataset(
    dataset_name="Pharmacy",
    input_file=PHARMACY_FILE,
    adapter=PharmacyAdapter(),
    target=PHARMACY_TARGET,
    finder=find_pharmacy_record
)


# =========================================================
# AUTHORIZATION
# =========================================================

authorization_result = process_dataset(
    dataset_name="Authorization",
    input_file=AUTHORIZATION_FILE,
    adapter=AuthorizationAdapter(),
    target=AUTHORIZATION_TARGET,
    finder=find_authorization_record
)


# =========================================================
# FINAL STATUS
# =========================================================

print(
    "\n"
    + "=" * 70
)

if (
    claims_result is not None
    and pharmacy_result is not None
    and authorization_result is not None
):

    print(
        "ALL THREE XAI TESTS PASSED"
    )

else:

    print(
        "ONE OR MORE XAI TESTS FAILED"
    )

print(
    "=" * 70
)