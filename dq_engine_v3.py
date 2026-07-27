from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import dq_engine_v2 as dq_v2


BASE_DIR = Path(__file__).resolve().parent

OUTPUT_FILE = (
    BASE_DIR
    / "outputs"
    / "data_quality_results_v3.xlsx"
)

DIMENSIONS = [
    "Completeness",
    "Validity",
    "Accuracy",
    "Consistency",
    "Uniqueness",
    "Timeliness",
]

VALID_STATUSES = {
    "Passed",
    "Failed",
    "Not Executed",
}


def safe_average(series):
    numeric_values = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if numeric_values.empty:
        return 0.0

    return round(float(numeric_values.mean()), 2)


def calculate_coverage(executed, planned):
    if planned == 0:
        return 0.0

    return round((executed / planned) * 100, 2)


def calculate_adjusted_score(
    quality_score,
    coverage,
):
    return round(
        quality_score * (coverage / 100),
        2,
    )


def execute_all_checks(dataframe, columns):
    results = []

    for _, row in dataframe.iterrows():
        bt_id = dq_v2.get_value(
            row,
            columns,
            "bt_id",
        )

        business_term = dq_v2.get_value(
            row,
            columns,
            "business_term_name",
        )

        checks = [
            dq_v2.evaluate_completeness(
                row,
                columns,
                bt_id,
                business_term,
            ),
            dq_v2.evaluate_validity(
                row,
                columns,
                bt_id,
                business_term,
            ),
            dq_v2.evaluate_accuracy(
                row,
                columns,
                bt_id,
                business_term,
            ),
            dq_v2.evaluate_consistency(
                row,
                columns,
                bt_id,
                business_term,
            ),
            dq_v2.evaluate_uniqueness(
                row,
                columns,
                dataframe,
                bt_id,
                business_term,
            ),
            dq_v2.evaluate_timeliness(
                row,
                columns,
                bt_id,
                business_term,
            ),
        ]

        for check in checks:
            status = check.get("execution_status")

            if status not in VALID_STATUSES:
                raise ValueError(
                    "Invalid DQ execution status: "
                    f"{status}. Every check must be "
                    "Passed, Failed or Not Executed."
                )

            check["planned_check"] = 1

            check["executed_check"] = (
                1
                if status in {"Passed", "Failed"}
                else 0
            )

            results.append(check)

    return pd.DataFrame(results)


def build_summary(results, business_term_count):
    planned = len(results)

    passed = int(
        (
            results["execution_status"]
            == "Passed"
        ).sum()
    )

    failed = int(
        (
            results["execution_status"]
            == "Failed"
        ).sum()
    )

    not_executed = int(
        (
            results["execution_status"]
            == "Not Executed"
        ).sum()
    )

    executed = passed + failed

    if planned != executed + not_executed:
        raise ValueError(
            "DQ totals are inconsistent. Planned checks "
            "must equal executed plus not-executed checks."
        )

    executed_rows = results[
        results["execution_status"]
        .isin(["Passed", "Failed"])
    ]

    quality_score = safe_average(
        executed_rows["score"]
    )

    execution_coverage = calculate_coverage(
        executed,
        planned,
    )

    adjusted_score = calculate_adjusted_score(
        quality_score,
        execution_coverage,
    )

    return pd.DataFrame(
        [
            {
                "execution_time": datetime.now(
                    timezone.utc
                ).isoformat(),
                "business_terms_assessed": (
                    business_term_count
                ),
                "dq_dimensions_per_business_term": 6,
                "planned_dq_checks": planned,
                "executed_dq_checks": executed,
                "passed_dq_checks": passed,
                "failed_dq_checks": failed,
                "not_executed_dq_checks": not_executed,
                "execution_coverage": execution_coverage,
                "overall_dq_score": quality_score,
                "coverage_adjusted_score": adjusted_score,
            }
        ]
    )


def build_dimension_summary(results):
    rows = []

    for dimension in DIMENSIONS:
        group = results[
            results["dq_dimension"] == dimension
        ]

        planned = len(group)

        passed = int(
            (
                group["execution_status"]
                == "Passed"
            ).sum()
        )

        failed = int(
            (
                group["execution_status"]
                == "Failed"
            ).sum()
        )

        not_executed = int(
            (
                group["execution_status"]
                == "Not Executed"
            ).sum()
        )

        executed = passed + failed

        executed_rows = group[
            group["execution_status"]
            .isin(["Passed", "Failed"])
        ]

        quality_score = safe_average(
            executed_rows["score"]
        )

        coverage = calculate_coverage(
            executed,
            planned,
        )

        rows.append(
            {
                "dimension": dimension,
                "dq_score": quality_score,
                "execution_coverage": coverage,
                "planned_dq_checks": planned,
                "executed_dq_checks": executed,
                "passed": passed,
                "failed": failed,
                "not_executed": not_executed,
                "coverage_adjusted_score": (
                    calculate_adjusted_score(
                        quality_score,
                        coverage,
                    )
                ),
            }
        )

    return pd.DataFrame(rows)


def build_business_term_summary(results):
    rows = []

    grouped_results = results.groupby(
        ["bt_id", "business_term_name"],
        dropna=False,
    )

    for (bt_id, business_term), group in grouped_results:
        planned = len(group)

        passed = int(
            (
                group["execution_status"]
                == "Passed"
            ).sum()
        )

        failed = int(
            (
                group["execution_status"]
                == "Failed"
            ).sum()
        )

        not_executed = int(
            (
                group["execution_status"]
                == "Not Executed"
            ).sum()
        )

        executed = passed + failed

        executed_rows = group[
            group["execution_status"]
            .isin(["Passed", "Failed"])
        ]

        dq_score = safe_average(
            executed_rows["score"]
        )

        coverage = calculate_coverage(
            executed,
            planned,
        )

        rows.append(
            {
                "bt_id": bt_id,
                "business_term_name": business_term,
                "dq_score": dq_score,
                "execution_coverage": coverage,
                "planned_dq_checks": planned,
                "executed_dq_checks": executed,
                "passed": passed,
                "failed": failed,
                "not_executed": not_executed,
                "coverage_adjusted_score": (
                    calculate_adjusted_score(
                        dq_score,
                        coverage,
                    )
                ),
            }
        )

    summary = pd.DataFrame(rows)

    return summary.sort_values(
        by=[
            "dq_score",
            "execution_coverage",
            "business_term_name",
        ],
        ascending=[True, True, True],
    )


def build_column_summary(results):
    rows = []

    for target_column, group in results.groupby(
        "target_column",
        dropna=False,
    ):
        planned = len(group)

        passed = int(
            (
                group["execution_status"]
                == "Passed"
            ).sum()
        )

        failed = int(
            (
                group["execution_status"]
                == "Failed"
            ).sum()
        )

        not_executed = int(
            (
                group["execution_status"]
                == "Not Executed"
            ).sum()
        )

        executed = passed + failed

        executed_rows = group[
            group["execution_status"]
            .isin(["Passed", "Failed"])
        ]

        dq_score = safe_average(
            executed_rows["score"]
        )

        coverage = calculate_coverage(
            executed,
            planned,
        )

        rows.append(
            {
                "target_column": target_column,
                "dq_score": dq_score,
                "execution_coverage": coverage,
                "planned_dq_checks": planned,
                "executed_dq_checks": executed,
                "passed": passed,
                "failed": failed,
                "not_executed": not_executed,
            }
        )

    return pd.DataFrame(rows)


def build_execution_summary(results):
    rows = []

    for status in [
        "Passed",
        "Failed",
        "Not Executed",
    ]:
        count = int(
            (
                results["execution_status"]
                == status
            ).sum()
        )

        rows.append(
            {
                "execution_status": status,
                "dq_check_count": count,
                "definition": {
                    "Passed": (
                        "The DQ check ran and the data "
                        "satisfied the rule."
                    ),
                    "Failed": (
                        "The DQ check ran, but the data "
                        "violated the rule."
                    ),
                    "Not Executed": (
                        "The DQ check could not run because "
                        "a required input was unavailable."
                    ),
                }[status],
            }
        )

    return pd.DataFrame(rows)


def run_data_quality_v3():
    dataframe = dq_v2.load_mapping_data()

    columns = {
        name: dq_v2.find_column(
            dataframe,
            name,
        )
        for name in dq_v2.COLUMN_ALIASES
    }

    required_columns = [
        "bt_id",
        "business_term_name",
    ]

    missing_columns = [
        column
        for column in required_columns
        if columns.get(column) is None
    ]

    if missing_columns:
        raise ValueError(
            "Required mapping columns were not found: "
            + ", ".join(missing_columns)
        )

    results = execute_all_checks(
        dataframe,
        columns,
    )

    expected_check_count = len(dataframe) * 6

    if len(results) != expected_check_count:
        raise ValueError(
            "Incorrect number of planned checks. "
            f"Expected {expected_check_count}, "
            f"received {len(results)}."
        )

    summary = build_summary(
        results,
        len(dataframe),
    )

    dimension_summary = build_dimension_summary(
        results
    )

    business_term_summary = (
        build_business_term_summary(results)
    )

    column_summary = build_column_summary(results)

    execution_summary = build_execution_summary(
        results
    )

    issues = results[
        results["execution_status"]
        .isin(["Failed", "Not Executed"])
    ].copy()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
    ) as writer:
        summary.to_excel(
            writer,
            sheet_name="Summary",
            index=False,
        )

        execution_summary.to_excel(
            writer,
            sheet_name="Execution Summary",
            index=False,
        )

        dimension_summary.to_excel(
            writer,
            sheet_name="Dimension Scores",
            index=False,
        )

        business_term_summary.to_excel(
            writer,
            sheet_name="BT Scores",
            index=False,
        )

        column_summary.to_excel(
            writer,
            sheet_name="Column Scores",
            index=False,
        )

        results.to_excel(
            writer,
            sheet_name="All DQ Checks",
            index=False,
        )

        issues.to_excel(
            writer,
            sheet_name="DQ Issues",
            index=False,
        )

    summary_row = summary.iloc[0]

    print()
    print("Data Quality V3 execution completed.")
    print(
        "Business Terms assessed: "
        f"{summary_row['business_terms_assessed']}"
    )
    print(
        "Planned DQ checks: "
        f"{summary_row['planned_dq_checks']}"
    )
    print(
        "Executed DQ checks: "
        f"{summary_row['executed_dq_checks']}"
    )
    print(
        "Passed DQ checks: "
        f"{summary_row['passed_dq_checks']}"
    )
    print(
        "Failed DQ checks: "
        f"{summary_row['failed_dq_checks']}"
    )
    print(
        "Not-executed DQ checks: "
        f"{summary_row['not_executed_dq_checks']}"
    )
    print(
        "Execution coverage: "
        f"{summary_row['execution_coverage']}%"
    )
    print(
        "Overall DQ score: "
        f"{summary_row['overall_dq_score']}%"
    )
    print(f"Saved to: {OUTPUT_FILE}")
    print()

    return {
        "summary": summary.iloc[0].to_dict(),
        "execution_summary": (
            execution_summary.to_dict(
                orient="records"
            )
        ),
        "dimension_scores": (
            dimension_summary.to_dict(
                orient="records"
            )
        ),
        "business_term_scores": (
            business_term_summary.to_dict(
                orient="records"
            )
        ),
        "column_scores": (
            column_summary.to_dict(
                orient="records"
            )
        ),
        "dq_checks": results.to_dict(
            orient="records"
        ),
        "issues": issues.to_dict(
            orient="records"
        ),
    }


if __name__ == "__main__":
    run_data_quality_v3()