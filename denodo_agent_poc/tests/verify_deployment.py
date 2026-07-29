import json
import sys
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8000"


def request_json(
    path: str,
) -> dict:
    url = f"{BASE_URL}{path}"

    try:
        with urllib.request.urlopen(
            url,
            timeout=15,
        ) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"{path} returned HTTP "
                    f"{response.status}."
                )

            return json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Unable to access {url}: "
            f"{error}"
        ) from error


def check(
    condition: bool,
    message: str,
):
    if not condition:
        raise AssertionError(message)

    print(f"PASSED: {message}")


def verify_portal_status():
    status = request_json(
        "/portal-status"
    )

    check(
        status["status"] == "ready",
        "Portal status is ready",
    )

    check(
        status["portal_version"]
        == "4.0.0",
        "Portal version is 4.0.0",
    )

    check(
        status["api_version"]
        == "3.0.0",
        "API version is 3.0.0",
    )

    check(
        status["pipeline_version"]
        == "3.0.0",
        "Pipeline version is 3.0.0",
    )

    check(
        status["data_source"]
        == "excel",
        "Excel data source is selected",
    )

    check(
        status["schedule_time"]
        == "06:00",
        "Schedule time is 06:00",
    )

    check(
        status["timezone"]
        == "Asia/Riyadh",
        "Schedule timezone is Asia/Riyadh",
    )

    check(
        status["schedule_enabled"]
        is False,
        "Scheduler is safely disabled",
    )

    check(
        status["contacts_enabled"]
        is True,
        "Contact popovers are enabled",
    )

    check(
        status["rule_issue_panel_enabled"]
        is True,
        "DQ issue panel is enabled",
    )


def verify_api_health():
    health = request_json(
        "/api/health"
    )

    check(
        health["status"] == "healthy",
        "Agent API health is healthy",
    )

    check(
        all(
            health["files"].values()
        ),
        "All required result files exist",
    )


def verify_dashboard():
    dashboard = request_json(
        "/api/dashboard"
    )

    summary = dashboard[
        "execution_summary"
    ]

    check(
        int(summary["source_records"])
        == 56_000,
        "Dashboard reports 56,000 records",
    )

    check(
        int(summary["planned_assessments"])
        == 378,
        "Dashboard reports 378 assessments",
    )

    check(
        int(summary["executed_rules"])
        == 259,
        "Dashboard reports 259 executed rules",
    )

    check(
        int(
            summary[
                "not_applicable_assessments"
            ]
        )
        == 119,
        "Dashboard reports 119 Not Applicable assessments",
    )

    check(
        float(summary["execution_coverage"])
        == 100.0,
        "Dashboard reports 100% execution coverage",
    )

    check(
        float(summary["overall_dq_score"])
        == 98.26,
        "Dashboard reports 98.26% DQ score",
    )

    check(
        len(
            dashboard[
                "business_unit_scores"
            ]
        )
        == 7,
        "Dashboard contains seven Business Units",
    )

    check(
        len(
            dashboard[
                "dimension_scores"
            ]
        )
        == 6,
        "Dashboard contains six DQ dimensions",
    )

    check(
        len(
            dashboard[
                "business_term_scores"
            ]
        )
        == 45,
        "Dashboard contains 45 Business Terms",
    )


def run_verification():
    print()
    print("Docker Deployment Verification")
    print("=" * 60)

    verify_portal_status()
    verify_api_health()
    verify_dashboard()

    print("=" * 60)
    print(
        "ALL DEPLOYMENT CHECKS PASSED"
    )
    print()


if __name__ == "__main__":
    try:
        run_verification()
    except Exception as error:
        print()
        print(
            "DEPLOYMENT VERIFICATION FAILED"
        )
        print(str(error))
        print()

        sys.exit(1)