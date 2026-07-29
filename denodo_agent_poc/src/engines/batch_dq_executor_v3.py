from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd


SOURCE_CODE_DIR = Path(__file__).resolve().parents[1]

if str(SOURCE_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_CODE_DIR))


from data_sources import (  # noqa: E402
    BaseDataSource,
    ExcelDataSource,
)

import batch_dq_executor as dq  # noqa: E402


FAILURE_COLUMNS = [
    "rule_id",
    "bt_id",
    "business_term_name",
    "business_unit",
    "table_name",
    "target_column",
    "execution_column",
    "dq_dimension",
    "rule_type",
    "source_row",
    "record_identifier",
    "failed_value",
    "failure_reason",
]


def create_source_error_result(
    rule: pd.Series,
    reason: str,
) -> dict:
    return dq.create_assessment_result(
        rule=rule,
        status="Not Executed",
        total_records=0,
        evaluated_records=0,
        passed_records=0,
        failed_records=0,
        score=None,
        reason=reason,
    )


def load_rule_asset(
    rule: pd.Series,
    data_source: BaseDataSource,
    source_cache: dict,
):
    business_unit = str(
        rule["business_unit"]
    ).strip().upper()

    table_name = str(
        rule["table_name"]
    ).strip().lower()

    cache_key = (
        business_unit,
        table_name,
    )

    if cache_key in source_cache:
        return source_cache[cache_key]

    asset = data_source.find_asset(
        business_unit=business_unit,
        table_name=table_name,
    )

    dataframe = data_source.read_asset(asset)

    source_cache[cache_key] = dataframe

    print(
        f"Loaded {business_unit}: "
        f"{len(dataframe):,} records "
        f"from {table_name}"
    )

    return dataframe


def calculate_summary(
    results: pd.DataFrame,
    failures: pd.DataFrame,
    source_cache: dict,
    data_source: BaseDataSource,
) -> pd.DataFrame:
    executed_mask = results[
        "execution_status"
    ].isin(
        ["Passed", "Failed"]
    )

    executed_rules = results.loc[
        executed_mask
    ]

    applicable_count = int(
        (
            results["applicability"]
            == "Applicable"
        ).sum()
    )

    executed_count = len(executed_rules)

    passed_rules = int(
        (
            results["execution_status"]
            == "Passed"
        ).sum()
    )

    failed_rules = int(
        (
            results["execution_status"]
            == "Failed"
        ).sum()
    )

    not_executed_rules = int(
        (
            results["execution_status"]
            == "Not Executed"
        ).sum()
    )

    not_applicable = int(
        (
            results["execution_status"]
            == "Not Applicable"
        ).sum()
    )

    total_evaluated = int(
        executed_rules[
            "evaluated_records"
        ].sum()
    )

    total_passed = int(
        executed_rules[
            "passed_records"
        ].sum()
    )

    total_failed = int(
        executed_rules[
            "failed_records"
        ].sum()
    )

    if total_evaluated:
        overall_score = round(
            (
                total_passed
                / total_evaluated
            )
            * 100,
            2,
        )
    else:
        overall_score = 0.0

    if applicable_count:
        execution_coverage = round(
            (
                executed_count
                / applicable_count
            )
            * 100,
            2,
        )
    else:
        execution_coverage = 0.0

    source_record_count = sum(
        len(dataframe)
        for dataframe
        in source_cache.values()
    )

    return pd.DataFrame(
        [
            {
                "execution_time": datetime.now(
                    timezone.utc
                ).isoformat(),
                "data_source_type": (
                    data_source.source_type
                ),
                "source_assets": len(
                    source_cache
                ),
                "source_files": len(
                    source_cache
                ),
                "source_records": (
                    source_record_count
                ),
                "planned_assessments": len(
                    results
                ),
                "applicable_rules": (
                    applicable_count
                ),
                "executed_rules": (
                    executed_count
                ),
                "passed_rules": passed_rules,
                "failed_rules": failed_rules,
                "not_executed_rules": (
                    not_executed_rules
                ),
                "not_applicable_assessments": (
                    not_applicable
                ),
                "execution_coverage": (
                    execution_coverage
                ),
                "evaluated_record_checks": (
                    total_evaluated
                ),
                "passed_record_checks": (
                    total_passed
                ),
                "failed_record_checks": (
                    total_failed
                ),
                "overall_dq_score": (
                    overall_score
                ),
                "failure_detail_rows": len(
                    failures
                ),
            }
        ]
    )


def write_execution_results(
    summary: pd.DataFrame,
    results: pd.DataFrame,
    failures: pd.DataFrame,
):
    dimension_summary = (
        dq.aggregate_results(
            results,
            ["dq_dimension"],
        )
    )

    bt_summary = dq.aggregate_results(
        results,
        [
            "bt_id",
            "business_term_name",
        ],
    )

    column_summary = (
        dq.aggregate_results(
            results,
            [
                "business_unit",
                "table_name",
                "column_name",
            ],
        )
    )

    business_unit_summary = (
        dq.aggregate_results(
            results,
            ["business_unit"],
        )
    )

    with pd.ExcelWriter(
        dq.RESULT_FILE,
        engine="openpyxl",
    ) as writer:
        summary.to_excel(
            writer,
            sheet_name="Summary",
            index=False,
        )

        dimension_summary.to_excel(
            writer,
            sheet_name="Dimension Scores",
            index=False,
        )

        bt_summary.to_excel(
            writer,
            sheet_name="BT Scores",
            index=False,
        )

        column_summary.to_excel(
            writer,
            sheet_name="Column Scores",
            index=False,
        )

        business_unit_summary.to_excel(
            writer,
            sheet_name="BU Scores",
            index=False,
        )

        results.to_excel(
            writer,
            sheet_name="Rule Results",
            index=False,
        )

        results.loc[
            results["execution_status"]
            == "Not Applicable"
        ].to_excel(
            writer,
            sheet_name="Not Applicable",
            index=False,
        )

        results.loc[
            results["execution_status"]
            == "Not Executed"
        ].to_excel(
            writer,
            sheet_name="Not Executed",
            index=False,
        )

        failures.head(
            dq.EXCEL_FAILURE_SAMPLE_LIMIT
        ).to_excel(
            writer,
            sheet_name="Failure Samples",
            index=False,
        )

    failures.to_csv(
        dq.FULL_FAILURE_FILE,
        index=False,
    )


def print_summary(
    summary: pd.DataFrame,
):
    result = summary.iloc[0]

    print()
    print(
        "Data-source-independent "
        "DQ execution completed."
    )
    print(
        "Data source: "
        f"{result['data_source_type']}"
    )
    print(
        "Source assets: "
        f"{int(result['source_assets'])}"
    )
    print(
        "Source records: "
        f"{int(result['source_records']):,}"
    )
    print(
        "Planned assessments: "
        f"{int(result['planned_assessments'])}"
    )
    print(
        "Applicable rules: "
        f"{int(result['applicable_rules'])}"
    )
    print(
        "Executed rules: "
        f"{int(result['executed_rules'])}"
    )
    print(
        "Passed rules: "
        f"{int(result['passed_rules'])}"
    )
    print(
        "Failed rules: "
        f"{int(result['failed_rules'])}"
    )
    print(
        "Not Executed: "
        f"{int(result['not_executed_rules'])}"
    )
    print(
        "Not Applicable: "
        f"{int(result['not_applicable_assessments'])}"
    )
    print(
        "Execution coverage: "
        f"{result['execution_coverage']}%"
    )
    print(
        "Evaluated record checks: "
        f"{int(result['evaluated_record_checks']):,}"
    )
    print(
        "Failed record checks: "
        f"{int(result['failed_record_checks']):,}"
    )
    print(
        "Overall DQ score: "
        f"{result['overall_dq_score']}%"
    )
    print(
        "Failure detail rows: "
        f"{int(result['failure_detail_rows']):,}"
    )
    print(f"Saved: {dq.RESULT_FILE}")
    print(f"Saved: {dq.FULL_FAILURE_FILE}")
    print()


def run_batch_dq_execution_v3(
    data_source: BaseDataSource | None = None,
):
    if data_source is None:
        data_source = ExcelDataSource()

    if not dq.RULE_FILE.exists():
        raise FileNotFoundError(
            "DQ rule registry not found: "
            f"{dq.RULE_FILE}"
        )

    health = data_source.health_check()

    if health["status"] != "healthy":
        problems = health.get(
            "problems",
            [],
        )

        raise RuntimeError(
            "Data source health check failed: "
            + "; ".join(problems)
        )

    registry = pd.read_excel(
        dq.RULE_FILE,
        sheet_name="Rule Registry",
    )

    source_cache = {}
    source_errors = {}
    result_rows = []
    failed_rows = []

    print()
    print(
        "Starting data-source-independent "
        "DQ execution..."
    )
    print(
        f"Data source: "
        f"{data_source.source_type}"
    )

    for rule_number, (_, rule) in enumerate(
        registry.iterrows(),
        start=1,
    ):
        business_unit = str(
            rule["business_unit"]
        ).strip().upper()

        table_name = str(
            rule["table_name"]
        ).strip().lower()

        cache_key = (
            business_unit,
            table_name,
        )

        if cache_key in source_errors:
            result_rows.append(
                create_source_error_result(
                    rule,
                    source_errors[cache_key],
                )
            )
            continue

        try:
            dataframe = load_rule_asset(
                rule=rule,
                data_source=data_source,
                source_cache=source_cache,
            )
        except Exception as error:
            reason = (
                "Source loading error for "
                f"{business_unit}.{table_name}: "
                f"{error}"
            )

            source_errors[cache_key] = reason

            result_rows.append(
                create_source_error_result(
                    rule,
                    reason,
                )
            )
            continue

        try:
            (
                result,
                failure_mask,
                execution_column,
            ) = dq.execute_rule(
                rule,
                dataframe,
            )

            result_rows.append(result)

            if (
                result["execution_status"]
                == "Failed"
            ):
                failed_rows.extend(
                    dq.collect_failures(
                        rule,
                        dataframe,
                        failure_mask,
                        execution_column,
                    )
                )

        except Exception as error:
            result_rows.append(
                dq.create_assessment_result(
                    rule=rule,
                    status="Not Executed",
                    total_records=len(
                        dataframe
                    ),
                    evaluated_records=0,
                    passed_records=0,
                    failed_records=0,
                    score=None,
                    reason=(
                        "Execution error: "
                        f"{error}"
                    ),
                )
            )

        if rule_number % 50 == 0:
            print(
                f"Processed {rule_number}/"
                f"{len(registry)} assessments"
            )

    results = pd.DataFrame(
        result_rows
    )

    failures = pd.DataFrame(
        failed_rows,
        columns=FAILURE_COLUMNS,
    )

    summary = calculate_summary(
        results=results,
        failures=failures,
        source_cache=source_cache,
        data_source=data_source,
    )

    write_execution_results(
        summary=summary,
        results=results,
        failures=failures,
    )

    print_summary(summary)

    return {
        "summary": summary,
        "rule_results": results,
        "failures": failures,
    }


if __name__ == "__main__":
    run_batch_dq_execution_v3()