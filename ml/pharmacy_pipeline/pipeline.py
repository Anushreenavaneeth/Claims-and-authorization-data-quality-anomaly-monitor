import subprocess
import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent


# ============================================================
# PIPELINE STAGES
# ============================================================

STAGES = [
    (
        "EDA",
        "preprocessing/eda.py",
    ),
    (
        "PREPROCESSING",
        "preprocessing/preprocess.py",
    ),
    (
        "VALIDATION",
        "validation/pharmacy_validation.py",
    ),
    (
        "FEATURE ENGINEERING",
        "features/pharmacy_features.py",
    ),
    (
        "BEHAVIOR ANALYSIS",
        "behavior/pharmacy_behavior.py",
    ),
    (
        "ML ANOMALY DETECTION",
        "ml/pharmacy_anomaly.py",
    ),
    (
        "RULE DETECTION",
        "rules/pharmacy_rules.py",
    ),
    (
        "DECISION ENGINE",
        "decision/pharmacy_decision.py",
    ),
    (
        "SLA RISK",
        "sla/pharmacy_sla.py",
    ),
    (
        "FINAL JSON",
        "output/pharmacy_json.py",
    ),
]


# ============================================================
# RUN ONE STAGE
# ============================================================

def run_stage(stage_name, script_path):

    print("\n")
    print("=" * 80)
    print(f"STARTING: {stage_name}")
    print("=" * 80)

    script = PROJECT_ROOT / script_path

    if not script.exists():

        print(
            f"\nERROR: Stage file does not exist:"
        )

        print(script)

        return False

    print(
        f"\nRunning:"
    )

    print(script)

    result = subprocess.run(
        [
            sys.executable,
            str(script),
        ],
        cwd=PROJECT_ROOT,
    )

    if result.returncode != 0:

        print("\n" + "=" * 80)
        print(
            f"FAILED: {stage_name}"
        )
        print("=" * 80)

        print(
            f"\nExit code: "
            f"{result.returncode}"
        )

        return False

    print("\n" + "=" * 80)
    print(
        f"COMPLETED: {stage_name}"
    )
    print("=" * 80)

    return True


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print("=" * 80)
    print("PHARMACY ANOMALY DETECTION PIPELINE")
    print("=" * 80)

    print(
        "\nProject root:"
    )

    print(PROJECT_ROOT)

    print(
        "\nTotal stages:"
    )

    print(len(STAGES))

    # --------------------------------------------------------
    # Run stages
    # --------------------------------------------------------

    completed = 0

    for stage_name, script_path in STAGES:

        success = run_stage(
            stage_name,
            script_path,
        )

        if not success:

            print("\n" + "=" * 80)
            print("PHARMACY PIPELINE FAILED")
            print("=" * 80)

            print(
                f"\nFailed stage:"
            )

            print(stage_name)

            print(
                "\nPipeline stopped."
            )

            sys.exit(1)

        completed += 1

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("PHARMACY PIPELINE COMPLETED")
    print("=" * 80)

    print(
        f"\nCompleted stages: "
        f"{completed}/{len(STAGES)}"
    )

    print(
        "\nFinal output directory:"
    )

    print(
        PROJECT_ROOT
        / "data"
        / "final_output"
    )

    print("=" * 80)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()