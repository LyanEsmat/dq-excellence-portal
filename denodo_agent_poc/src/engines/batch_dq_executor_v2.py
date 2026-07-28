from datetime import datetime, timezone

import pandas as pd

import batch_dq_executor as dq


def run_batch_dq_execution_v2():
    if not dq.RULE_FILE.exists():
        raise FileNotFoundError(
            f"DQ rule registry not found: "
            f"{dq.RULE_FILE}"
        )

    registry = pd.read_excel(
        dq.RULE_FILE,
        sheet_name="Rule Registry",
    )

    source_cache = {}
    result_rows = []
    failed_rows = []

    print()
    print("Starting corrected batch DQ execution...")

    for rule_number, (_, rule) in enumerate(
        registry.iterrows(),
        start=1,
    ):
        schema_name = str(
            rule["schema_name"]
        ).lower()

        if schema_name not in source_cache:
            source_file = dq.locate_source_file(
                schema_name
            )

            source_cache[schema_name] = (
                pd.read_excel(source_file)
            )

            print(
                f"Loaded {schema_name.upper()}: "
                f"{len(source_cache[schema_name]):,} "
                "records"
            )

        dataframe = source_cache[schema_name]

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
                    total_records=len(dataframe),
                    evaluated_records=0,
                    passed_records=0,
                    failed_records=0,
                    score=None,
                    reason=(
                        f"Execution error: {error}"
                    ),
                )
            )

        if rule_number % 50 == 0:
            print(
                f"Processed {rule_number}/"
                f"{len(registry)} assessments"
            )

    results = pd.DataFrame(result_rows)

    failure_columns = [
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

    failures = pd.DataFrame(
        failed_rows,
        columns=failure_columns,
    )

    executed_mask = results[
        "execution_status"
    ].isin(
        ["Passed", "Failed"]
    )

    executed_rules = results[executed_mask]

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

    total_evaluated_records = int(
        executed_rules[
            "evaluated_records"
        ].sum()
    )

    total_passed_records = int(
        executed_rules[
            "passed_records"
        ].sum()
    )

    total_failed_records = int(
        executed_rules[
            "failed_records"
        ].sum()
    )

    if total_evaluated_records == 0:
        overall_dq_score = 0.0
    else:
        overall_dq_score = round(
            (
                total_passed_records
                / total_evaluated_records
            )
            * 100,
            2,
        )

    execution_coverage = round(
        (
            len(executed_rules)
            / int(
                (
                    results["applicability"]
                    == "Applicable"
                ).sum()
            )
        )
        * 100,
        2,
    )

    summary = pd.DataFrame(
        [
            {
                "execution_time": datetime.now(
                    timezone.utc
                ).isoformat(),
                "source_files": len(source_cache),
                "source_records": sum(
                    len(dataframe)
                    for dataframe
                    in source_cache.values()
                ),
                "planned_assessments": len(
                    results
                ),
                "applicable_rules": int(
                    (
                        results["applicability"]
                        == "Applicable"
                    ).sum()
                ),
                "executed_rules": len(
                    executed_rules
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
                    total_evaluated_records
                ),
                "passed_record_checks": (
                    total_passed_records
                ),
                "failed_record_checks": (
                    total_failed_records
                ),
                "overall_dq_score": (
                    overall_dq_score
                ),
                "failure_detail_rows": len(
                    failures
                ),
            }
        ]
    )

    dimension_summary = dq.aggregate_results(
        results,
        ["dq_dimension"],
    )

    bt_summary = dq.aggregate_results(
        results,
        [
            "bt_id",
            "business_term_name",
        ],
    )

    column_summary = dq.aggregate_results(
        results,
        [
            "business_unit",
            "table_name",
            "column_name",
        ],
    )

    business_unit_summary = dq.aggregate_results(
        results,
        ["business_unit"],
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

        results[
            results["execution_status"]
            == "Not Applicable"
        ].to_excel(
            writer,
            sheet_name="Not Applicable",
            index=False,
        )

        results[
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

    result = summary.iloc[0]

    print()
    print("Corrected Batch DQ execution completed.")
    print(
        f"Source files: "
        f"{int(result['source_files'])}"
    )
    print(
        f"Source records: "
        f"{int(result['source_records']):,}"
    )
    print(
        f"Planned assessments: "
        f"{int(result['planned_assessments'])}"
    )
    print(
        f"Applicable rules: "
        f"{int(result['applicable_rules'])}"
    )
    print(
        f"Executed rules: "
        f"{int(result['executed_rules'])}"
    )
    print(
        f"Passed rules: "
        f"{int(result['passed_rules'])}"
    )
    print(
        f"Failed rules: "
        f"{int(result['failed_rules'])}"
    )
    print(
        f"Not Executed: "
        f"{int(result['not_executed_rules'])}"
    )
    print(
        f"Not Applicable: "
        f"{int(result['not_applicable_assessments'])}"
    )
    print(
        f"Execution coverage: "
        f"{result['execution_coverage']}%"
    )
    print(
        f"Evaluated record checks: "
        f"{int(result['evaluated_record_checks']):,}"
    )
    print(
        f"Failed record checks: "
        f"{int(result['failed_record_checks']):,}"
    )
    print(
        f"Overall DQ score: "
        f"{result['overall_dq_score']}%"
    )
    print(
        f"Failure detail rows: "
        f"{int(result['failure_detail_rows']):,}"
    )
    print(f"Saved: {dq.RESULT_FILE}")
    print(f"Saved: {dq.FULL_FAILURE_FILE}")
    print()


if __name__ == "__main__":
    run_batch_dq_execution_v2()