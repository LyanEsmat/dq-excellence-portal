from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

RESULT_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_execution_results.xlsx"
)

FAILURE_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_failed_records.csv"
)


def check(
    condition: bool,
    message: str,
):
    if not condition:
        raise AssertionError(message)

    print(f"PASSED: {message}")


def run_tests():
    print()
    print("Batch DQ Executor V3 Tests")
    print("=" * 55)

    check(
        RESULT_FILE.exists(),
        "DQ execution workbook exists",
    )

    check(
        FAILURE_FILE.exists(),
        "Failed-record CSV exists",
    )

    summary = pd.read_excel(
        RESULT_FILE,
        sheet_name="Summary",
    ).iloc[0]

    rule_results = pd.read_excel(
        RESULT_FILE,
        sheet_name="Rule Results",
    )

    failures = pd.read_csv(
        FAILURE_FILE,
    )

    check(
        summary["data_source_type"]
        == "excel",
        "Execution used the Excel adapter",
    )

    check(
        int(summary["source_assets"]) == 7,
        "Seven source assets loaded",
    )

    check(
        int(summary["source_records"])
        == 56_000,
        "56,000 source records assessed",
    )

    check(
        int(summary["planned_assessments"])
        == 378,
        "378 DQ assessments planned",
    )

    check(
        len(rule_results) == 378,
        "378 rule-result rows produced",
    )

    check(
        int(summary["applicable_rules"])
        == 259,
        "259 applicable rules identified",
    )

    check(
        int(summary["executed_rules"])
        == 259,
        "All 259 applicable rules executed",
    )

    check(
        int(summary["not_executed_rules"])
        == 0,
        "No applicable rules were skipped",
    )

    check(
        int(
            summary[
                "not_applicable_assessments"
            ]
        )
        == 119,
        "119 assessments correctly marked Not Applicable",
    )

    check(
        float(summary["execution_coverage"])
        == 100.0,
        "Execution coverage is 100%",
    )

    check(
        int(summary["evaluated_record_checks"])
        == 2_067_065,
        "2,067,065 record checks evaluated",
    )

    check(
        int(summary["failed_record_checks"])
        == 36_016,
        "36,016 failed record checks detected",
    )

    check(
        len(failures) == 36_016,
        "Failure CSV matches the summary",
    )

    check(
        float(summary["overall_dq_score"])
        == 98.26,
        "Overall DQ score remains 98.26%",
    )

    applicable_results = (
        rule_results[
            rule_results["applicability"]
            == "Applicable"
        ]
    )

    check(
        applicable_results[
            "execution_status"
        ]
        .isin(
            ["Passed", "Failed"]
        )
        .all(),
        "Every applicable rule has a completed result",
    )

    check(
        rule_results["dq_score"]
        .dropna()
        .between(0, 100)
        .all(),
        "All calculated DQ scores are valid percentages",
    )

    print("=" * 55)
    print(
        "ALL BATCH DQ EXECUTOR V3 TESTS PASSED"
    )
    print()


if __name__ == "__main__":
    run_tests()