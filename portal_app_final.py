from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from portal_app_v2 import app as v2_api_app


BASE_DIR = Path(__file__).resolve().parent

DASHBOARD_FILE = (
    BASE_DIR
    / "templates"
    / "dq_dashboard_final.html"
)


app = FastAPI(
    title="Data Quality Excellence Portal",
    description=(
        "Business Term mapping and detailed "
        "Data Quality assessment portal."
    ),
    version="2.0.0",
)


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


# Reuse all tested V2 API endpoints.
for route in v2_api_app.routes:
    route_path = getattr(route, "path", "")

    if route_path.startswith("/api/v2/"):
        app.router.routes.append(route)


@app.get("/", include_in_schema=False)
def portal_home():
    return FileResponse(DASHBOARD_FILE)


@app.get("/portal-status", include_in_schema=False)
def portal_status():
    return {
        "status": "ready",
        "dashboard": DASHBOARD_FILE.name,
        "dashboard_exists": DASHBOARD_FILE.exists(),
        "api_version": "2.0.0",
    }