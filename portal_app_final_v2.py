from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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
    version="2.1.0",
)


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


# Reuse the tested V2 API endpoints.
for route in v2_api_app.routes:
    route_path = getattr(route, "path", "")

    if route_path.startswith("/api/v2/"):
        app.router.routes.append(route)


DASHBOARD_IMPROVEMENTS = """
<style>
    /* Move the complete MAADEN logo slightly downward. */
    .logo-window {
        transform: translateY(5px);
    }

    /*
       Give Business Term DQ results an independent
       scrollable sub-window.
    */
    .panel:has(#businessTermTableBody) .table-wrap {
        max-height: 430px;
        overflow-x: auto;
        overflow-y: auto;
        border: 1px solid #293633;
        border-radius: 6px;
        scrollbar-color: #c4aa67 #101817;
        scrollbar-width: thin;
    }

    /*
       Keep the table headings visible while the user
       scrolls through Business Term results.
    */
    .panel:has(#businessTermTableBody) thead th {
        position: sticky;
        top: 0;
        z-index: 5;
        background: #08100f;
        box-shadow: 0 1px 0 #293633;
    }

    /*
       Give failed and not-executed DQ results their
       own scrollable sub-window.
    */
    #failureGrid {
        max-height: 520px;
        overflow-y: auto;
        padding: 4px 10px 4px 4px;
        scrollbar-color: #c4aa67 #101817;
        scrollbar-width: thin;
    }

    /*
       Chrome and Edge scrollbar styling.
    */
    .panel:has(#businessTermTableBody) .table-wrap::-webkit-scrollbar,
    #failureGrid::-webkit-scrollbar {
        width: 9px;
        height: 9px;
    }

    .panel:has(#businessTermTableBody) .table-wrap::-webkit-scrollbar-track,
    #failureGrid::-webkit-scrollbar-track {
        background: #101817;
        border-radius: 999px;
    }

    .panel:has(#businessTermTableBody) .table-wrap::-webkit-scrollbar-thumb,
    #failureGrid::-webkit-scrollbar-thumb {
        background: #806f43;
        border: 2px solid #101817;
        border-radius: 999px;
    }

    .panel:has(#businessTermTableBody) .table-wrap::-webkit-scrollbar-thumb:hover,
    #failureGrid::-webkit-scrollbar-thumb:hover {
        background: #c4aa67;
    }

    /*
       Visual boundary around the DQ-results window.
    */
    .panel:has(#failureGrid) .panel-body {
        background: #090f0e;
    }

    @media (max-width: 850px) {
        .panel:has(#businessTermTableBody) .table-wrap {
            max-height: 500px;
        }

        #failureGrid {
            max-height: 600px;
        }
    }
</style>
"""


@app.get("/", include_in_schema=False)
def portal_home():
    if not DASHBOARD_FILE.exists():
        return HTMLResponse(
            content=(
                "<h1>Dashboard file not found</h1>"
                "<p>Expected templates/"
                "dq_dashboard_final.html</p>"
            ),
            status_code=404,
        )

    dashboard_html = DASHBOARD_FILE.read_text(
        encoding="utf-8"
    )

    dashboard_html = dashboard_html.replace(
        "</head>",
        f"{DASHBOARD_IMPROVEMENTS}</head>",
    )

    return HTMLResponse(content=dashboard_html)


@app.get("/portal-status", include_in_schema=False)
def portal_status():
    return {
        "status": "ready",
        "version": "2.1.0",
        "dashboard_exists": DASHBOARD_FILE.exists(),
        "business_term_window": "scrollable",
        "dq_failure_window": "scrollable",
        "logo_adjustment": "moved downward",
    }