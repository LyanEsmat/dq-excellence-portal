from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import app as existing_api_app


BASE_DIR = Path(__file__).resolve().parent


app = FastAPI(
    title="Data Quality Excellence Portal",
    version="1.0.0",
)


app.mount(
    "/static",
    StaticFiles(
        directory=BASE_DIR / "static"
    ),
    name="static",
)


# Reuse all working API endpoints from app.py.
for route in existing_api_app.routes:
    route_path = getattr(route, "path", "")

    if route_path.startswith("/api/"):
        app.router.routes.append(route)


@app.get(
    "/",
    include_in_schema=False,
)
def portal_home():
    return FileResponse(
        BASE_DIR
        / "templates"
        / "portal_dashboard.html"
    )