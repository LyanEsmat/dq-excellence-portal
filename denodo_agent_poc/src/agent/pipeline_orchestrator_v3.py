from copy import deepcopy
from pathlib import Path

import pipeline_orchestrator as base
import pipeline_orchestrator_v2


PROJECT_DIR = Path(__file__).resolve().parents[2]

V4_EXECUTOR_FILE = (
    PROJECT_DIR
    / "src"
    / "engines"
    / "batch_dq_executor_v4.py"
)


def create_v3_pipeline_steps():
    """
    Create the deployment-configured pipeline.

    V3 preserves all seven stages and replaces the
    previous executor with Batch DQ Executor V4.
    """
    steps = deepcopy(
        pipeline_orchestrator_v2
        .create_v2_pipeline_steps()
    )

    replacement_completed = False

    for step in steps:
        script_name = Path(
            step["script"]
        ).name

        if (
            script_name
            == "batch_dq_executor_v3.py"
        ):
            step["name"] = (
                "Deployment-Configured "
                "Batch DQ Execution"
            )

            step["script"] = (
                V4_EXECUTOR_FILE
            )

            replacement_completed = True
            break

    if not replacement_completed:
        raise RuntimeError(
            "Batch DQ Executor V3 could not "
            "be found in Pipeline V2."
        )

    return steps


def validate_v3_pipeline():
    if not V4_EXECUTOR_FILE.exists():
        raise FileNotFoundError(
            "Batch DQ Executor V4 "
            "is missing: "
            f"{V4_EXECUTOR_FILE}"
        )

    steps = create_v3_pipeline_steps()

    if len(steps) != 7:
        raise RuntimeError(
            "The deployment pipeline must "
            "contain seven stages."
        )

    missing_scripts = [
        str(step["script"])
        for step in steps
        if not Path(
            step["script"]
        ).exists()
    ]

    if missing_scripts:
        raise FileNotFoundError(
            "Pipeline scripts are missing: "
            + ", ".join(missing_scripts)
        )

    v4_steps = [
        step
        for step in steps
        if Path(
            step["script"]
        ).name
        == "batch_dq_executor_v4.py"
    ]

    if len(v4_steps) != 1:
        raise RuntimeError(
            "The pipeline must contain "
            "exactly one V4 executor."
        )

    return steps


def run_pipeline_v3(
    trigger: str = "Manual",
):
    base.PIPELINE_STEPS = (
        validate_v3_pipeline()
    )

    print()
    print(
        "Pipeline V3 deployment "
        "configuration validated."
    )
    print(
        "The DQ data source will be "
        "selected from .env."
    )

    return base.run_pipeline(
        trigger=trigger
    )


if __name__ == "__main__":
    run_pipeline_v3(
        trigger="Manual"
    )