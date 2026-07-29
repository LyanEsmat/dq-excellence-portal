from pathlib import Path
import subprocess
import sys

from fastapi import (
    FastAPI,
    HTTPException,
)

import agent_api as base


PROJECT_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_DIR = PROJECT_DIR.parent

ORCHESTRATOR_V2_FILE = (
    PROJECT_DIR
    / "src"
    / "agent"
    / "pipeline_orchestrator_v2.py"
)


app = FastAPI(
    title="Agentic Data Quality API V2",
    description=(
        "Data Quality API using an interchangeable "
        "data-source adapter and Pipeline V2."
    ),
    version="2.0.0",
)


# Reuse all validated API routes except the old pipeline endpoint.
for route in base.app.routes:
    route_path = getattr(
        route,
        "path",
        "",
    )

    if (
        route_path.startswith("/api/")
        and route_path != "/api/pipeline/run"
    ):
        app.router.routes.append(route)


@app.get("/", include_in_schema=False)
def api_home():
    return {
        "name": "Agentic Data Quality API",
        "version": "2.0.0",
        "data_source_architecture": (
            "adapter-based"
        ),
        "pipeline": (
            "pipeline_orchestrator_v2.py"
        ),
        "documentation": "/docs",
        "health": "/api/health",
    }


@app.post(
    "/api/pipeline/run",
    tags=["Pipeline"],
)
def run_pipeline_v2():
    if not ORCHESTRATOR_V2_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Pipeline Orchestrator V2 "
                "is missing."
            ),
        )

    result = subprocess.run(
        [
            sys.executable,
            str(ORCHESTRATOR_V2_FILE),
        ],
        cwd=REPOSITORY_DIR,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": (
                    "Agent Pipeline V2 failed."
                ),
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
        )

    latest_run = base.read_json(
        base.LATEST_PIPELINE_LOG
    )

    return {
        "message": (
            "Agent Pipeline V2 completed "
            "successfully."
        ),
        "pipeline_version": "2.0.0",
        "data_source_architecture": (
            "adapter-based"
        ),
        "latest_run": latest_run,
        "output": result.stdout,
    }


@app.get(
    "/api/system-configuration",
    tags=["System"],
)
def system_configuration():
    return {
        "api_version": "2.0.0",
        "pipeline_orchestrator": (
            ORCHESTRATOR_V2_FILE.name
        ),
        "pipeline_exists": (
            ORCHESTRATOR_V2_FILE.exists()
        ),
        "data_source_architecture": (
            "adapter-based"
        ),
        "current_data_source": "excel",
        "denodo_ready": False,
        "scheduled_execution": {
            "enabled": False,
            "planned_time": "06:00",
            "timezone": "Asia/Riyadh",
        },
    }