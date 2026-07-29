from fastapi import FastAPI
from fastapi.responses import (
    HTMLResponse,
)
from fastapi.staticfiles import (
    StaticFiles,
)

import agent_api_v3
import agent_portal_v2


STATIC_DIR = (
    agent_portal_v2.STATIC_DIR
)

BASE_DASHBOARD_FILE = (
    agent_portal_v2
    .BASE_DASHBOARD_FILE
)


app = FastAPI(
    title=(
        "Agentic Data Quality "
        "Excellence Portal V4"
    ),
    description=(
        "Deployment-configured enterprise "
        "Data Quality portal connected to "
        "API V3 and Pipeline V3."
    ),
    version="4.0.0",
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


for route in agent_api_v3.app.routes:
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
    configuration = (
        agent_api_v3
        .system_configuration()
    )

    return {
        "status": "ready",
        "portal_version": "4.0.0",
        "api_version": "3.0.0",
        "pipeline_version": "3.0.0",
        "environment": configuration[
            "environment"
        ],
        "data_source": configuration[
            "data_source"
        ],
        "schedule_enabled": configuration[
            "schedule_enabled"
        ],
        "schedule_time": configuration[
            "schedule_time"
        ],
        "timezone": configuration[
            "timezone"
        ],
        "denodo_configured": configuration[
            "denodo_configured"
        ],
        "api_auth_enabled": configuration[
            "api_auth_enabled"
        ],
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