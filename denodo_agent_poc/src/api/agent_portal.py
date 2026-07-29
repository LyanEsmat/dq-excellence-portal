from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agent_api import app as agent_api_app


PROJECT_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_DIR = PROJECT_DIR.parent

DASHBOARD_FILE = (
    PROJECT_DIR
    / "templates"
    / "agent_dashboard.html"
)

STATIC_DIR = REPOSITORY_DIR / "static"


app = FastAPI(
    title="Agentic Data Quality Excellence Portal",
    description=(
        "Enterprise portal for semantic mapping, "
        "automated DQ execution and agent insights."
    ),
    version="1.0.0",
)


if not STATIC_DIR.exists():
    raise RuntimeError(
        f"Static folder was not found: {STATIC_DIR}"
    )


app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


# Reuse every tested Agent API endpoint.
for route in agent_api_app.routes:
    route_path = getattr(route, "path", "")

    if route_path.startswith("/api/"):
        app.router.routes.append(route)


@app.get("/", include_in_schema=False)
def portal_home():
    if not DASHBOARD_FILE.exists():
        return {
            "status": "Dashboard file missing",
            "expected_file": str(
                DASHBOARD_FILE
            ),
        }

    return FileResponse(DASHBOARD_FILE)


@app.get(
    "/portal-status",
    include_in_schema=False,
)
def portal_status():
    return {
        "status": "ready",
        "version": "1.0.0",
        "dashboard_exists": (
            DASHBOARD_FILE.exists()
        ),
        "static_directory_exists": (
            STATIC_DIR.exists()
        ),
        "api_routes_loaded": len(
            [
                route
                for route in app.routes
                if getattr(
                    route,
                    "path",
                    "",
                ).startswith("/api/")
            ]
        ),
    }