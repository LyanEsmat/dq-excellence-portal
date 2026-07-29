from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from agent_api import app as agent_api_app


PROJECT_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_DIR = PROJECT_DIR.parent
BASE_DASHBOARD_FILE = PROJECT_DIR / "templates" / "agent_dashboard.html"
STATIC_DIR = REPOSITORY_DIR / "static"


CONTACT_CSS = """
        .team-contacts {
            position: relative;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .contact-circles {
            display: flex;
        }

        .contact-trigger {
            border: 0;
            background: transparent;
            color: inherit;
            cursor: pointer;
        }

        .contact-circle {
            width: 42px;
            height: 42px;
            padding: 0;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 1px solid var(--gold);
            border-radius: 50%;
            background: #0c1211;
            color: var(--gold-light);
            font-size: 12px;
            transition: transform .15s, background .15s;
        }

        .contact-circle + .contact-circle {
            margin-left: -7px;
        }

        .contact-circle:hover,
        .contact-name:hover {
            color: var(--gold-light);
            transform: translateY(-1px);
        }

        .contact-name {
            padding: 0;
            font-size: 14px;
            font-weight: 700;
        }

        .contact-popover {
            position: absolute;
            top: calc(100% + 14px);
            right: 0;
            z-index: 20;
            width: min(340px, calc(100vw - 32px));
            padding: 14px;
            display: none;
            border: 1px solid #5f5335;
            border-radius: 8px;
            background: #101816;
            box-shadow: 0 18px 45px rgba(0, 0, 0, .45);
            text-align: left;
        }

        .contact-popover.visible {
            display: block;
        }

        .contact-popover::before {
            position: absolute;
            top: -7px;
            right: 25px;
            width: 12px;
            height: 12px;
            content: "";
            border-top: 1px solid #5f5335;
            border-left: 1px solid #5f5335;
            background: #101816;
            transform: rotate(45deg);
        }

        .contact-card-name {
            color: var(--text);
            font-weight: 750;
        }

        .contact-card-email {
            margin: 7px 0 12px;
            color: var(--muted);
            font-size: 12px;
            overflow-wrap: anywhere;
        }

        .contact-email-button {
            width: 100%;
            min-height: 38px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 1px solid var(--gold);
            border-radius: 5px;
            background: var(--gold);
            color: #080a08;
            font-weight: 750;
            text-decoration: none;
        }

        .issue-summary {
            margin: 0 0 12px;
            color: var(--muted);
            font-size: 11px;
            line-height: 1.55;
        }

        .issue-toolbar {
            margin-bottom: 12px;
            display: grid;
            grid-template-columns: 1fr 210px;
            gap: 9px;
        }

        .issue-reason,
        .issue-action {
            min-width: 260px;
            white-space: normal;
            line-height: 1.5;
        }

        .issue-action {
            color: #dce4e2;
        }

        .status-note {
            color: var(--muted);
        }

        @media (max-width: 800px) {
            .team-contacts {
                width: 100%;
                justify-content: space-between;
            }

            .issue-toolbar {
                grid-template-columns: 1fr;
            }
        }
"""


CONTACT_HTML = """
    <div class="team-contacts">
        <div class="contact-circles" aria-label="Project contacts">
            <button
                class="contact-trigger contact-circle"
                data-contact="lyan"
                aria-label="Contact Lyan Esmat"
                type="button"
            >LE</button>
            <button
                class="contact-trigger contact-circle"
                data-contact="moath"
                aria-label="Contact Moath AlSoqair"
                type="button"
            >MA</button>
        </div>

        <div class="team">
            <strong>
                <button
                    class="contact-trigger contact-name"
                    data-contact="lyan"
                    type="button"
                >Lyan Esmat</button>
                &amp;
                <button
                    class="contact-trigger contact-name"
                    data-contact="moath"
                    type="button"
                >Moath AlSoqair</button>
            </strong>
            <div>Data &amp; AI Platform Governance</div>
        </div>

        <div
            id="contactPopover"
            class="contact-popover"
            role="dialog"
            aria-live="polite"
        >
            <div id="contactCardName" class="contact-card-name"></div>
            <div id="contactCardEmail" class="contact-card-email"></div>
            <a id="contactEmailButton" class="contact-email-button" href="#">
                Email
            </a>
        </div>
    </div>
"""


ISSUE_PANEL_HTML = """
    <section class="panel">
        <div class="panel-header">
            <h2 class="panel-title">
                Failed and Not-Executed DQ Rules
            </h2>
            <span id="issueCount" class="panel-count"></span>
        </div>
        <div class="panel-body">
            <p class="issue-summary">
                <strong>Failed</strong> means the rule ran and found
                defective records. <strong>Not Executed</strong> means an
                applicable rule could not run because a required source,
                column, reference or input was unavailable.
            </p>
            <div class="issue-toolbar">
                <input
                    id="issueSearch"
                    class="input"
                    placeholder="Search BT, Business Unit, table, column or dimension..."
                >
                <select id="issueStatus" class="select">
                    <option value="all">Failed + Not Executed</option>
                    <option value="Failed">Failed only</option>
                    <option value="Not Executed">Not Executed only</option>
                </select>
            </div>
            <div class="scroll-window">
                <table>
                    <thead>
                    <tr>
                        <th>Business Term</th>
                        <th>BU</th>
                        <th>Table / Column</th>
                        <th>Dimension</th>
                        <th>Status</th>
                        <th>Evaluated</th>
                        <th>Failed Records</th>
                        <th>DQ Score</th>
                        <th>Why</th>
                        <th>Recommended Action</th>
                    </tr>
                    </thead>
                    <tbody id="issueBody"></tbody>
                </table>
            </div>
        </div>
    </section>
"""


EXTRA_SCRIPT = r"""
    const CONTACTS = {
        lyan: {
            name: "Lyan Esmat",
            email: "EsmatL@maaden.com.sa"
        },
        moath: {
            name: "Moath AlSoqair",
            email: "AlsoqairM@maaden.com.sa"
        }
    };

    let issueRows = [];
    let insightRows = [];

    const firstValue = (row, keys, fallback = "") => {
        for (const key of keys) {
            const value = row?.[key];
            if (value !== null && value !== undefined && value !== "") {
                return value;
            }
        }
        return fallback;
    };

    function openContact(contactId) {
        const contact = CONTACTS[contactId];
        const popover = document.getElementById("contactPopover");

        document.getElementById("contactCardName").textContent =
            contact.name;
        document.getElementById("contactCardEmail").textContent =
            contact.email;
        document.getElementById("contactEmailButton").href =
            `mailto:${contact.email}`;
        document.getElementById("contactEmailButton").textContent =
            `Email ${contact.name}`;

        popover.classList.add("visible");
    }

    function closeContact() {
        document.getElementById(
            "contactPopover"
        ).classList.remove("visible");
    }

    function matchingInsight(row) {
        const bu = String(firstValue(
            row,
            ["business_unit", "technical_business_unit"]
        )).toUpperCase();
        const table = String(firstValue(
            row,
            ["table_name", "technical_table"]
        )).toLowerCase();
        const dimension = String(firstValue(
            row,
            ["dq_dimension", "dimension"]
        )).toLowerCase();

        return insightRows.find(insight =>
            String(insight.business_unit ?? "").toUpperCase() === bu
            && String(insight.dq_dimension ?? "").toLowerCase() === dimension
            && (
                !table
                || String(insight.table_name ?? "").toLowerCase() === table
                || String(insight.issue_title ?? "").toLowerCase()
                    .includes(table)
            )
        );
    }

    function defaultRecommendation(dimension, status) {
        if (status === "Not Executed") {
            return "Restore the missing source, column, reference data or rule input, then rerun the agent pipeline.";
        }

        const actions = {
            completeness: "Make the field mandatory at the source and prevent incomplete records from being submitted.",
            validity: "Correct invalid values and enforce the approved format or domain at data entry.",
            accuracy: "Reconcile the values with the approved reference source and correct mismatches.",
            consistency: "Align the source transformation and reference logic across systems.",
            uniqueness: "Review duplicates, retain the authoritative record and enforce a unique key.",
            timeliness: "Refresh stale records and schedule monitored source updates."
        };

        return actions[String(dimension).toLowerCase()]
            ?? "Review the failed records, correct the source process and rerun the rule.";
    }

    function renderRuleIssues() {
        const search = document.getElementById(
            "issueSearch"
        ).value.toLowerCase().trim();
        const selectedStatus = document.getElementById(
            "issueStatus"
        ).value;

        const rows = issueRows.filter(row => {
            const status = String(firstValue(
                row,
                ["execution_status", "status"]
            ));
            const statusMatch = selectedStatus === "all"
                ? ["Failed", "Not Executed"].includes(status)
                : status === selectedStatus;
            const haystack = [
                firstValue(row, ["bt_id"]),
                firstValue(row, ["business_term_name", "business_term"]),
                firstValue(row, ["business_unit", "technical_business_unit"]),
                firstValue(row, ["table_name", "technical_table"]),
                firstValue(row, ["column_name", "execution_column"]),
                firstValue(row, ["dq_dimension", "dimension"])
            ].join(" ").toLowerCase();

            return statusMatch && haystack.includes(search);
        });

        const failedCount = issueRows.filter(row =>
            String(firstValue(
                row,
                ["execution_status", "status"]
            )) === "Failed"
        ).length;
        const notExecutedCount = issueRows.filter(row =>
            String(firstValue(
                row,
                ["execution_status", "status"]
            )) === "Not Executed"
        ).length;

        document.getElementById("issueCount").textContent =
            `${failedCount} Failed · ${notExecutedCount} Not Executed`;

        if (!rows.length) {
            document.getElementById("issueBody").innerHTML = `
                <tr>
                    <td colspan="10" class="empty">
                        No rules match this filter.
                    </td>
                </tr>
            `;
            return;
        }

        document.getElementById("issueBody").innerHTML =
            rows.map(row => {
                const status = String(firstValue(
                    row,
                    ["execution_status", "status"],
                    "Unknown"
                ));
                const dimension = firstValue(
                    row,
                    ["dq_dimension", "dimension"]
                );
                const failedRecords = number(firstValue(
                    row,
                    [
                        "failed_records",
                        "failure_count",
                        "failed_record_checks"
                    ],
                    0
                ));
                const evaluated = number(firstValue(
                    row,
                    [
                        "evaluated_records",
                        "records_evaluated",
                        "evaluated_record_checks",
                        "total_records"
                    ],
                    0
                ));
                const scoreValue = firstValue(
                    row,
                    ["dq_score", "rule_score", "score"],
                    evaluated
                        ? 100 * (evaluated - failedRecords) / evaluated
                        : 0
                );
                const table = firstValue(
                    row,
                    ["table_name", "technical_table"]
                );
                const column = firstValue(
                    row,
                    ["column_name", "execution_column"]
                );
                const insight = matchingInsight(row);
                const explicitReason = firstValue(
                    row,
                    [
                        "execution_reason",
                        "failure_reason",
                        "status_reason",
                        "error_message",
                        "reason"
                    ]
                );
                const why = explicitReason || (
                    status === "Failed"
                        ? `The rule executed successfully, but ${formatNumber(failedRecords)} of ${formatNumber(evaluated)} evaluated records did not satisfy the ${String(dimension).toLowerCase()} requirement.`
                        : "The applicable rule could not execute because a required input was unavailable."
                );
                const recommendation =
                    insight?.recommendation
                    || defaultRecommendation(dimension, status);

                return `
                    <tr>
                        <td>
                            ${escapeHtml(firstValue(
                                row,
                                ["bt_id"]
                            ))}
                            ·
                            ${escapeHtml(firstValue(
                                row,
                                ["business_term_name", "business_term"]
                            ))}
                        </td>
                        <td>${escapeHtml(firstValue(
                            row,
                            ["business_unit", "technical_business_unit"]
                        ))}</td>
                        <td>
                            ${escapeHtml(table)}
                            /
                            ${escapeHtml(column)}
                        </td>
                        <td>${escapeHtml(dimension)}</td>
                        <td>${badge(status)}</td>
                        <td>${formatNumber(evaluated)}</td>
                        <td>${formatNumber(failedRecords)}</td>
                        <td class="score">${percent(scoreValue)}</td>
                        <td class="issue-reason">${escapeHtml(why)}</td>
                        <td class="issue-action">${escapeHtml(
                            recommendation
                        )}</td>
                    </tr>
                `;
            }).join("");
    }

    async function loadRuleIssues() {
        try {
            const [ruleResponse, insightResponse] = await Promise.all([
                fetch("/api/rule-results?page_size=200"),
                fetch("/api/insights?page_size=200")
            ]);

            if (!ruleResponse.ok || !insightResponse.ok) {
                throw new Error(
                    "Detailed rule results could not be loaded."
                );
            }

            const firstRulePage = await ruleResponse.json();
            const insightData = await insightResponse.json();
            issueRows = firstRulePage.results ?? [];
            insightRows = insightData.results ?? [];

            if (number(firstRulePage.total_pages) > 1) {
                const remaining = [];
                for (
                    let page = 2;
                    page <= number(firstRulePage.total_pages);
                    page += 1
                ) {
                    remaining.push(
                        fetch(
                            `/api/rule-results?page=${page}&page_size=200`
                        ).then(response => response.json())
                    );
                }

                const pages = await Promise.all(remaining);
                issueRows.push(
                    ...pages.flatMap(page => page.results ?? [])
                );
            }

            renderRuleIssues();
        } catch (error) {
            document.getElementById("issueCount").textContent =
                "Unable to load";
            document.getElementById("issueBody").innerHTML = `
                <tr>
                    <td colspan="10" class="empty">
                        ${escapeHtml(error.message)}
                    </td>
                </tr>
            `;
        }
    }

    document.querySelectorAll("[data-contact]").forEach(trigger => {
        trigger.addEventListener("click", event => {
            event.stopPropagation();
            openContact(trigger.dataset.contact);
        });
    });

    document.getElementById(
        "contactPopover"
    ).addEventListener("click", event => event.stopPropagation());

    document.addEventListener("click", closeContact);
    document.addEventListener("keydown", event => {
        if (event.key === "Escape") {
            closeContact();
        }
    });

    document.getElementById(
        "issueSearch"
    ).addEventListener("input", renderRuleIssues);

    document.getElementById(
        "issueStatus"
    ).addEventListener("change", renderRuleIssues);
"""


def build_dashboard():
    html = BASE_DASHBOARD_FILE.read_text(encoding="utf-8")

    old_team = """    <div class="team">
        <strong>Lyan Esmat &amp; Moath AlSoqair</strong>
        <div>Data &amp; AI Platform Governance</div>
    </div>"""

    html = html.replace(
        "</style>",
        f"{CONTACT_CSS}\n    </style>",
        1,
    )
    html = html.replace(old_team, CONTACT_HTML, 1)
    html = html.replace(
        """    <section class="panel">
        <div class="panel-header">
            <h2 class="panel-title">Consolidated Agent Insights</h2>""",
        f"""{ISSUE_PANEL_HTML}

    <section class="panel">
        <div class="panel-header">
            <h2 class="panel-title">Consolidated Agent Insights</h2>""",
        1,
    )
    html = html.replace(
        "    loadDashboard();\n</script>",
        (
            f"{EXTRA_SCRIPT}\n"
            "    loadDashboard();\n"
            "    loadRuleIssues();\n"
            "</script>"
        ),
        1,
    )
    html = html.replace(
        "            await loadDashboard();",
        "            await loadDashboard();\n            await loadRuleIssues();",
        1,
    )

    return html


app = FastAPI(
    title="Agentic Data Quality Excellence Portal",
    description=(
        "Enterprise portal with detailed DQ failures, "
        "recommendations and project contact cards."
    ),
    version="2.0.0",
)


if not STATIC_DIR.exists():
    raise RuntimeError(f"Static folder was not found: {STATIC_DIR}")


app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


for route in agent_api_app.routes:
    route_path = getattr(route, "path", "")
    if route_path.startswith("/api/"):
        app.router.routes.append(route)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def portal_home():
    if not BASE_DASHBOARD_FILE.exists():
        return HTMLResponse(
            "<h1>Base dashboard file is missing.</h1>",
            status_code=500,
        )

    return HTMLResponse(build_dashboard())


@app.get("/portal-status", include_in_schema=False)
def portal_status():
    return {
        "status": "ready",
        "version": "2.0.0",
        "base_dashboard_exists": BASE_DASHBOARD_FILE.exists(),
        "contacts_enabled": True,
        "rule_issue_panel_enabled": True,
        "api_routes_loaded": len(
            [
                route
                for route in app.routes
                if getattr(route, "path", "").startswith("/api/")
            ]
        ),
    }