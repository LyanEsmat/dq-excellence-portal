from copy import deepcopy
from pathlib import Path

import pipeline_orchestrator as base


PROJECT_DIR = Path(__file__).resolve().parents[2]

V3_EXECUTOR_FILE = (
    PROJECT_DIR
    / "src"
    / "engines"
    / "batch_dq_executor_v3.py"
)


def create_v2_pipeline_steps():
    """
    Preserve the seven validated pipeline stages while replacing
    Batch DQ Executor V2 with the data-source-independent V3.
    """
    steps = deepcopy(
        base.PIPELINE_STEPS
    )

    replacement_completed = False

    for step in steps:
        if step["name"] == "Batch DQ Execution":
            step["name"] = (
                "Data-Source-Independent "
                "Batch DQ Execution"
            )

            step["script"] = (
                V3_EXECUTOR_FILE
            )

            replacement_completed = True
            break

    if not replacement_completed:
        raise RuntimeError(
            "The Batch DQ Execution stage could "
            "not be found in the original pipeline."
        )

    return steps


def validate_v2_pipeline():
    if not V3_EXECUTOR_FILE.exists():
        raise FileNotFoundError(
            "Batch DQ Executor V3 is missing: "
            f"{V3_EXECUTOR_FILE}"
        )

    steps = create_v2_pipeline_steps()

    if len(steps) != 7:
        raise RuntimeError(
            "The pipeline must contain exactly "
            f"seven stages, but {len(steps)} were found."
        )

    missing_scripts = [
        str(step["script"])
        for step in steps
        if not Path(step["script"]).exists()
    ]

    if missing_scripts:
        raise FileNotFoundError(
            "Pipeline scripts are missing: "
            + ", ".join(missing_scripts)
        )

    v3_steps = [
        step
        for step in steps
        if Path(step["script"]).name
        == "batch_dq_executor_v3.py"
    ]

    if len(v3_steps) != 1:
        raise RuntimeError(
            "The pipeline must contain exactly "
            "one V3 DQ executor stage."
        )

    return steps


def run_pipeline_v2(
    trigger: str = "Manual",
):
    """
    Execute the full agent pipeline using the configured
    data-source adapter.
    """
    base.PIPELINE_STEPS = (
        validate_v2_pipeline()
    )

    print()
    print(
        "Pipeline V2 configuration validated."
    )
    print(
        "DQ execution source: "
        "configured data-source adapter"
    )

    return base.run_pipeline(
        trigger=trigger
    )


if __name__ == "__main__":
    run_pipeline_v2(
        trigger="Manual"
    )