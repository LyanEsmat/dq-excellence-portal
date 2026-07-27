from pathlib import Path
import subprocess
import sys

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from portal_app_final_v5 import (
    BASE_DIR,
    DASHBOARD_FILE,
    DASHBOARD_STYLES,
    LOGO_FIX,
    v2_api_app,
)

from portal_app_v2 import (
    MAPPING_FILE,
    dataframe_to_records,
    read_excel_sheet,
)


DQ_FILE_V3 = (
    BASE_DIR
    / "outputs"
    / "data_quality_results_v3.xlsx"
)


app = FastAPI(
    title="Data Quality Excellence Portal",
    description=(
        "Detailed Business Term Data Quality results "
        "with execution coverage."
    ),
    version="3.0.0",
)


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


@app.get("/api/v2/dashboard")
def get_dashboard_data():
    summary = read_excel_sheet(
        DQ_FILE_V3,
        "Summary",
    )

    dimensions = read_excel_sheet(
        DQ_FILE_V3,
        "Dimension Scores",
    )

    business_terms = read_excel_sheet(
        DQ_FILE_V3,
        "BT Scores",
    )

    columns = read_excel_sheet(
        DQ_FILE_V3,
        "Column Scores",
    )

    issues = read_excel_sheet(
        DQ_FILE_V3,
        "DQ Issues",
    )

    execution_summary = read_excel_sheet(
        DQ_FILE_V3,
        "Execution Summary",
    )

    return {
        "summary": dataframe_to_records(summary)[0],
        "execution_summary": dataframe_to_records(
            execution_summary
        ),
        "dimension_scores": dataframe_to_records(
            dimensions
        ),
        "business_term_scores": dataframe_to_records(
            business_terms
        ),
        "column_scores": dataframe_to_records(columns),
        "failures": dataframe_to_records(issues),
    }


@app.get("/api/v2/dq/checks")
def get_dq_checks():
    checks = read_excel_sheet(
        DQ_FILE_V3,
        "All DQ Checks",
    )

    return {
        "count": len(checks),
        "results": dataframe_to_records(checks),
    }


@app.get("/api/v2/dq/issues")
def get_dq_issues():
    issues = read_excel_sheet(
        DQ_FILE_V3,
        "DQ Issues",
    )

    return {
        "count": len(issues),
        "results": dataframe_to_records(issues),
    }


@app.post("/api/v2/run-pipeline")
def run_pipeline():
    commands = [
        [sys.executable, "mapping_engine.py"],
        [sys.executable, "dq_engine_v3.py"],
    ]

    execution_log = []

    for command in commands:
        result = subprocess.run(
            command,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        execution_log.append(
            {
                "command": " ".join(command),
                "return_code": result.returncode,
                "output": result.stdout,
                "error": result.stderr,
            }
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "The pipeline failed.",
                    "failed_command": " ".join(command),
                    "output": result.stdout,
                    "error": result.stderr,
                },
            )

    summary = read_excel_sheet(
        DQ_FILE_V3,
        "Summary",
    )

    return {
        "message": (
            "Mapping and Data Quality pipeline "
            "completed successfully."
        ),
        "summary": dataframe_to_records(summary)[0],
        "execution_log": execution_log,
    }


@app.get("/api/v2/download/dq-results")
def download_dq_results():
    if not DQ_FILE_V3.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "The V3 DQ results have not been "
                "generated. Run dq_engine_v3.py first."
            ),
        )

    return FileResponse(
        DQ_FILE_V3,
        filename="data_quality_results_v3.xlsx",
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )


# Reuse non-conflicting endpoints from the tested API.
excluded_routes = {
    "/api/v2/dashboard",
    "/api/v2/run-pipeline",
    "/api/v2/download/dq-results",
}

for route in v2_api_app.routes:
    route_path = getattr(route, "path", "")

    if not route_path.startswith("/api/v2/"):
        continue

    if route_path in excluded_routes:
        continue

    if route_path.startswith("/api/v2/dq/"):
        continue

    app.router.routes.append(route)


V6_STYLES = """
<style>
    .execution-summary {
        margin-bottom: 18px;
        padding: 18px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 22px;
        border: 1px solid #806f43;
        border-radius: 8px;
        background:
            linear-gradient(
                135deg,
                rgba(196, 170, 103, 0.10),
                rgba(11, 17, 16, 0.95)
            );
    }

    .execution-summary-title {
        margin: 0 0 8px;
        color: #efd47e;
        font-size: 16px;
    }

    .execution-summary-text {
        margin: 0;
        color: #c6d0cd;
        font-size: 12px;
        line-height: 1.65;
    }

    .execution-formula {
        padding: 15px;
        border: 1px solid #293633;
        border-radius: 6px;
        background: #08100f;
    }

    .formula-row {
        padding: 5px 0;
        display: flex;
        justify-content: space-between;
        gap: 15px;
        color: #9caeaa;
        font-size: 11px;
    }

    .formula-row strong {
        color: #f5f7f6;
        font-size: 12px;
    }

    .formula-row.total {
        margin-top: 6px;
        padding-top: 10px;
        border-top: 1px solid #293633;
    }

    .formula-row.total strong {
        color: #efd47e;
    }

    .dimension-secondary {
        margin-top: 11px;
        padding: 9px;
        display: flex;
        justify-content: space-between;
        gap: 8px;
        border: 1px solid #293633;
        border-radius: 5px;
        background: #0b1110;
        color: #9caeaa;
        font-size: 10px;
    }

    .dimension-secondary strong {
        color: #efd47e;
        font-size: 12px;
    }

    @media (max-width: 850px) {
        .execution-summary {
            grid-template-columns: 1fr;
        }
    }
</style>
"""


V6_SCRIPT = """
<script>
    function changeKpiText(
        valueElementId,
        label,
        note
    ) {
        const valueElement = document.getElementById(
            valueElementId
        );

        const card = valueElement.closest(".kpi");

        card.querySelector(
            ".kpi-label"
        ).textContent = label;

        card.querySelector(
            ".kpi-note"
        ).textContent = note;
    }


    changeKpiText(
        "businessTermsKpi",
        "Business Terms",
        "Terms assessed"
    );

    changeKpiText(
        "executionsKpi",
        "Planned DQ Checks",
        "Business Terms × six dimensions"
    );

    changeKpiText(
        "passedKpi",
        "Executed DQ Checks",
        "Checks that returned Passed or Failed"
    );

    changeKpiText(
        "failedKpi",
        "Failed DQ Checks",
        "Executed checks that violated rules"
    );

    changeKpiText(
        "notExecutedKpi",
        "Not Executed",
        "Checks missing required inputs"
    );

    changeKpiText(
        "overallScoreKpi",
        "Overall DQ Score",
        "Score from executed checks"
    );


    const firstPanel = document.querySelector(".panel");

    const summaryPanel = document.createElement("section");

    summaryPanel.id = "executionSummary";
    summaryPanel.className = "execution-summary";

    firstPanel.parentNode.insertBefore(
        summaryPanel,
        firstPanel
    );


    const businessTermTable =
        document.getElementById(
            "businessTermTableBody"
        ).closest("table");

    businessTermTable.querySelector(
        "thead"
    ).innerHTML = `
        <tr>
            <th>BT ID</th>
            <th>Business Term</th>
            <th>DQ Score</th>
            <th>Coverage</th>
            <th>Executed DQ</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Not Executed</th>
            <th>Planned DQ</th>
        </tr>
    `;


    const columnTable =
        document.getElementById(
            "columnTableBody"
        ).closest("table");

    columnTable.querySelector(
        "thead"
    ).innerHTML = `
        <tr>
            <th>Evaluated Column</th>
            <th>DQ Score</th>
            <th>Coverage</th>
            <th>Executed DQ</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Not Executed</th>
            <th>Planned DQ</th>
        </tr>
    `;


    renderSummary = function(summary) {
        const planned =
            numberValue(summary.planned_dq_checks);

        const executed =
            numberValue(summary.executed_dq_checks);

        const passed =
            numberValue(summary.passed_dq_checks);

        const failed =
            numberValue(summary.failed_dq_checks);

        const notExecuted =
            numberValue(
                summary.not_executed_dq_checks
            );

        const coverage =
            numberValue(summary.execution_coverage);

        document.getElementById(
            "businessTermsKpi"
        ).textContent =
            numberValue(
                summary.business_terms_assessed
            );

        document.getElementById(
            "executionsKpi"
        ).textContent = planned;

        document.getElementById(
            "passedKpi"
        ).textContent = executed;

        document.getElementById(
            "failedKpi"
        ).textContent = failed;

        document.getElementById(
            "notExecutedKpi"
        ).textContent = notExecuted;

        document.getElementById(
            "overallScoreKpi"
        ).textContent =
            percentage(summary.overall_dq_score);

        document.getElementById(
            "executionSummary"
        ).innerHTML = `
            <div>
                <h2 class="execution-summary-title">
                    How to read the DQ execution results
                </h2>

                <p class="execution-summary-text">
                    <strong>${planned} planned DQ checks</strong>
                    means that six checks were scheduled for
                    every Business Term. It does not mean that
                    all ${planned} checks successfully ran.
                    A check is counted as executed only when it
                    returns Passed or Failed.
                </p>

                <p class="execution-summary-text">
                    Failed and Not Executed are different,
                    mutually exclusive results for an individual
                    check. Failed means the check ran and found
                    a violation. Not Executed means the check
                    could not run because a required input was
                    unavailable.
                </p>
            </div>

            <div class="execution-formula">
                <div class="formula-row">
                    <span>Planned checks</span>
                    <strong>${planned}</strong>
                </div>

                <div class="formula-row">
                    <span>Passed checks</span>
                    <strong>${passed}</strong>
                </div>

                <div class="formula-row">
                    <span>Failed checks</span>
                    <strong>${failed}</strong>
                </div>

                <div class="formula-row">
                    <span>Executed = Passed + Failed</span>
                    <strong>${executed}</strong>
                </div>

                <div class="formula-row">
                    <span>Not executed</span>
                    <strong>${notExecuted}</strong>
                </div>

                <div class="formula-row total">
                    <span>Execution coverage</span>
                    <strong>${percentage(coverage)}</strong>
                </div>
            </div>
        `;
    };


    renderDimensions = function(dimensions) {
        const container = document.getElementById(
            "dimensionGrid"
        );

        container.innerHTML = dimensions.map((item) => {
            const score =
                numberValue(item.dq_score);

            const coverage =
                numberValue(item.execution_coverage);

            return `
                <article class="dimension-card">
                    <div class="dimension-name">
                        ${escapeHtml(item.dimension)}
                    </div>

                    <div class="dimension-score">
                        ${percentage(score)}
                    </div>

                    <div class="quality-metric-label">
                        DQ score from executed checks
                    </div>

                    <div class="score-track">
                        <div
                            class="score-fill"
                            style="width:${
                                Math.min(
                                    100,
                                    Math.max(0, score)
                                )
                            }%"
                        ></div>
                    </div>

                    <div class="dimension-secondary">
                        <span>Execution coverage</span>
                        <strong>
                            ${percentage(coverage)}
                        </strong>
                    </div>

                    <div class="dimension-breakdown">
                        <div>
                            <strong>
                                ${numberValue(item.executed_dq_checks)}
                            </strong>
                            Executed
                        </div>

                        <div>
                            <strong>
                                ${numberValue(item.failed)}
                            </strong>
                            Failed
                        </div>

                        <div>
                            <strong>
                                ${numberValue(item.not_executed)}
                            </strong>
                            Not run
                        </div>
                    </div>
                </article>
            `;
        }).join("");
    };


    renderColumns = function(columns) {
        document.getElementById(
            "columnCount"
        ).textContent =
            `${columns.length} evaluated column groups`;

        document.getElementById(
            "columnTableBody"
        ).innerHTML = columns.map((item) => `
            <tr>
                <td>
                    ${escapeHtml(item.target_column)}
                </td>

                <td class="score-cell">
                    ${percentage(item.dq_score)}
                </td>

                <td>
                    ${percentage(
                        item.execution_coverage
                    )}
                </td>

                <td>
                    ${numberValue(
                        item.executed_dq_checks
                    )}
                </td>

                <td>${numberValue(item.passed)}</td>
                <td>${numberValue(item.failed)}</td>

                <td>
                    ${numberValue(item.not_executed)}
                </td>

                <td>
                    ${numberValue(
                        item.planned_dq_checks
                    )}
                </td>
            </tr>
        `).join("");
    };


    renderBusinessTerms = function() {
        const search = document.getElementById(
            "businessTermSearch"
        ).value.trim().toLowerCase();

        const status = document.getElementById(
            "businessTermStatus"
        ).value;

        const sort = document.getElementById(
            "businessTermSort"
        ).value;

        let records = [
            ...dashboardData.business_term_scores
        ];

        records = records.filter((item) => {
            const searchable = `
                ${item.bt_id}
                ${item.business_term_name}
            `.toLowerCase();

            if (search && !searchable.includes(search)) {
                return false;
            }

            if (
                status === "failed"
                && numberValue(item.failed) === 0
            ) {
                return false;
            }

            if (
                status === "not-executed"
                && numberValue(item.not_executed) === 0
            ) {
                return false;
            }

            if (
                status === "passed"
                && (
                    numberValue(item.failed) > 0
                    || numberValue(
                        item.not_executed
                    ) > 0
                )
            ) {
                return false;
            }

            return true;
        });

        records.sort((a, b) => {
            if (sort === "highest") {
                return numberValue(b.dq_score)
                    - numberValue(a.dq_score);
            }

            if (sort === "name") {
                return String(
                    a.business_term_name
                ).localeCompare(
                    String(b.business_term_name)
                );
            }

            return numberValue(a.dq_score)
                - numberValue(b.dq_score);
        });

        document.getElementById(
            "businessTermCount"
        ).textContent =
            `${records.length} of ${
                dashboardData.business_term_scores.length
            } terms`;

        const tbody = document.getElementById(
            "businessTermTableBody"
        );

        if (!records.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="empty-state">
                        No Business Terms match the filters.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = records.map((item) => `
            <tr>
                <td>${escapeHtml(item.bt_id)}</td>

                <td>
                    ${escapeHtml(
                        item.business_term_name
                    )}
                </td>

                <td class="score-cell">
                    ${percentage(item.dq_score)}
                </td>

                <td>
                    ${percentage(
                        item.execution_coverage
                    )}
                </td>

                <td>
                    ${numberValue(
                        item.executed_dq_checks
                    )}
                </td>

                <td>${numberValue(item.passed)}</td>
                <td>${numberValue(item.failed)}</td>

                <td>
                    ${numberValue(item.not_executed)}
                </td>

                <td>
                    ${numberValue(
                        item.planned_dq_checks
                    )}
                </td>
            </tr>
        `).join("");
    };
</script>
"""


@app.get("/", include_in_schema=False)
def portal_home():
    if not DASHBOARD_FILE.exists():
        return HTMLResponse(
            "<h1>Dashboard file was not found.</h1>",
            status_code=404,
        )

    dashboard_html = DASHBOARD_FILE.read_text(
        encoding="utf-8"
    )

    dashboard_html = dashboard_html.replace(
        "/static/maaden-logo.png",
        "/static/maaden-logo-centered.png",
    )

    dashboard_html = dashboard_html.replace(
        "</head>",
        (
            f"{DASHBOARD_STYLES}"
            f"{LOGO_FIX}"
            f"{V6_STYLES}"
            "</head>"
        ),
    )

    dashboard_html = dashboard_html.replace(
        "</body>",
        f"{V6_SCRIPT}</body>",
    )

    return HTMLResponse(content=dashboard_html)


@app.get("/portal-status", include_in_schema=False)
def portal_status():
    return {
        "status": "ready",
        "version": "3.0.0",
        "dq_file": str(DQ_FILE_V3.name),
        "dq_file_exists": DQ_FILE_V3.exists(),
    }