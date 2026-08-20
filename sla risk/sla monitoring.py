import json
import os
import statistics
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

# Get the folder where this Python file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Input JSON paths
CLAIMS_JSON_PATH = os.path.join(
    BASE_DIR,
    "json files",
    "claims.json"
)

AUTHORIZATION_JSON_PATH = os.path.join(
    BASE_DIR,
    "json files",
    "authorization.json"
)


# Output JSON path
OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "sla_monitoring_output.json"
)


# ============================================================
# SLA CONFIGURATION
# ============================================================

SLA_CONFIG = {

    "claims": {
        "sla_hours": 24,

        # Used only when actual total pipeline records are available
        "anomaly_rate_warning": 0.10,
        "anomaly_rate_high": 0.20
    },

    "authorization": {
        "sla_hours": 48,

        # Used only when actual total pipeline records are available
        "anomaly_rate_warning": 0.10,
        "anomaly_rate_high": 0.20
    },

    "pharmacy": {
        "sla_hours": 24,
        "anomaly_rate_warning": 0.10,
        "anomaly_rate_high": 0.20
    }
}


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path):

    if not os.path.exists(path):

        print(f"\nWARNING: File not found -> {path}")
        return None

    try:

        with open(path, "r", encoding="utf-8") as file:

            data = json.load(file)

        print(f"\nSuccessfully loaded -> {path}")

        return data

    except Exception as error:

        print(f"\nERROR loading JSON -> {path}")
        print(error)

        return None


# ============================================================
# SAFE FLOAT CONVERSION
# ============================================================

def to_float(value):

    if value is None:
        return None

    try:
        return float(value)

    except (ValueError, TypeError):
        return None


# ============================================================
# SAFE INTEGER CONVERSION
# ============================================================

def to_int(value):

    if value is None:
        return None

    try:
        return int(float(value))

    except (ValueError, TypeError):
        return None


# ============================================================
# SAFE BOOLEAN CHECK
# ============================================================

def is_true(value):

    if value is True:
        return True

    if isinstance(value, str):

        return value.strip().lower() in [
            "true",
            "yes",
            "1"
        ]

    if isinstance(value, (int, float)):
        return value == 1

    return False


# ============================================================
# CHECK IF DICTIONARY LOOKS LIKE A RECORD
# ============================================================

def looks_like_record(item):

    if not isinstance(item, dict):
        return False

    possible_record_keys = {

        # Claims
        "record",
        "anomaly",
        "detection",
        "claim_id",

        # Authorization
        "dataset_type",
        "record_id",
        "detection_summary",
        "rule_based_evidence",
        "ml_based_evidence",
        "record_context"
    }

    return len(
        possible_record_keys.intersection(item.keys())
    ) > 0


# ============================================================
# FIND RECORD LIST
#
# Supports:
#
# {
#     "anomalies": [...]
# }
#
# {
#     "records": [...]
# }
#
# {
#     "data": [...]
# }
#
# [...]
# ============================================================

def find_record_list(data):

    # --------------------------------------------------------
    # CASE 1: ROOT IS A LIST
    # --------------------------------------------------------

    if isinstance(data, list):

        if len(data) == 0:
            return []

        if (
            isinstance(data[0], dict)
            and looks_like_record(data[0])
        ):
            return data

        for item in data:

            result = find_record_list(item)

            if result:
                return result

        return []


    # --------------------------------------------------------
    # CASE 2: ROOT IS A DICTIONARY
    # --------------------------------------------------------

    if isinstance(data, dict):

        possible_list_keys = [

            "anomalies",
            "results",
            "records",
            "data",
            "output",
            "items",
            "anomaly_results",
            "claims_results",
            "authorization_results",
            "claims_output",
            "authorization_output"
        ]


        # Check common keys first
        for key in possible_list_keys:

            if key in data:

                value = data[key]

                if (
                    isinstance(value, list)
                    and len(value) > 0
                    and isinstance(value[0], dict)
                    and looks_like_record(value[0])
                ):

                    print(
                        f"Records found under key: {key}"
                    )

                    return value


        # Search all dictionary values
        for key, value in data.items():

            if (
                isinstance(value, list)
                and len(value) > 0
                and isinstance(value[0], dict)
                and looks_like_record(value[0])
            ):

                print(
                    f"Records found under key: {key}"
                )

                return value


        # Dictionary itself may be one record
        if looks_like_record(data):

            return [data]


        # Recursive search
        for value in data.values():

            if isinstance(value, (dict, list)):

                result = find_record_list(value)

                if result:
                    return result


    return []


# ============================================================
# FIND TOTAL ORIGINAL PIPELINE RECORD COUNT
#
# This is important because the JSON may contain ONLY anomalies.
#
# Example:
#
# total_input_records = 10000
# anomaly_records = 408
#
# actual anomaly rate = 408 / 10000 = 4.08%
#
# If total original count is not available:
#
# pipeline_anomaly_rate = None
# ============================================================

def find_total_pipeline_records(data):

    possible_total_keys = [

        "total_input_records",
        "total_records",
        "total_record_count",
        "input_record_count",
        "original_record_count",
        "source_record_count",
        "pipeline_record_count",
        "records_processed",
        "total_processed_records"
    ]


    def recursive_search(obj):

        if isinstance(obj, dict):

            # Search direct keys
            for key in possible_total_keys:

                if key in obj:

                    value = to_int(obj[key])

                    if value is not None and value > 0:

                        return value


            # Search metadata-like sections first
            metadata_keys = [

                "metadata",
                "metrics",
                "summary",
                "pipeline_metrics",
                "processing_summary",
                "dataset_summary",
                "run_summary"
            ]

            for key in metadata_keys:

                if key in obj:

                    result = recursive_search(obj[key])

                    if result is not None:
                        return result


            # Search remaining nested values
            for value in obj.values():

                if isinstance(value, (dict, list)):

                    result = recursive_search(value)

                    if result is not None:
                        return result


        elif isinstance(obj, list):

            for item in obj:

                if isinstance(item, (dict, list)):

                    result = recursive_search(item)

                    if result is not None:
                        return result


        return None


    return recursive_search(data)


# ============================================================
# DETECT SOURCE TYPE
# ============================================================

def detect_source(records):

    if not records:
        return "unknown"

    first = records[0]

    if not isinstance(first, dict):
        return "unknown"


    keys = set(first.keys())


    # --------------------------------------------------------
    # AUTHORIZATION
    # --------------------------------------------------------

    dataset_type = str(
        first.get("dataset_type", "")
    ).lower()

    if "author" in dataset_type:
        return "authorization"


    authorization_keys = {

        "detection_summary",
        "rule_based_evidence",
        "ml_based_evidence",
        "record_context",
        "sla"
    }

    if len(
        keys.intersection(authorization_keys)
    ) > 0:

        return "authorization"


    # --------------------------------------------------------
    # CLAIMS
    # --------------------------------------------------------

    claims_keys = {

        "record",
        "anomaly",
        "detection"
    }

    if len(
        keys.intersection(claims_keys)
    ) >= 2:

        return "claims"


    if "claim_id" in keys:
        return "claims"


    return "unknown"


# ============================================================
# PROCESS CLAIMS RECORDS
# ============================================================

def process_claims(records):

    anomaly_records_received = len(records)

    rule_anomalies = 0
    ml_anomalies = 0

    ml_scores = []


    for item in records:

        # ----------------------------------------------------
        # DETECTION
        # ----------------------------------------------------

        detection = item.get(
            "detection",
            {}
        )

        if not isinstance(detection, dict):
            detection = {}


        # ----------------------------------------------------
        # RULE BASED
        # ----------------------------------------------------

        rule_data = detection.get(
            "rule_based",
            {}
        )

        if isinstance(rule_data, dict):

            if is_true(
                rule_data.get(
                    "detected",
                    rule_data.get(
                        "anomaly_detected",
                        False
                    )
                )
            ):

                rule_anomalies += 1


        # ----------------------------------------------------
        # MACHINE LEARNING
        # ----------------------------------------------------

        ml_data = detection.get(
            "machine_learning",
            {}
        )

        if isinstance(ml_data, dict):

            if is_true(
                ml_data.get(
                    "detected",
                    ml_data.get(
                        "anomaly_detected",
                        False
                    )
                )
            ):

                ml_anomalies += 1


            score = to_float(

                ml_data.get(
                    "anomaly_score",
                    ml_data.get(
                        "score",
                        ml_data.get(
                            "risk_score"
                        )
                    )
                )
            )


            if score is not None:

                # Isolation Forest scores can be negative
                ml_scores.append(abs(score))


    # --------------------------------------------------------
    # AVERAGE ML SCORE
    # --------------------------------------------------------

    average_risk_score = (

        sum(ml_scores) / len(ml_scores)

        if ml_scores

        else 0
    )


    return {

        "anomaly_records_received":
            anomaly_records_received,

        "rule_anomalies":
            rule_anomalies,

        "ml_anomalies":
            ml_anomalies,

        "average_risk_score":
            average_risk_score,

        # Claims JSON currently has no processing times
        "processing_times": []
    }


# ============================================================
# PROCESS AUTHORIZATION RECORDS
# ============================================================

def process_authorization(records):

    anomaly_records_received = len(records)

    rule_anomalies = 0
    ml_anomalies = 0

    risk_scores = []
    processing_times = []


    for item in records:

        # ----------------------------------------------------
        # DETECTION SUMMARY
        # ----------------------------------------------------

        detection = item.get(
            "detection_summary",
            {}
        )

        if not isinstance(detection, dict):
            detection = {}


        # ----------------------------------------------------
        # RULE ANOMALY
        # ----------------------------------------------------

        if is_true(

            detection.get(
                "rule_anomaly",
                item.get(
                    "rule_anomaly",
                    False
                )
            )
        ):

            rule_anomalies += 1


        # ----------------------------------------------------
        # ML ANOMALY
        # ----------------------------------------------------

        if is_true(

            detection.get(
                "ml_anomaly",
                item.get(
                    "ml_anomaly",
                    False
                )
            )
        ):

            ml_anomalies += 1


        # ----------------------------------------------------
        # RISK SCORE
        # ----------------------------------------------------

        risk_score = to_float(

            detection.get(
                "final_risk_score"
            )
        )


        if risk_score is None:

            risk_score = to_float(

                item.get(
                    "final_risk_score"
                )
            )


        if risk_score is not None:

            risk_scores.append(risk_score)


        # ----------------------------------------------------
        # PROCESSING TIME
        # ----------------------------------------------------

        context = item.get(
            "record_context",
            {}
        )

        if not isinstance(context, dict):
            context = {}


        processing_time = to_float(

            context.get(
                "processing_time_hours"
            )
        )


        if processing_time is None:

            processing_time = to_float(

                item.get(
                    "processing_time_hours"
                )
            )


        if processing_time is not None:

            processing_times.append(
                processing_time
            )


    # --------------------------------------------------------
    # AVERAGE RISK SCORE
    # --------------------------------------------------------

    average_risk_score = (

        sum(risk_scores) / len(risk_scores)

        if risk_scores

        else 0
    )


    return {

        "anomaly_records_received":
            anomaly_records_received,

        "rule_anomalies":
            rule_anomalies,

        "ml_anomalies":
            ml_anomalies,

        "average_risk_score":
            average_risk_score,

        "processing_times":
            processing_times
    }


# ============================================================
# CALCULATE ACTUAL PIPELINE ANOMALY RATE
#
# Only calculated when total original pipeline count is known.
# ============================================================

def calculate_anomaly_rate(
    anomaly_records_received,
    total_pipeline_records
):

    if (
        total_pipeline_records is None
        or total_pipeline_records <= 0
    ):

        return {

            "available": False,

            "rate": None
        }


    rate = (
        anomaly_records_received
        / total_pipeline_records
    )


    return {

        "available": True,

        "rate": rate
    }


# ============================================================
# PROCESSING TIME ANALYSIS
# ============================================================

def analyze_processing_times(
    processing_times,
    sla_hours
):

    # --------------------------------------------------------
    # NO PROCESSING TIME DATA
    # --------------------------------------------------------

    if not processing_times:

        return {

            "available": False,

            "average_hours": None,

            "median_hours": None,

            "max_hours": None,

            "sla_hours": sla_hours,

            "records_over_sla": 0,

            "over_sla_rate": None,

            "processing_anomaly": False
        }


    # --------------------------------------------------------
    # BASIC METRICS
    # --------------------------------------------------------

    average_hours = (

        sum(processing_times)
        / len(processing_times)
    )


    median_hours = statistics.median(
        processing_times
    )


    max_hours = max(
        processing_times
    )


    records_over_sla = sum(

        1

        for value in processing_times

        if value > sla_hours
    )


    over_sla_rate = (

        records_over_sla
        / len(processing_times)
    )


    # --------------------------------------------------------
    # UNUSUAL PROCESSING TIME DETECTION
    # --------------------------------------------------------

    processing_anomaly = False


    if len(processing_times) >= 5:

        try:

            standard_deviation = statistics.stdev(
                processing_times
            )


            threshold = (

                median_hours
                + (2 * standard_deviation)
            )


            if max_hours > threshold:

                processing_anomaly = True


        except statistics.StatisticsError:

            processing_anomaly = False


    # Any record exceeding SLA indicates SLA processing risk
    if records_over_sla > 0:

        processing_anomaly = True


    return {

        "available": True,

        "average_hours":
            round(average_hours, 2),

        "median_hours":
            round(median_hours, 2),

        "max_hours":
            round(max_hours, 2),

        "sla_hours":
            sla_hours,

        "records_over_sla":
            records_over_sla,

        "over_sla_rate":
            round(over_sla_rate, 4),

        "processing_anomaly":
            processing_anomaly
    }


# ============================================================
# CALCULATE DATA QUALITY RISK
#
# Uses:
# - Actual anomaly rate when available
# - Otherwise anomaly workload and ML/rule findings
# - Average anomaly risk score
# ============================================================

def calculate_data_quality_risk(
    source,
    anomaly_records_received,
    rule_anomalies,
    ml_anomalies,
    anomaly_rate_result,
    average_risk_score
):

    config = SLA_CONFIG[source]

    risk_points = 0
    reasons = []


    # --------------------------------------------------------
    # ACTUAL ANOMALY RATE
    # --------------------------------------------------------

    if anomaly_rate_result["available"]:

        anomaly_rate = anomaly_rate_result["rate"]


        if anomaly_rate >= config["anomaly_rate_high"]:

            risk_points += 3

            reasons.append(
                f"High pipeline anomaly rate: "
                f"{anomaly_rate:.2%}"
            )


        elif anomaly_rate >= config["anomaly_rate_warning"]:

            risk_points += 2

            reasons.append(
                f"Elevated pipeline anomaly rate: "
                f"{anomaly_rate:.2%}"
            )


    # --------------------------------------------------------
    # ANOMALY RATE NOT AVAILABLE
    # --------------------------------------------------------

    else:

        reasons.append(
            "Actual pipeline anomaly rate is unavailable because "
            "the input JSON contains anomaly output records and "
            "does not provide the total original pipeline record count."
        )


        # Large anomaly workload
        if anomaly_records_received >= 1000:

            risk_points += 3

            reasons.append(
                f"High anomaly workload: "
                f"{anomaly_records_received} anomaly records received"
            )


        elif anomaly_records_received >= 500:

            risk_points += 2

            reasons.append(
                f"Elevated anomaly workload: "
                f"{anomaly_records_received} anomaly records received"
            )


        elif anomaly_records_received >= 100:

            risk_points += 1

            reasons.append(
                f"Anomaly workload requires review: "
                f"{anomaly_records_received} anomaly records received"
            )


    # --------------------------------------------------------
    # ML ANOMALY PRESSURE
    # --------------------------------------------------------

    if ml_anomalies >= 500:

        risk_points += 2

        reasons.append(
            f"High ML anomaly volume: "
            f"{ml_anomalies} records"
        )


    elif ml_anomalies >= 100:

        risk_points += 1

        reasons.append(
            f"Significant ML anomaly volume: "
            f"{ml_anomalies} records"
        )


    # --------------------------------------------------------
    # RULE ANOMALY PRESSURE
    # --------------------------------------------------------

    if rule_anomalies >= 500:

        risk_points += 2

        reasons.append(
            f"High rule-based anomaly volume: "
            f"{rule_anomalies} records"
        )


    elif rule_anomalies >= 100:

        risk_points += 1

        reasons.append(
            f"Significant rule-based anomaly volume: "
            f"{rule_anomalies} records"
        )


    # --------------------------------------------------------
    # AVERAGE RISK SCORE
    # --------------------------------------------------------

    if average_risk_score >= 0.70:

        risk_points += 2

        reasons.append(
            "High average anomaly/risk score"
        )


    elif average_risk_score >= 0.40:

        risk_points += 1

        reasons.append(
            "Moderate average anomaly/risk score"
        )


    # --------------------------------------------------------
    # FINAL DATA QUALITY RISK
    # --------------------------------------------------------

    if risk_points >= 6:

        data_quality_risk = "HIGH"


    elif risk_points >= 3:

        data_quality_risk = "MEDIUM"


    else:

        data_quality_risk = "LOW"


    return {

        "data_quality_risk":
            data_quality_risk,

        "risk_points":
            risk_points,

        "risk_reasons":
            reasons
    }


# ============================================================
# CALCULATE SLA RISK
#
# Uses ONLY processing / SLA indicators.
#
# This prevents data anomaly count from being incorrectly
# treated as an actual SLA breach.
# ============================================================

def calculate_sla_risk(
    processing_analysis
):

    risk_points = 0
    reasons = []


    # --------------------------------------------------------
    # PROCESSING DATA NOT AVAILABLE
    # --------------------------------------------------------

    if not processing_analysis["available"]:

        return {

            "sla_risk": "NOT_AVAILABLE",

            "risk_points": 0,

            "risk_reasons": [

                "Processing-time data is not available, so actual "
                "SLA risk cannot be calculated for this source."
            ]
        }


    # --------------------------------------------------------
    # RECORDS EXCEEDING SLA
    # --------------------------------------------------------

    records_over_sla = (
        processing_analysis["records_over_sla"]
    )


    over_sla_rate = (
        processing_analysis["over_sla_rate"]
    )


    if records_over_sla > 0:

        if over_sla_rate >= 0.50:

            risk_points += 4

            reasons.append(
                f"Severe SLA exposure: "
                f"{over_sla_rate:.2%} of records exceeded "
                f"the {processing_analysis['sla_hours']} hour SLA"
            )


        elif over_sla_rate >= 0.20:

            risk_points += 3

            reasons.append(
                f"High SLA exposure: "
                f"{over_sla_rate:.2%} of records exceeded "
                f"the {processing_analysis['sla_hours']} hour SLA"
            )


        else:

            risk_points += 2

            reasons.append(
                f"{records_over_sla} record(s) exceeded "
                f"the {processing_analysis['sla_hours']} hour SLA"
            )


    # --------------------------------------------------------
    # UNUSUAL PROCESSING PATTERN
    # --------------------------------------------------------

    if processing_analysis["processing_anomaly"]:

        risk_points += 2

        reasons.append(
            "Unusual processing-time pattern detected"
        )


    # --------------------------------------------------------
    # FINAL SLA RISK
    # --------------------------------------------------------

    if risk_points >= 5:

        sla_risk = "HIGH"


    elif risk_points >= 2:

        sla_risk = "MEDIUM"


    else:

        sla_risk = "LOW"


    return {

        "sla_risk":
            sla_risk,

        "risk_points":
            risk_points,

        "risk_reasons":
            reasons
    }


# ============================================================
# CALCULATE OVERALL PIPELINE RISK
# ============================================================

def calculate_overall_risk(
    data_quality_result,
    sla_result
):

    points = (
        data_quality_result["risk_points"]
        + sla_result["risk_points"]
    )


    if points >= 9:

        overall_risk = "HIGH"


    elif points >= 4:

        overall_risk = "MEDIUM"


    else:

        overall_risk = "LOW"


    return {

        "overall_pipeline_risk":
            overall_risk,

        "combined_risk_points":
            points
    }


# ============================================================
# GENERATE RECOMMENDATIONS
# ============================================================

def generate_recommendations(
    source,
    anomaly_rate_result,
    anomaly_records_received,
    rule_anomalies,
    ml_anomalies,
    processing_analysis,
    data_quality_result,
    sla_result,
    overall_result
):

    recommendations = []


    # --------------------------------------------------------
    # ANOMALY RATE UNAVAILABLE
    # --------------------------------------------------------

    if not anomaly_rate_result["available"]:

        recommendations.append(
            "Provide the total original pipeline record count in "
            "future pipeline outputs so the actual anomaly rate can "
            "be calculated accurately."
        )


    # --------------------------------------------------------
    # DATA QUALITY RISK
    # --------------------------------------------------------

    if data_quality_result["data_quality_risk"] == "HIGH":

        recommendations.append(
            "Prioritize investigation of the high anomaly workload "
            "and identify common root causes in upstream data."
        )


    elif data_quality_result["data_quality_risk"] == "MEDIUM":

        recommendations.append(
            "Review the detected anomaly patterns and validate "
            "recent changes in source data or pipeline processing."
        )


    # --------------------------------------------------------
    # ML / RULE FINDINGS
    # --------------------------------------------------------

    if ml_anomalies > 0:

        recommendations.append(
            "Review ML-detected anomaly patterns to identify "
            "previously unknown or unusual data behavior."
        )


    if rule_anomalies > 0:

        recommendations.append(
            "Review rule-based violations and correct recurring "
            "data-quality issues at the upstream source."
        )


    # --------------------------------------------------------
    # SLA RISK
    # --------------------------------------------------------

    if sla_result["sla_risk"] == "HIGH":

        recommendations.append(
            "Escalate the pipeline for immediate investigation "
            "because a high proportion of records are at risk of "
            "or have exceeded the configured SLA."
        )


    elif sla_result["sla_risk"] == "MEDIUM":

        recommendations.append(
            "Monitor processing delays closely and address "
            "bottlenecks before additional SLA breaches occur."
        )


    elif sla_result["sla_risk"] == "NOT_AVAILABLE":

        recommendations.append(
            "Capture record or pipeline processing timestamps in "
            "future outputs to enable SLA breach and delay analysis."
        )


    # --------------------------------------------------------
    # OVERALL HIGH RISK
    # --------------------------------------------------------

    if overall_result["overall_pipeline_risk"] == "HIGH":

        recommendations.append(
            "Assign the issue for immediate administrative review "
            "and track remediation until the affected data quality "
            "and processing risks are resolved."
        )


    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    if not recommendations:

        recommendations.append(
            "Continue routine monitoring. No significant pipeline "
            "risk indicators were detected."
        )


    # Remove duplicates
    unique_recommendations = []


    for recommendation in recommendations:

        if recommendation not in unique_recommendations:

            unique_recommendations.append(
                recommendation
            )


    return unique_recommendations


# ============================================================
# ANALYZE ONE SOURCE
# ============================================================

def analyze_source(
    source,
    records,
    original_json_data
):

    print("\n" + "=" * 60)
    print(f"ANALYZING: {source.upper()}")
    print("=" * 60)

    print(
        f"Anomaly records received: {len(records)}"
    )


    # --------------------------------------------------------
    # PROCESS RECORDS
    # --------------------------------------------------------

    if source == "claims":

        summary = process_claims(
            records
        )


    elif source == "authorization":

        summary = process_authorization(
            records
        )


    else:

        print(
            "Unsupported source."
        )

        return None


    # --------------------------------------------------------
    # FIND TOTAL ORIGINAL PIPELINE RECORD COUNT
    # --------------------------------------------------------

    total_pipeline_records = find_total_pipeline_records(
        original_json_data
    )


    if total_pipeline_records is not None:

        print(
            f"Total original pipeline records found: "
            f"{total_pipeline_records}"
        )


    else:

        print(
            "Total original pipeline record count: "
            "NOT AVAILABLE"
        )


    # --------------------------------------------------------
    # ACTUAL ANOMALY RATE
    # --------------------------------------------------------

    anomaly_rate_result = calculate_anomaly_rate(

        summary["anomaly_records_received"],

        total_pipeline_records
    )


    # --------------------------------------------------------
    # CONFIG
    # --------------------------------------------------------

    config = SLA_CONFIG[source]


    # --------------------------------------------------------
    # PROCESSING TIME ANALYSIS
    # --------------------------------------------------------

    processing_analysis = analyze_processing_times(

        summary["processing_times"],

        config["sla_hours"]
    )


    # --------------------------------------------------------
    # DATA QUALITY RISK
    # --------------------------------------------------------

    data_quality_result = calculate_data_quality_risk(

        source=source,

        anomaly_records_received=
            summary["anomaly_records_received"],

        rule_anomalies=
            summary["rule_anomalies"],

        ml_anomalies=
            summary["ml_anomalies"],

        anomaly_rate_result=
            anomaly_rate_result,

        average_risk_score=
            summary["average_risk_score"]
    )


    # --------------------------------------------------------
    # SLA RISK
    # --------------------------------------------------------

    sla_result = calculate_sla_risk(

        processing_analysis
    )


    # --------------------------------------------------------
    # OVERALL RISK
    # --------------------------------------------------------

    overall_result = calculate_overall_risk(

        data_quality_result,

        sla_result
    )


    # --------------------------------------------------------
    # RECOMMENDATIONS
    # --------------------------------------------------------

    recommendations = generate_recommendations(

        source=source,

        anomaly_rate_result=
            anomaly_rate_result,

        anomaly_records_received=
            summary["anomaly_records_received"],

        rule_anomalies=
            summary["rule_anomalies"],

        ml_anomalies=
            summary["ml_anomalies"],

        processing_analysis=
            processing_analysis,

        data_quality_result=
            data_quality_result,

        sla_result=
            sla_result,

        overall_result=
            overall_result
    )


    # --------------------------------------------------------
    # FINAL SOURCE OUTPUT
    # --------------------------------------------------------

    return {

        "source":
            source,


        "pipeline_run_id":

            f"{source.upper()}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}",


        # ----------------------------------------------------
        # DATA METRICS
        # ----------------------------------------------------

        "metrics": {

            "anomaly_records_received":

                summary["anomaly_records_received"],


            "total_pipeline_records":

                total_pipeline_records,


            "anomaly_rate_available":

                anomaly_rate_result["available"],


            "pipeline_anomaly_rate":

                round(
                    anomaly_rate_result["rate"],
                    4
                )

                if anomaly_rate_result["available"]

                else None,


            "rule_anomalies":

                summary["rule_anomalies"],


            "ml_anomalies":

                summary["ml_anomalies"],


            "average_anomaly_risk_score":

                round(
                    summary["average_risk_score"],
                    4
                )
        },


        # ----------------------------------------------------
        # PROCESSING MONITORING
        # ----------------------------------------------------

        "processing_monitoring":

            processing_analysis,


        # ----------------------------------------------------
        # DATA QUALITY RISK
        # ----------------------------------------------------

        "data_quality_monitoring":

            data_quality_result,


        # ----------------------------------------------------
        # SLA MONITORING
        # ----------------------------------------------------

        "sla_monitoring": {

            "configured_sla_hours":

                config["sla_hours"],


            "sla_risk":

                sla_result["sla_risk"],


            "risk_points":

                sla_result["risk_points"],


            "risk_reasons":

                sla_result["risk_reasons"]
        },


        # ----------------------------------------------------
        # OVERALL PIPELINE RISK
        # ----------------------------------------------------

        "overall_risk":

            overall_result,


        # ----------------------------------------------------
        # RECOMMENDATIONS
        # ----------------------------------------------------

        "recommendations":

            recommendations
    }


# ============================================================
# MAIN FUNCTION
# ============================================================

def main():

    final_output = {

        "generated_at":

            datetime.now().isoformat(),


        "sources": []
    }


    # ========================================================
    # CLAIMS
    # ========================================================

    print("\n" + "#" * 60)
    print("LOADING CLAIMS JSON")
    print("#" * 60)


    claims_data = load_json(
        CLAIMS_JSON_PATH
    )


    if claims_data is not None:

        claims_records = find_record_list(
            claims_data
        )


        print(
            f"Claims records extracted: "
            f"{len(claims_records)}"
        )


        if claims_records:

            print(
                "Claims first record keys:"
            )

            print(
                list(
                    claims_records[0].keys()
                )
            )


            claims_source = detect_source(
                claims_records
            )


            print(
                f"Detected source: "
                f"{claims_source}"
            )


            claims_result = analyze_source(

                source="claims",

                records=claims_records,

                original_json_data=claims_data
            )


            if claims_result is not None:

                final_output["sources"].append(
                    claims_result
                )


        else:

            print(
                "WARNING: No records found in Claims JSON."
            )


    # ========================================================
    # AUTHORIZATION
    # ========================================================

    print("\n" + "#" * 60)
    print("LOADING AUTHORIZATION JSON")
    print("#" * 60)


    authorization_data = load_json(
        AUTHORIZATION_JSON_PATH
    )


    if authorization_data is not None:

        authorization_records = find_record_list(
            authorization_data
        )


        print(
            f"Authorization records extracted: "
            f"{len(authorization_records)}"
        )


        if authorization_records:

            print(
                "Authorization first record keys:"
            )

            print(
                list(
                    authorization_records[0].keys()
                )
            )


            authorization_source = detect_source(
                authorization_records
            )


            print(
                f"Detected source: "
                f"{authorization_source}"
            )


            authorization_result = analyze_source(

                source="authorization",

                records=authorization_records,

                original_json_data=authorization_data
            )


            if authorization_result is not None:

                final_output["sources"].append(
                    authorization_result
                )


        else:

            print(
                "WARNING: No records found in Authorization JSON."
            )


    # ========================================================
    # SAVE OUTPUT
    # ========================================================

    try:

        with open(
            OUTPUT_PATH,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(

                final_output,

                file,

                indent=4,

                ensure_ascii=False
            )


        # ====================================================
        # TERMINAL OUTPUT
        # ====================================================

        print("\n" + "=" * 60)
        print("SLA MONITORING COMPLETED")
        print("=" * 60)


        print(
            f"\nSources successfully processed: "
            f"{len(final_output['sources'])}"
        )


        for result in final_output["sources"]:

            print("\n" + "-" * 50)

            print(
                f"Source: "
                f"{result['source']}"
            )


            print(
                f"Anomaly Records Received: "
                f"{result['metrics']['anomaly_records_received']}"
            )


            print(
                f"Total Pipeline Records: "
                f"{result['metrics']['total_pipeline_records']}"
            )


            if result["metrics"]["anomaly_rate_available"]:

                print(
                    f"Actual Pipeline Anomaly Rate: "
                    f"{result['metrics']['pipeline_anomaly_rate']:.2%}"
                )

            else:

                print(
                    "Actual Pipeline Anomaly Rate: "
                    "NOT AVAILABLE"
                )


            print(
                f"Rule Anomalies: "
                f"{result['metrics']['rule_anomalies']}"
            )


            print(
                f"ML Anomalies: "
                f"{result['metrics']['ml_anomalies']}"
            )


            print(
                f"Data Quality Risk: "
                f"{result['data_quality_monitoring']['data_quality_risk']}"
            )


            print(
                f"SLA Risk: "
                f"{result['sla_monitoring']['sla_risk']}"
            )


            print(
                f"Overall Pipeline Risk: "
                f"{result['overall_risk']['overall_pipeline_risk']}"
            )


        print(
            "\nOutput saved to:"
        )

        print(
            OUTPUT_PATH
        )


    except Exception as error:

        print(
            "\nERROR saving output:"
        )

        print(
            error
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()