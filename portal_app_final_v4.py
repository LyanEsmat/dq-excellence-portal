from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from portal_app_final_v3 import (
    BASE_DIR,
    DASHBOARD_FILE,
    DASHBOARD_SCRIPT,
    DASHBOARD_STYLES,
    v2_api_app,
)


app = FastAPI(
    title="Data Quality Excellence Portal",
    description=(
        "Business Term mapping and detailed "
        "Data Quality assessment portal."
    ),
    version="2.3.0",
)


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


for route in v2_api_app.routes:
    route_path = getattr(route, "path", "")

    if route_path.startswith("/api/v2/"):
        app.router.routes.append(route)


WHY_STYLES = """
<style>
    .dimension-card {
        position: relative;
    }

    .why-button {
        position: absolute;
        top: 12px;
        right: 12px;
        padding: 3px 8px;
        border: 1px solid #806f43;
        border-radius: 999px;
        background: transparent;
        color: #efd47e;
        font-size: 9px;
        font-weight: 700;
        line-height: 1.4;
    }

    .why-button:hover {
        border-color: #efd47e;
        background: rgba(196, 170, 103, 0.12);
    }

    .why-overlay {
        position: fixed;
        inset: 0;
        z-index: 1000;
        padding: 20px;
        display: none;
        align-items: center;
        justify-content: center;
        background: rgba(0, 0, 0, 0.76);
        backdrop-filter: blur(5px);
    }

    .why-overlay.visible {
        display: flex;
    }

    .why-dialog {
        width: min(540px, 100%);
        overflow: hidden;
        border: 1px solid #806f43;
        border-radius: 9px;
        background: #101817;
        box-shadow: 0 24px 70px rgba(0, 0, 0, 0.6);
    }

    .why-dialog-header {
        padding: 16px 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        border-bottom: 1px solid #293633;
        background: #151e1c;
    }

    .why-dialog-title {
        margin: 0;
        color: #efd47e;
        font-size: 17px;
    }

    .why-close {
        width: 32px;
        height: 32px;
        display: grid;
        place-items: center;
        border: 1px solid #394744;
        border-radius: 50%;
        background: transparent;
        color: #f5f7f6;
        font-size: 20px;
        line-height: 1;
    }

    .why-close:hover {
        border-color: #efd47e;
        color: #efd47e;
    }

    .why-dialog-body {
        padding: 18px;
        color: #dbe2e0;
        font-size: 13px;
        line-height: 1.65;
    }

    .why-score-box {
        margin-bottom: 15px;
        padding: 13px;
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        border: 1px solid #293633;
        border-radius: 6px;
        background: #0b1110;
    }

    .why-score-item {
        color: #9caeaa;
        font-size: 10px;
    }

    .why-score-item strong {
        margin-top: 4px;
        display: block;
        color: #efd47e;
        font-size: 20px;
    }

    .why-explanation {
        margin: 0;
    }

    .why-example {
        margin-top: 15px;
        padding: 12px;
        border-left: 3px solid #c4aa67;
        background: rgba(196, 170, 103, 0.08);
        color: #cbd4d1;
    }

    .why-status-list {
        margin: 15px 0 0;
        padding: 0;
        list-style: none;
    }

    .why-status-list li {
        margin-top: 7px;
        color: #9caeaa;
    }

    .why-status-list strong {
        color: #f5f7f6;
    }
</style>
"""


WHY_SCRIPT = """
<script>
    const whyOverlay = document.createElement("div");

    whyOverlay.id = "whyOverlay";
    whyOverlay.className = "why-overlay";

    whyOverlay.innerHTML = `
        <div
            class="why-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="whyDialogTitle"
        >
            <div class="why-dialog-header">
                <h3
                    id="whyDialogTitle"
                    class="why-dialog-title"
                >
                    DQ score explanation
                </h3>

                <button
                    id="whyCloseButton"
                    class="why-close"
                    aria-label="Close explanation"
                >
                    ×
                </button>
            </div>

            <div
                id="whyDialogBody"
                class="why-dialog-body"
            ></div>
        </div>
    `;

    document.body.appendChild(whyOverlay);

    function closeWhyExplanation() {
        whyOverlay.classList.remove("visible");
    }

    document.getElementById(
        "whyCloseButton"
    ).addEventListener(
        "click",
        closeWhyExplanation
    );

    whyOverlay.addEventListener("click", function(event) {
        if (event.target === whyOverlay) {
            closeWhyExplanation();
        }
    });

    document.addEventListener("keydown", function(event) {
        if (event.key === "Escape") {
            closeWhyExplanation();
        }
    });

    function showWhyExplanation(
        dimension,
        score,
        passed,
        failed,
        notExecuted
    ) {
        const total = passed + failed + notExecuted;

        const complianceRate = total > 0
            ? (passed / total) * 100
            : 0;

        let explanation = `
            The displayed score is the average result
            calculated from the values evaluated by this
            Data Quality dimension.
        `;

        let example = `
            The average score and the number of fully
            compliant Business Terms measure different
            things, so they do not always have to match.
        `;

        if (dimension === "Completeness") {
            explanation = `
                The Completeness score measures the average
                percentage of required fields that are
                populated across all Business Terms.
                A Business Term passes only when all of its
                required fields are populated.
            `;

            example = `
                For example, a Business Term with most of
                its required fields populated can contribute
                a high completeness score but still fail
                because at least one required field is
                missing. Therefore, an average score of
                ${percentage(score)} can coexist with
                ${failed} failed Business Terms.
            `;
        }

        if (dimension === "Validity") {
            explanation = `
                The Validity score measures whether evaluated
                values follow their expected format and
                accepted-value rules. A Business Term fails
                if one or more required validity checks fail.
            `;
        }

        if (dimension === "Accuracy") {
            explanation = `
                The Accuracy score measures whether the
                Data Steward was successfully mapped to an
                accepted employee metadata record.
            `;
        }

        if (dimension === "Consistency") {
            explanation = `
                The Consistency score measures how closely
                the steward name agrees with the matched
                employee name after text normalization.
            `;
        }

        if (dimension === "Uniqueness") {
            explanation = `
                The Uniqueness score measures whether every
                Business Term ID occurs only once in the
                assessed dataset.
            `;
        }

        if (dimension === "Timeliness") {
            explanation = `
                The Timeliness score measures how recently
                the supporting employee metadata was updated.
                Missing or stale update dates can fail or
                prevent this evaluation.
            `;
        }

        document.getElementById(
            "whyDialogTitle"
        ).textContent = `${dimension}: why this result?`;

        document.getElementById(
            "whyDialogBody"
        ).innerHTML = `
            <div class="why-score-box">
                <div class="why-score-item">
                    Average DQ score
                    <strong>${percentage(score)}</strong>
                </div>

                <div class="why-score-item">
                    Fully compliant BTs
                    <strong>
                        ${percentage(complianceRate)}
                    </strong>
                </div>
            </div>

            <p class="why-explanation">
                ${explanation}
            </p>

            <div class="why-example">
                ${example}
            </div>

            <ul class="why-status-list">
                <li>
                    <strong>Passed:</strong>
                    ${passed} Business Terms satisfied
                    the complete dimension rule.
                </li>

                <li>
                    <strong>Failed:</strong>
                    ${failed} Business Terms were evaluated
                    but did not satisfy the complete rule.
                </li>

                <li>
                    <strong>Not run:</strong>
                    ${notExecuted} Business Terms could not
                    be evaluated because required inputs
                    were unavailable.
                </li>
            </ul>
        `;

        whyOverlay.classList.add("visible");
    }


    renderDimensions = function(dimensions) {
        const container = document.getElementById(
            "dimensionGrid"
        );

        container.innerHTML = dimensions.map((item) => {
            const score = numberValue(item.score);
            const passed = numberValue(item.passed);
            const failed = numberValue(item.failed);
            const notExecuted =
                numberValue(item.not_executed);

            const total = passed + failed + notExecuted;

            const complianceRate = total > 0
                ? (passed / total) * 100
                : 0;

            let complianceClass = "low";

            if (complianceRate >= 90) {
                complianceClass = "high";
            } else if (complianceRate >= 70) {
                complianceClass = "medium";
            }

            const scoreDescription =
                item.dimension === "Completeness"
                    ? "Average required-field completeness"
                    : "Average executed-rule score";

            return `
                <article class="dimension-card">
                    <button
                        class="why-button"
                        onclick='showWhyExplanation(
                            ${JSON.stringify(item.dimension)},
                            ${score},
                            ${passed},
                            ${failed},
                            ${notExecuted}
                        )'
                    >
                        Why?
                    </button>

                    <div class="dimension-name">
                        ${escapeHtml(item.dimension)}
                    </div>

                    <div class="dimension-score">
                        ${percentage(score)}
                    </div>

                    <div class="quality-metric-label">
                        ${scoreDescription}
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

                    <div class="compliance-row ${complianceClass}">
                        <span>Fully compliant BTs</span>

                        <strong>
                            ${percentage(complianceRate)}
                        </strong>
                    </div>

                    <div class="dimension-breakdown">
                        <div>
                            <strong>${passed}</strong>
                            Passed
                        </div>

                        <div>
                            <strong>${failed}</strong>
                            Failed
                        </div>

                        <div>
                            <strong>${notExecuted}</strong>
                            Not run
                        </div>
                    </div>
                </article>
            `;
        }).join("");
    };
</script>
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
        f"{DASHBOARD_STYLES}{WHY_STYLES}</head>",
    )

    dashboard_html = dashboard_html.replace(
        "</body>",
        f"{DASHBOARD_SCRIPT}{WHY_SCRIPT}</body>",
    )

    return HTMLResponse(content=dashboard_html)


@app.get("/portal-status", include_in_schema=False)
def portal_status():
    return {
        "status": "ready",
        "version": "2.3.0",
        "dashboard_exists": DASHBOARD_FILE.exists(),
        "dimension_explanations": "enabled",
        "business_term_results": "scrollable",
        "dq_failures": "scrollable",
        "steward_mapping": "scrollable",
    }