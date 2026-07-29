from pathlib import Path
import subprocess
import sys

from fastapi import (
    FastAPI,
    HTTPException,
)

import agent_api as core
import agent_api_v2


PROJECT_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_DIR = PROJECT_DIR.parent
CONFIG_DIRECTORY = PROJECT_DIR / "config"

if str(CONFIG_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(CONFIG_DIRECTORY),
    )


from deployment_settings import (  # noqa: E402
    get_settings,
)


ORCHESTRATOR_V3_FILE = (
    PROJECT_DIR
    / "src"
    / "agent"
    / "pipeline_orchestrator_v3.py"
)


app = FastAPI(
    title="Agentic Data Quality API V3",
    description=(
        "Deployment-configured Data Quality API "
        "with environment-based source selection."
    ),
    version="3.0.0",
)


# Keep all validated API endpoints except the two
# endpoints replaced by this deployment version.
for route in agent_api_v2.app.routes:
    route_path = getattr(
        route,
        "path",
        "",
    )

    if (
        route_path.startswith("/api/")
        and route_path
        not in {
            "/api/pipeline/run",
            "/api/system-configuration",
        }
    ):
        app.router.routes.append(route)


@app.get("/", include_in_schema=False)
def api_home():
    settings = get_settings()

    return {
        "name": (
            "Agentic Data Quality API"
        ),
        "version": "3.0.0",
        "environment": (
            settings.environment
        ),
        "data_source": (
            settings.data_source
        ),
        "pipeline": (
            ORCHESTRATOR_V3_FILE.name
        ),
        "documentation": "/docs",
        "health": "/api/health",
    }


@app.post(
    "/api/pipeline/run",
    tags=["Pipeline"],
)
def run_pipeline_v3():
    if not ORCHESTRATOR_V3_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Pipeline Orchestrator V3 "
                "is missing."
            ),
        )

    settings = get_settings()

    result = subprocess.run(
        [
            sys.executable,
            str(ORCHESTRATOR_V3_FILE),
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
                    "Deployment-configured "
                    "agent pipeline failed."
                ),
                "data_source": (
                    settings.data_source
                ),
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
        )

    latest_run = core.read_json(
        core.LATEST_PIPELINE_LOG
    )

    return {
        "message": (
            "Deployment-configured agent "
            "pipeline completed successfully."
        ),
        "api_version": "3.0.0",
        "pipeline_version": "3.0.0",
        "environment": (
            settings.environment
        ),
        "data_source": (
            settings.data_source
        ),
        "latest_run": latest_run,
        "output": result.stdout,
    }


@app.get(
    "/api/system-configuration",
    tags=["System"],
)
def system_configuration():
    settings = get_settings()
    configuration = (
        settings.safe_summary()
    )

    return {
        "api_version": "3.0.0",
        "pipeline_version": "3.0.0",
        "pipeline_orchestrator": (
            ORCHESTRATOR_V3_FILE.name
        ),
        "pipeline_exists": (
            ORCHESTRATOR_V3_FILE.exists()
        ),
        **configuration,
    }