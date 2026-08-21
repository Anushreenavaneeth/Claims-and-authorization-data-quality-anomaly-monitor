import json
from pathlib import Path
from collections import Counter


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

JSON_DIR = BASE_DIR / "json files"

DEFAULT_INPUT_FILES = {
    "authorization": JSON_DIR / "authorization.json",
    "claims": JSON_DIR / "claims.json",
    "pharmacy": JSON_DIR / "pharmacy.json"
}

DEFAULT_OUTPUT_FILE = BASE_DIR / "sla_monitoring_output.json"


# ============================================================
# SEVERITY WEIGHTS
# ============================================================

SEVERITY_WEIGHTS = {
    "NONE": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4
}


# ============================================================
# LOAD JSON FILE
# ============================================================

def load_json(file_path):
    """
    Loads a JSON file and returns its contents.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data


# ============================================================
# VALIDATE INPUT STRUCTURE
# ============================================================

def validate_json_structure(data, file_path):
    """
    Checks whether the input JSON has a records list.
    """

    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid JSON structure in {file_path}. "
            f"Expected a JSON object."
        )

    if "records" not in data:
        raise ValueError(
            f"'records' field missing in {file_path}"
        )

    if not isinstance(data["records"], list):
        raise ValueError(
            f"'records' must be a list in {file_path}"
        )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_anomaly(record):
    """
    Returns whether the record is detected as anomalous.
    """

    final_assessment = record.get("final_assessment", {})

    return bool(
        final_assessment.get("anomaly", False)
    )


def get_severity(record):
    """
    Returns normalized severity.
    """

    final_assessment = record.get("final_assessment", {})

    severity = final_assessment.get(
        "severity",
        "NONE"
    )

    if severity is None:
        return "NONE"

    severity = str(severity).strip().upper()

    if severity not in SEVERITY_WEIGHTS:
        return "NONE"

    return severity


def get_signal_count(record):
    """
    Returns the number of anomaly signals.
    """

    final_assessment = record.get("final_assessment", {})

    value = final_assessment.get(
        "signal_count",
        0
    )

    try:
        return max(0, int(value))

    except (ValueError, TypeError):
        return 0


def get_signal_names(record):
    """
    Converts signals into a clean list.
    """

    final_assessment = record.get("final_assessment", {})

    signals = final_assessment.get(
        "signals",
        "None"
    )

    if signals is None:
        return []

    if isinstance(signals, list):
        return [
            str(signal).strip()
            for signal in signals
            if str(signal).strip()
        ]

    signals = str(signals).strip()

    if not signals or signals.lower() == "none":
        return []

    return [
        signal.strip()
        for signal in signals.split(",")
        if signal.strip()
    ]


def get_record_id(record):
    """
    Dynamically extracts the primary ID from different datasets.
    """

    record_id = record.get("record_id", {})

    if not isinstance(record_id, dict):
        return "UNKNOWN"

    preferred_keys = [
        "authorization_id",
        "claim_id",
        "pharmacy_id",
        "plan_id",
        "member_id",
        "id"
    ]

    for key in preferred_keys:
        value = record_id.get(key)

        if value not in [None, ""]:
            return str(value)

    # Fallback: first non-empty ID
    for value in record_id.values():
        if value not in [None, ""]:
            return str(value)

    return "UNKNOWN"


# ============================================================
# SLA COMPONENT 1 - ANOMALY WORKLOAD
# ============================================================

def calculate_anomaly_workload(records):
    """
    Calculates the percentage of anomalous records.
    """

    total_records = len(records)

    if total_records == 0:
        return 0.0

    anomalous_records = sum(
        1
        for record in records
        if get_anomaly(record)
    )

    score = (
        anomalous_records / total_records
    ) * 100

    return round(score, 2)


# ============================================================
# SLA COMPONENT 2 - SEVERITY BURDEN
# ============================================================

def calculate_severity_burden(records):
    """
    Calculates severity burden.

    NONE      = 0
    LOW       = 1
    MEDIUM    = 2
    HIGH      = 3
    CRITICAL  = 4
    """

    if not records:
        return 0.0

    total_weight = 0

    for record in records:
        severity = get_severity(record)

        total_weight += SEVERITY_WEIGHTS.get(
            severity,
            0
        )

    maximum_possible_weight = len(records) * 4

    if maximum_possible_weight == 0:
        return 0.0

    score = (
        total_weight / maximum_possible_weight
    ) * 100

    return round(score, 2)


# ============================================================
# SLA COMPONENT 3 - SIGNAL BURDEN
# ============================================================

def calculate_signal_burden(records):
    """
    Calculates anomaly signal burden.

    Signal contribution is capped at 3 signals.
    """

    if not records:
        return 0.0

    total_signal_score = 0

    for record in records:
        signal_count = get_signal_count(record)

        total_signal_score += min(
            signal_count,
            3
        )

    maximum_possible_score = len(records) * 3

    if maximum_possible_score == 0:
        return 0.0

    score = (
        total_signal_score / maximum_possible_score
    ) * 100

    return round(score, 2)


# ============================================================
# DATASET SLA RISK SCORE
# ============================================================

def calculate_dataset_sla_risk(
    anomaly_workload,
    severity_burden,
    signal_burden
):
    """
    Final Dataset SLA Risk Score.

    Weighting:
        50% Anomaly Workload
        30% Severity Burden
        20% Signal Burden
    """

    score = (
        0.50 * anomaly_workload
        + 0.30 * severity_burden
        + 0.20 * signal_burden
    )

    score = max(0, min(score, 100))

    return round(score, 2)


# ============================================================
# RISK LEVEL
# ============================================================

def get_risk_level(score):
    """
    Converts SLA score into a risk category.
    """

    if score <= 30:
        return "LOW"

    elif score <= 60:
        return "MEDIUM"

    elif score <= 80:
        return "HIGH"

    else:
        return "CRITICAL"


# ============================================================
# RECORD LEVEL SLA RISK
# ============================================================

def calculate_record_sla_risk(record):
    """
    Calculates SLA exposure for an individual record.

    Weighting:
        50% Anomaly existence
        30% Severity
        20% Signal count
    """

    anomaly = get_anomaly(record)

    severity = get_severity(record)

    signal_count = get_signal_count(record)

    # No anomaly means no current SLA exposure
    if not anomaly:
        return {
            "risk_score": 0.0,
            "risk_level": "LOW"
        }

    # --------------------------------------------------------
    # 1. ANOMALY CONTRIBUTION
    # --------------------------------------------------------

    anomaly_score = 100

    # --------------------------------------------------------
    # 2. SEVERITY CONTRIBUTION
    # --------------------------------------------------------

    severity_weight = SEVERITY_WEIGHTS.get(
        severity,
        0
    )

    severity_score = (
        severity_weight / 4
    ) * 100

    # --------------------------------------------------------
    # 3. SIGNAL CONTRIBUTION
    # --------------------------------------------------------

    signal_score = (
        min(signal_count, 3) / 3
    ) * 100

    # --------------------------------------------------------
    # FINAL RECORD SCORE
    # --------------------------------------------------------

    score = (
        0.50 * anomaly_score
        + 0.30 * severity_score
        + 0.20 * signal_score
    )

    score = max(0, min(score, 100))

    score = round(score, 2)

    return {
        "risk_score": score,
        "risk_level": get_risk_level(score)
    }


# ============================================================
# SLA RECOMMENDATION ENGINE
# ============================================================

def get_sla_recommendation(risk_level):
    """
    Gives an OPERATIONAL recommendation.

    It does NOT explain how to fix the anomaly.
    Detailed anomaly explanation/fix can be handled by RAG.
    """

    recommendations = {

        "LOW": {
            "action": "Continue Normal Monitoring",

            "recommendation": (
                "Continue standard processing and routine monitoring. "
                "No immediate SLA intervention is currently required."
            )
        },

        "MEDIUM": {
            "action": "Prioritized Review",

            "recommendation": (
                "Review the affected workload within the defined "
                "processing window and prioritize unresolved anomalies "
                "before they accumulate into a processing backlog."
            )
        },

        "HIGH": {
            "action": "Immediate Prioritization",

            "recommendation": (
                "Prioritize the affected records for resolution and "
                "assign them to the appropriate operations queue to "
                "reduce the risk of processing delays and potential "
                "SLA breach."
            )
        },

        "CRITICAL": {
            "action": "Escalation Required",

            "recommendation": (
                "Immediately escalate the affected workload, prioritize "
                "critical anomalies, and allocate additional operational "
                "resources to prevent an SLA breach."
            )
        }
    }

    return recommendations.get(
        risk_level,
        recommendations["LOW"]
    )


# ============================================================
# CREATE RECORD LEVEL OUTPUT
# ============================================================

def create_record_sla_output(record):
    """
    Creates SLA output for one record.
    """

    record_id = get_record_id(record)

    anomaly = get_anomaly(record)

    severity = get_severity(record)

    signal_count = get_signal_count(record)

    signals = get_signal_names(record)

    # Calculate record SLA risk
    sla_result = calculate_record_sla_risk(record)

    risk_score = sla_result["risk_score"]
    risk_level = sla_result["risk_level"]

    # SLA recommendation
    sla_recommendation = get_sla_recommendation(
        risk_level
    )

    return {

        "record_id": record_id,

        "anomaly_detected": anomaly,

        "anomaly_severity": severity,

        "signal_count": signal_count,

        "signals": signals,

        "sla_risk": {

            "risk_score": risk_score,

            "risk_level": risk_level
        },

        "sla_recommendation": {

            "action": sla_recommendation["action"],

            "recommendation": (
                sla_recommendation["recommendation"]
            )
        }
    }


# ============================================================
# PROCESS ONE DATASET
# ============================================================

def process_dataset(dataset_name, file_path):
    """
    Processes one input JSON dataset.
    """

    # Load JSON
    data = load_json(file_path)

    # Validate structure
    validate_json_structure(
        data,
        file_path
    )

    records = data["records"]

    total_records = len(records)

    # --------------------------------------------------------
    # ANOMALY SUMMARY
    # --------------------------------------------------------

    anomalous_records = sum(
        1
        for record in records
        if get_anomaly(record)
    )

    normal_records = (
        total_records - anomalous_records
    )

    if total_records > 0:

        anomaly_rate = (
            anomalous_records / total_records
        ) * 100

    else:
        anomaly_rate = 0.0

    anomaly_rate = round(
        anomaly_rate,
        2
    )

    # --------------------------------------------------------
    # SEVERITY DISTRIBUTION
    # --------------------------------------------------------

    severity_distribution = Counter(
        get_severity(record)
        for record in records
    )

    # --------------------------------------------------------
    # SIGNAL DISTRIBUTION
    # --------------------------------------------------------

    signal_distribution = Counter(
        get_signal_count(record)
        for record in records
    )

    # --------------------------------------------------------
    # SLA COMPONENTS
    # --------------------------------------------------------

    anomaly_workload = calculate_anomaly_workload(
        records
    )

    severity_burden = calculate_severity_burden(
        records
    )

    signal_burden = calculate_signal_burden(
        records
    )

    # --------------------------------------------------------
    # DATASET SLA RISK
    # --------------------------------------------------------

    sla_score = calculate_dataset_sla_risk(
        anomaly_workload,
        severity_burden,
        signal_burden
    )

    risk_level = get_risk_level(
        sla_score
    )

    # --------------------------------------------------------
    # SLA RECOMMENDATION
    # --------------------------------------------------------

    sla_recommendation = get_sla_recommendation(
        risk_level
    )

    # --------------------------------------------------------
    # RECORD RESULTS
    # --------------------------------------------------------

    record_results = []

    for record in records:

        result = create_record_sla_output(
            record
        )

        record_results.append(result)

    # --------------------------------------------------------
    # FINAL DATASET RESULT
    # --------------------------------------------------------

    return {

        "dataset": dataset_name,

        "source_file": str(file_path),

        "record_count": total_records,

        "anomaly_summary": {

            "anomalous_records": anomalous_records,

            "normal_records": normal_records,

            "anomaly_rate": anomaly_rate
        },

        "severity_distribution": dict(
            severity_distribution
        ),

        "signal_distribution": {

            str(key): value

            for key, value
            in sorted(signal_distribution.items())
        },

        "sla_metrics": {

            "anomaly_workload_score": anomaly_workload,

            "severity_burden_score": severity_burden,

            "signal_burden_score": signal_burden
        },

        "sla_risk": {

            "risk_score": sla_score,

            "risk_level": risk_level
        },

        "sla_recommendation": {

            "action": sla_recommendation["action"],

            "recommendation": (
                sla_recommendation["recommendation"]
            )
        },

        "record_results": record_results
    }


# ============================================================
# MAIN SLA MONITORING FUNCTION
# ============================================================

def run_sla_monitoring(
    authorization_path=None,
    claims_path=None,
    pharmacy_path=None,
    output_path=None
):
    """
    Main reusable SLA Monitoring function.

    CURRENT USAGE:
        Uses local JSON files automatically.

    FUTURE INTEGRATION:
        Backend can pass paths directly:

        run_sla_monitoring(
            authorization_path="path/to/file.json",
            claims_path="path/to/file.json",
            pharmacy_path="path/to/file.json"
        )

    The number of records can change dynamically.
    """

    # --------------------------------------------------------
    # DEFAULT INPUT PATHS
    # --------------------------------------------------------

    if authorization_path is None:
        authorization_path = DEFAULT_INPUT_FILES[
            "authorization"
        ]

    if claims_path is None:
        claims_path = DEFAULT_INPUT_FILES[
            "claims"
        ]

    if pharmacy_path is None:
        pharmacy_path = DEFAULT_INPUT_FILES[
            "pharmacy"
        ]

    if output_path is None:
        output_path = DEFAULT_OUTPUT_FILE

    # --------------------------------------------------------
    # INPUT DATASETS
    # --------------------------------------------------------

    input_files = {

        "authorization": authorization_path,

        "claims": claims_path,

        "pharmacy": pharmacy_path
    }

    results = []

    # ========================================================
    # PROCESS EACH DATASET
    # ========================================================

    for dataset_name, file_path in input_files.items():

        if file_path is None:
            continue

        try:

            print(
                f"\nProcessing "
                f"{dataset_name.upper()}..."
            )

            result = process_dataset(
                dataset_name,
                file_path
            )

            results.append(result)

            print(
                f"Records        : "
                f"{result['record_count']}"
            )

            print(
                f"Anomalies      : "
                f"{result['anomaly_summary']['anomalous_records']}"
            )

            print(
                f"Anomaly Rate   : "
                f"{result['anomaly_summary']['anomaly_rate']}%"
            )

            print(
                f"SLA Score      : "
                f"{result['sla_risk']['risk_score']}"
            )

            print(
                f"SLA Risk Level : "
                f"{result['sla_risk']['risk_level']}"
            )

            print(
                f"Action         : "
                f"{result['sla_recommendation']['action']}"
            )

        except Exception as error:

            print(
                f"\nERROR processing "
                f"{dataset_name.upper()}: {error}"
            )

    # ========================================================
    # OVERALL SUMMARY
    # ========================================================

    total_records = sum(
        result["record_count"]
        for result in results
    )

    total_anomalies = sum(
        result["anomaly_summary"][
            "anomalous_records"
        ]
        for result in results
    )

    # --------------------------------------------------------
    # OVERALL ANOMALY RATE
    # --------------------------------------------------------

    if total_records > 0:

        overall_anomaly_rate = (
            total_anomalies / total_records
        ) * 100

    else:
        overall_anomaly_rate = 0.0

    overall_anomaly_rate = round(
        overall_anomaly_rate,
        2
    )

    # --------------------------------------------------------
    # WEIGHTED OVERALL SLA SCORE
    # --------------------------------------------------------

    if total_records > 0:

        weighted_sla_total = sum(

            result["sla_risk"]["risk_score"]
            *
            result["record_count"]

            for result in results

        )

        overall_sla_score = (
            weighted_sla_total / total_records
        )

    else:
        overall_sla_score = 0.0

    overall_sla_score = round(
        max(
            0,
            min(overall_sla_score, 100)
        ),
        2
    )

    overall_risk_level = get_risk_level(
        overall_sla_score
    )

    overall_recommendation = (
        get_sla_recommendation(
            overall_risk_level
        )
    )

    # ========================================================
    # DATASET RISK SUMMARY
    # ========================================================

    dataset_risk_summary = []

    for result in results:

        dataset_risk_summary.append({

            "dataset":
                result["dataset"],

            "record_count":
                result["record_count"],

            "anomaly_rate":
                result["anomaly_summary"][
                    "anomaly_rate"
                ],

            "sla_risk_score":
                result["sla_risk"][
                    "risk_score"
                ],

            "sla_risk_level":
                result["sla_risk"][
                    "risk_level"
                ],

            "recommended_action":
                result["sla_recommendation"][
                    "action"
                ]
        })

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    output = {

        "project":
            "Healthcare Data Operations Platform - SLA Risk Monitor",

        "schema_version":
            "1.0",

        "monitoring_type":
            "Operational SLA Risk Exposure Monitoring",

        "datasets_processed":
            len(results),

        "overall_summary": {

            "total_records":
                total_records,

            "total_anomalous_records":
                total_anomalies,

            "overall_anomaly_rate":
                overall_anomaly_rate
        },

        "overall_sla_risk": {

            "risk_score":
                overall_sla_score,

            "risk_level":
                overall_risk_level
        },

        "overall_sla_recommendation": {

            "action":
                overall_recommendation["action"],

            "recommendation":
                overall_recommendation["recommendation"]
        },

        "dataset_risk_summary":
            dataset_risk_summary,

        "dataset_results":
            results
    }

    # ========================================================
    # SAVE OUTPUT
    # ========================================================

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=4,
            ensure_ascii=False
        )

    # ========================================================
    # CONSOLE OUTPUT
    # ========================================================

    print(
        "\n"
        + "=" * 60
    )

    print(
        "SLA MONITORING COMPLETED"
    )

    print(
        "=" * 60
    )

    print(
        f"Datasets Processed : {len(results)}"
    )

    print(
        f"Total Records      : {total_records}"
    )

    print(
        f"Total Anomalies    : {total_anomalies}"
    )

    print(
        f"Overall Anomaly %  : {overall_anomaly_rate}%"
    )

    print(
        f"Overall SLA Score  : {overall_sla_score}"
    )

    print(
        f"Overall SLA Risk   : {overall_risk_level}"
    )

    print(
        f"Recommended Action : "
        f"{overall_recommendation['action']}"
    )

    print(
        "\nRecommendation:"
    )

    print(
        overall_recommendation["recommendation"]
    )

    print(
        f"\nOutput saved to:\n{output_path}"
    )

    return output


# ============================================================
# RUN LOCALLY
# ============================================================

if __name__ == "__main__":

    run_sla_monitoring()