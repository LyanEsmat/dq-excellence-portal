from pathlib import Path
from datetime import datetime, timezone
import csv
import json
import subprocess
import sys
import time


PROJECT_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_DIR = PROJECT_DIR.parent

RESULTS_DIR = PROJECT_DIR / "data" / "results"

LOCK_FILE = RESULTS_DIR / "pipeline.lock"

LATEST_LOG_FILE = (
    RESULTS_DIR
    / "latest_pipeline_run.json"
)

HISTORY_FILE = (
    RESULTS_DIR
    / "pipeline_run_history.csv"
)

MAXIMUM_LOCK_AGE_HOURS = 12


PIPELINE_STEPS = [
    {
        "name": "Baseline Technical Mapping",
        "script": (
            PROJECT_DIR
            / "src"
            / "technical_mapping_engine_v2.py"
        ),
    },
    {
        "name": "Semantic Mapping Agent",
        "script": (
            PROJECT_DIR
            / "src"
            / "agent"
            / "semantic_mapping_agent.py"
        ),
    },
    {
        "name": "DQ Rule Planning Agent",
        "script": (
            PROJECT_DIR
            / "src"
            / "agent"
            / "dq_rule_planning_agent.py"
        ),
    },
    {
        "name": "Email Rule Validation Repair",
        "script": (
            PROJECT_DIR
            / "src"
            / "agent"
            / "repair_email_rule.py"
        ),
    },
    {
        "name": "Batch DQ Execution",
        "script": (
            PROJECT_DIR
            / "src"
            / "engines"
            / "batch_dq_executor_v2.py"
        ),
    },
    {
        "name": "DQ Insights Agent",
        "script": (
            PROJECT_DIR
            / "src"
            / "agent"
            / "dq_insights_agent.py"
        ),
    },
    {
        "name": "Insight Consolidation Agent",
        "script": (
            PROJECT_DIR
            / "src"
            / "agent"
            / "insight_consolidation_agent.py"
        ),
    },
]


def utc_now():
    return datetime.now(
        timezone.utc
    )


def create_run_id():
    return utc_now().strftime(
        "RUN-%Y%m%d-%H%M%S"
    )


def lock_age_hours():
    if not LOCK_FILE.exists():
        return None

    lock_modified_time = datetime.fromtimestamp(
        LOCK_FILE.stat().st_mtime,
        tz=timezone.utc,
    )

    age = utc_now() - lock_modified_time

    return age.total_seconds() / 3600


def acquire_lock(run_id):
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if LOCK_FILE.exists():
        age = lock_age_hours()

        if (
            age is not None
            and age < MAXIMUM_LOCK_AGE_HOURS
        ):
            lock_information = (
                LOCK_FILE.read_text(
                    encoding="utf-8"
                )
            )

            raise RuntimeError(
                "Another pipeline run may still be "
                "active. Lock information:\n"
                f"{lock_information}"
            )

        print(
            "Removing a stale pipeline lock "
            f"older than {MAXIMUM_LOCK_AGE_HOURS} hours."
        )

        LOCK_FILE.unlink()

    lock_payload = {
        "run_id": run_id,
        "created_at": utc_now().isoformat(),
        "process_id": None,
    }

    LOCK_FILE.write_text(
        json.dumps(
            lock_payload,
            indent=2,
        ),
        encoding="utf-8",
    )


def release_lock():
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()


def execute_step(step_number, step):
    script_path = step["script"]

    if not script_path.exists():
        raise FileNotFoundError(
            f"Pipeline script is missing: "
            f"{script_path}"
        )

    started_at = utc_now()
    start_time = time.perf_counter()

    print()
    print(
        f"[{step_number}/{len(PIPELINE_STEPS)}] "
        f"{step['name']}"
    )
    print(f"Running: {script_path.name}")

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
        ],
        cwd=REPOSITORY_DIR,
        capture_output=True,
        text=True,
    )

    finished_at = utc_now()

    duration_seconds = round(
        time.perf_counter() - start_time,
        2,
    )

    if result.stdout:
        print(result.stdout.strip())

    if result.stderr:
        print(result.stderr.strip())

    status = (
        "Completed"
        if result.returncode == 0
        else "Failed"
    )

    return {
        "step_number": step_number,
        "step_name": step["name"],
        "script": str(script_path),
        "status": status,
        "return_code": result.returncode,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": duration_seconds,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def save_latest_log(run_log):
    LATEST_LOG_FILE.write_text(
        json.dumps(
            run_log,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def append_history(run_log):
    file_exists = HISTORY_FILE.exists()

    history_row = {
        "run_id": run_log["run_id"],
        "status": run_log["status"],
        "trigger": run_log["trigger"],
        "started_at": run_log["started_at"],
        "finished_at": run_log[
            "finished_at"
        ],
        "duration_seconds": run_log[
            "duration_seconds"
        ],
        "completed_steps": run_log[
            "completed_steps"
        ],
        "failed_step": run_log[
            "failed_step"
        ],
    }

    with open(
        HISTORY_FILE,
        "a",
        newline="",
        encoding="utf-8",
    ) as history_file:
        writer = csv.DictWriter(
            history_file,
            fieldnames=list(
                history_row.keys()
            ),
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(history_row)


def run_pipeline(trigger="Manual"):
    run_id = create_run_id()
    started_at = utc_now()
    start_time = time.perf_counter()

    run_log = {
        "run_id": run_id,
        "status": "Running",
        "trigger": trigger,
        "started_at": started_at.isoformat(),
        "finished_at": None,
        "duration_seconds": None,
        "completed_steps": 0,
        "failed_step": None,
        "steps": [],
    }

    print()
    print("=" * 60)
    print("DATA QUALITY AGENT PIPELINE")
    print("=" * 60)
    print(f"Run ID: {run_id}")
    print(f"Trigger: {trigger}")
    print(f"Started: {started_at.isoformat()}")

    try:
        acquire_lock(run_id)

        for step_number, step in enumerate(
            PIPELINE_STEPS,
            start=1,
        ):
            step_result = execute_step(
                step_number,
                step,
            )

            run_log["steps"].append(
                step_result
            )

            if step_result["status"] == "Failed":
                run_log["status"] = "Failed"
                run_log["failed_step"] = (
                    step["name"]
                )

                raise RuntimeError(
                    f"Pipeline stopped because "
                    f"'{step['name']}' failed."
                )

            run_log["completed_steps"] += 1

        run_log["status"] = "Completed"

    except Exception as error:
        run_log["status"] = "Failed"

        if run_log["failed_step"] is None:
            run_log["failed_step"] = (
                "Pipeline Initialization"
            )

        run_log["pipeline_error"] = str(
            error
        )

        print()
        print(f"PIPELINE ERROR: {error}")

    finally:
        finished_at = utc_now()

        run_log["finished_at"] = (
            finished_at.isoformat()
        )

        run_log["duration_seconds"] = round(
            time.perf_counter() - start_time,
            2,
        )

        save_latest_log(run_log)
        append_history(run_log)
        release_lock()

    print()
    print("=" * 60)
    print(f"Pipeline status: {run_log['status']}")
    print(
        f"Completed steps: "
        f"{run_log['completed_steps']}/"
        f"{len(PIPELINE_STEPS)}"
    )
    print(
        f"Duration: "
        f"{run_log['duration_seconds']} seconds"
    )

    if run_log["failed_step"]:
        print(
            f"Failed step: "
            f"{run_log['failed_step']}"
        )

    print(f"Latest log: {LATEST_LOG_FILE}")
    print(f"History: {HISTORY_FILE}")
    print("=" * 60)
    print()

    if run_log["status"] != "Completed":
        sys.exit(1)

    return run_log


if __name__ == "__main__":
    run_pipeline(trigger="Manual")
    