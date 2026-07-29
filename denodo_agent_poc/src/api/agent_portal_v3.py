from fastapi import FastAPI
from fastapi.responses import (
    HTMLResponse,
)
from fastapi.staticfiles import (
    StaticFiles,
)

import agent_api_v2
import agent_portal_v2


STATIC_DIR = (
    agent_portal_v2.STATIC_DIR
)

BASE_DASHBOARD_FILE = (
    agent_portal_v2.BASE_DASHBOARD_FILE
)


app = FastAPI(
    title=(
        "Agentic Data Quality "
        "Excellence Portal V3"
    ),
    description=(
        "Enterprise Data Quality portal "
        "connected to the adapter-based "
        "Agent API V2 and Pipeline V2."
    ),
    version="3.0.0",
)


if not STATIC_DIR.exists():
    raise RuntimeError(
        "Static directory was not found: "
        f"{STATIC_DIR}"
    )


app.mount(
    "/static",
    StaticFiles(
        directory=STATIC_DIR
    ),
    name="static",
)


# Load every API V2 route, including the new
# adapter-based Run Agent Pipeline endpoint.
for route in agent_api_v2.app.routes:
    route_path = getattr(
        route,
        "path",
        "",
    )

    if route_path.startswith("/api/"):
        app.router.routes.append(route)


@app.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def portal_home():
    if not BASE_DASHBOARD_FILE.exists():
        return HTMLResponse(
            (
                "<h1>Base dashboard "
                "file is missing.</h1>"
            ),
            status_code=500,
        )

    return HTMLResponse(
        agent_portal_v2.build_dashboard()
    )


@app.get(
    "/portal-status",
    include_in_schema=False,
)
def portal_status():
    return {
        "status": "ready",
        "portal_version": "3.0.0",
        "api_version": "2.0.0",
        "pipeline_version": "2.0.0",
        "data_source_architecture": (
            "adapter-based"
        ),
        "current_data_source": "excel",
        "base_dashboard_exists": (
            BASE_DASHBOARD_FILE.exists()
        ),
        "contacts_enabled": True,
        "rule_issue_panel_enabled": True,
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