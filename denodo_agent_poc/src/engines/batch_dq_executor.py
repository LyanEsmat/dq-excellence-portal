from pathlib import Path
from datetime import datetime, timezone
import json
import re

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[2]

SOURCE_DIR = PROJECT_DIR / "data" / "source"

RULE_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_rule_registry.xlsx"
)

RESULT_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_execution_results.xlsx"
)

FULL_FAILURE_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_failed_records.csv"
)

EXCEL_FAILURE_SAMPLE_LIMIT = 20000


def parse_parameters(value):
    if pd.isna(value):
        return {}

    text = str(value).strip()

    if not text:
        return {}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def missing_mask(series):
    return (
        series.isna()
        | (
            series
            .fillna("")
            .astype(str)
            .str.strip()
            == ""
        )
    )


def non_missing_mask(series):
    return ~missing_mask(series)


def locate_source_file(schema_name):
    file_path = (
        SOURCE_DIR
        / f"{str(schema_name).lower()}_source.xlsx"
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Source file not found: {file_path}"
        )

    return file_path


def find_identifier_column(dataframe):
    identifier_columns = [
        column
        for column in dataframe.columns
        if str(column).lower().endswith("_id")
    ]

    if identifier_columns:
        return identifier_columns[0]

    return dataframe.columns[0]


def execute_not_null(series, parameters):
    evaluated = pd.Series(
        True,
        index=series.index,
    )

    failures = missing_mask(series)

    return evaluated, failures


def execute_email_format(series, parameters):
    evaluated = non_missing_mask(series)

    pattern = parameters.get(
        "pattern",
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )

    valid = (
        series
        .fillna("")
        .astype(str)
        .str.match(pattern, na=False)
    )

    failures = evaluated & ~valid

    return evaluated, failures


def execute_numeric_minimum(series, parameters):
    evaluated = non_missing_mask(series)
    numeric_values = pd.to_numeric(
        series,
        errors="coerce",
    )

    minimum = float(
        parameters.get("minimum", 0)
    )

    valid = (
        numeric_values.notna()
        & (numeric_values >= minimum)
    )

    failures = evaluated & ~valid

    return evaluated, failures


def execute_identifier_format(series, parameters):
    evaluated = non_missing_mask(series)

    pattern = parameters.get(
        "pattern",
        r"^[A-Z]+-[0-9]{7}$",
    )

    valid = (
        series
        .fillna("")
        .astype(str)
        .str.match(pattern, na=False)
    )

    failures = evaluated & ~valid

    return evaluated, failures


def execute_valid_date(series, parameters):
    evaluated = non_missing_mask(series)

    parsed = pd.to_datetime(
        series,
        errors="coerce",
        utc=True,
    )

    failures = evaluated & parsed.isna()

    return evaluated, failures


def execute_allowed_values(series, parameters):
    evaluated = non_missing_mask(series)

    allowed_values = {
        str(value)
        for value in parameters.get(
            "allowed_values",
            [],
        )
    }

    valid = (
        series
        .fillna("")
        .astype(str)
        .isin(allowed_values)
    )

    failures = evaluated & ~valid

    return evaluated, failures


def execute_non_blank_text(series, parameters):
    evaluated = non_missing_mask(series)

    valid = (
        series
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
    )

    failures = evaluated & ~valid

    return evaluated, failures


def execute_reference_match(series, parameters):
    evaluated = non_missing_mask(series)

    approved_values = {
        str(value)
        for value in parameters.get(
            "approved_values",
            [],
        )
    }

    valid = (
        series
        .fillna("")
        .astype(str)
        .isin(approved_values)
    )

    failures = evaluated & ~valid

    return evaluated, failures


def execute_corporate_domain(series, parameters):
    evaluated = non_missing_mask(series)

    domain = str(
        parameters.get(
            "accepted_domain",
            "dummy-company.com",
        )
    ).lower()

    valid = (
        series
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .str.endswith(f"@{domain}")
    )

    failures = evaluated & ~valid

    return evaluated, failures


def execute_normalized_format(series, parameters):
    evaluated = non_missing_mask(series)

    values = (
        series
        .fillna("")
        .astype(str)
    )

    trimmed = values.str.strip()

    expected_case = parameters.get(
        "expected_case",
        "upper",
    )

    if expected_case == "lower":
        expected = trimmed.str.lower()
    else:
        expected = trimmed.str.upper()

    valid = values == expected
    failures = evaluated & ~valid

    return evaluated, failures


def execute_unique_value(series, parameters):
    evaluated = non_missing_mask(series)

    duplicate = series.duplicated(
        keep=False
    )

    failures = evaluated & duplicate

    return evaluated, failures


def execute_maximum_age(series, parameters):
    evaluated = pd.Series(
        True,
        index=series.index,
    )

    maximum_age_days = int(
        parameters.get(
            "maximum_age_days",
            365,
        )
    )

    parsed = pd.to_datetime(
        series,
        errors="coerce",
        utc=True,
    )

    current_time = pd.Timestamp.now(tz="UTC")
    age_days = (
        current_time - parsed
    ).dt.days

    valid = (
        parsed.notna()
        & age_days.ge(0)
        & age_days.le(maximum_age_days)
    )

    failures = evaluated & ~valid

    return evaluated, failures


RULE_EXECUTORS = {
    "not_null": execute_not_null,
    "email_format": execute_email_format,
    "numeric_minimum": execute_numeric_minimum,
    "identifier_format": execute_identifier_format,
    "valid_date": execute_valid_date,
    "allowed_values": execute_allowed_values,
    "non_blank_text": execute_non_blank_text,
    "reference_match": execute_reference_match,
    "corporate_email_domain": (
        execute_corporate_domain
    ),
    "normalized_format": (
        execute_normalized_format
    ),
    "unique_value": execute_unique_value,
    "maximum_age_days": execute_maximum_age,
}


def failure_reason(rule):
    reasons = {
        "not_null": "Required value is missing.",
        "email_format": "Email format is invalid.",
        "numeric_minimum": (
            "Numeric value is below the minimum."
        ),
        "identifier_format": (
            "Identifier format is invalid."
        ),
        "valid_date": (
            "Value cannot be interpreted as a date."
        ),
        "allowed_values": (
            "Value is outside the approved list."
        ),
        "non_blank_text": (
            "Text value is empty or unusable."
        ),
        "reference_match": (
            "Value does not match approved "
            "reference data."
        ),
        "corporate_email_domain": (
            "Email does not use the approved domain."
        ),
        "normalized_format": (
            "Value has inconsistent casing "
            "or whitespace."
        ),
        "unique_value": (
            "Identifier occurs more than once."
        ),
        "maximum_age_days": (
            "Record is stale or has no valid "
            "update timestamp."
        ),
    }

    return reasons.get(
        rule["rule_type"],
        "The record violated the DQ rule.",
    )


def create_assessment_result(
    rule,
    status,
    total_records,
    evaluated_records,
    passed_records,
    failed_records,
    score,
    reason,
):
    return {
        "execution_time": datetime.now(
            timezone.utc
        ).isoformat(),
        "rule_id": rule["rule_id"],
        "agent_mapping_id": rule[
            "agent_mapping_id"
        ],
        "bt_id": rule["bt_id"],
        "business_term_name": rule[
            "business_term_name"
        ],
        "business_unit": rule[
            "business_unit"
        ],
        "schema_name": rule["schema_name"],
        "table_name": rule["table_name"],
        "column_name": rule["column_name"],
        "dq_dimension": rule[
            "dq_dimension"
        ],
        "rule_type": rule.get(
            "rule_type",
            "",
        ),
        "applicability": rule[
            "applicability"
        ],
        "execution_status": status,
        "total_records": total_records,
        "evaluated_records": evaluated_records,
        "passed_records": passed_records,
        "failed_records": failed_records,
        "dq_score": score,
        "execution_reason": reason,
    }


def execute_rule(rule, dataframe):
    if rule["applicability"] == "Not Applicable":
        return (
            create_assessment_result(
                rule=rule,
                status="Not Applicable",
                total_records=len(dataframe),
                evaluated_records=0,
                passed_records=0,
                failed_records=0,
                score=None,
                reason=rule["planning_reason"],
            ),
            pd.Series(
                False,
                index=dataframe.index,
            ),
            None,
        )

    rule_type = str(rule["rule_type"]).strip()

    if rule_type not in RULE_EXECUTORS:
        return (
            create_assessment_result(
                rule=rule,
                status="Not Executed",
                total_records=len(dataframe),
                evaluated_records=0,
                passed_records=0,
                failed_records=0,
                score=None,
                reason=(
                    f"No executor exists for "
                    f"rule type '{rule_type}'."
                ),
            ),
            pd.Series(
                False,
                index=dataframe.index,
            ),
            None,
        )

    target_column = rule["target_column"]

    if rule_type == "maximum_age_days":
        execution_column = rule[
            "supporting_column"
        ]
    else:
        execution_column = target_column

    if (
        pd.isna(execution_column)
        or str(execution_column)
        not in dataframe.columns
    ):
        return (
            create_assessment_result(
                rule=rule,
                status="Not Executed",
                total_records=len(dataframe),
                evaluated_records=0,
                passed_records=0,
                failed_records=0,
                score=None,
                reason=(
                    f"Required column "
                    f"'{execution_column}' "
                    "was not found."
                ),
            ),
            pd.Series(
                False,
                index=dataframe.index,
            ),
            execution_column,
        )

    parameters = parse_parameters(
        rule["rule_parameters"]
    )

    executor = RULE_EXECUTORS[rule_type]

    evaluated_mask, failure_mask = executor(
        dataframe[str(execution_column)],
        parameters,
    )

    evaluated_count = int(
        evaluated_mask.sum()
    )

    failed_count = int(
        failure_mask.sum()
    )

    passed_count = max(
        0,
        evaluated_count - failed_count,
    )

    if evaluated_count == 0:
        status = "Not Executed"
        score = None
        reason = (
            "The rule found no eligible records "
            "to evaluate."
        )
    else:
        score = round(
            (passed_count / evaluated_count) * 100,
            2,
        )

        if failed_count == 0:
            status = "Passed"
            reason = (
                "All evaluated records satisfied "
                "the rule."
            )
        else:
            status = "Failed"
            reason = failure_reason(rule)

    result = create_assessment_result(
        rule=rule,
        status=status,
        total_records=len(dataframe),
        evaluated_records=evaluated_count,
        passed_records=passed_count,
        failed_records=failed_count,
        score=score,
        reason=reason,
    )

    return result, failure_mask, execution_column


def collect_failures(
    rule,
    dataframe,
    failure_mask,
    execution_column,
):
    if not failure_mask.any():
        return []

    identifier_column = find_identifier_column(
        dataframe
    )

    failed_rows = []

    for index in dataframe.index[failure_mask]:
        failed_value = None

        if (
            execution_column is not None
            and str(execution_column)
            in dataframe.columns
        ):
            failed_value = dataframe.at[
                index,
                str(execution_column),
            ]

        failed_rows.append(
            {
                "rule_id": rule["rule_id"],
                "bt_id": rule["bt_id"],
                "business_term_name": rule[
                    "business_term_name"
                ],
                "business_unit": rule[
                    "business_unit"
                ],
                "table_name": rule["table_name"],
                "target_column": rule[
                    "target_column"
                ],
                "execution_column": (
                    execution_column
                ),
                "dq_dimension": rule[
                    "dq_dimension"
                ],
                "rule_type": rule[
                    "rule_type"
                ],
                "source_row": int(index) + 2,
                "record_identifier": dataframe.at[
                    index,
                    identifier_column,
                ],
                "failed_value": failed_value,
                "failure_reason": (
                    failure_reason(rule)
                ),
            }
        )

    return failed_rows


def aggregate_results(
    results,
    group_columns,
):
    rows = []

    grouped = results.groupby(
        group_columns,
        dropna=False,
    )

    for group_key, group in grouped:
        if not isinstance(group_key, tuple):
            group_key = (group_key,)

        row = dict(
            zip(group_columns, group_key)
        )

        executed = group[
            group["execution_status"]
            .isin(["Passed", "Failed"])
        ]

        evaluated_records = int(
            executed["evaluated_records"].sum()
        )

        passed_records = int(
            executed["passed_records"].sum()
        )

        failed_records = int(
            executed["failed_records"].sum()
        )

        if evaluated_records == 0:
            dq_score = None
        else:
            dq_score = round(
                (
                    passed_records
                    / evaluated_records
                )
                * 100,
                2,
            )

        row.update(
            {
                "planned_assessments": len(group),
                "executed_rules": len(executed),
                "passed_rules": int(
                    (
                        group["execution_status"]
                        == "Passed"
                    ).sum()
                ),
                "failed_rules": int(
                    (
                        group["execution_status"]
                        == "Failed"
                    ).sum()
                ),
                "not_executed_rules": int(
                    (
                        group["execution_status"]
                        == "Not Executed"
                    ).sum()
                ),
                "not_applicable_assessments": int(
                    (
                        group["execution_status"]
                        == "Not Applicable"
                    ).sum()
                ),
                "evaluated_records": (
                    evaluated_records
                ),
                "passed_records": passed_records,
                "failed_records": failed_records,
                "dq_score": dq_score,
            }
        )

        rows.append(row)

    return pd.DataFrame(rows)


def run_batch_dq_execution():
    if not RULE_FILE.exists():
        raise FileNotFoundError(
            f"DQ rule registry not found: "
            f"{RULE_FILE}"
        )

    registry = pd.read_excel(
        RULE_FILE,
        sheet_name="Rule Registry",
    )

    source_cache = {}
    result_rows = []
    failed_rows = []

    print()
    print("Starting batch DQ execution...")

    for rule_number, (_, rule) in enumerate(
        registry.iterrows(),
        start=1,
    ):
        schema_name = str(
            rule["schema_name"]
        ).lower()

        if schema_name not in source_cache:
            source_file = locate_source_file(
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
            ) = execute_rule(
                rule,
                dataframe,
            )

            result_rows.append(result)

            if (
                result["execution_status"]
                == "Failed"
            ):
                failed_rows.extend(
                    collect_failures(
                        rule,
                        dataframe,
                        failure_mask,
                        execution_column,
                    )
                )

        except Exception as error:
            result_rows.append(
                create_assessment_result(
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
    failures = pd.DataFrame(failed_rows)

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
                "executed_rules": int(
                    results[
                        "execution_status"
                        .isin(["Passed", "Failed"])
                    ].shape[0]
                ),
                "passed_rules": int(
                    (
                        results["execution_status"]
                        == "Passed"
                    ).sum()
                ),
                "failed_rules": int(
                    (
                        results["execution_status"]
                        == "Failed"
                    ).sum()
                ),
                "not_executed_rules": int(
                    (
                        results["execution_status"]
                        == "Not Executed"
                    ).sum()
                ),
                "not_applicable_assessments": int(
                    (
                        results["execution_status"]
                        == "Not Applicable"
                    ).sum()
                ),
                "record_failures": len(failures),
            }
        ]
    )

    dimension_summary = aggregate_results(
        results,
        ["dq_dimension"],
    )

    bt_summary = aggregate_results(
        results,
        [
            "bt_id",
            "business_term_name",
        ],
    )

    column_summary = aggregate_results(
        results,
        [
            "business_unit",
            "table_name",
            "column_name",
        ],
    )

    business_unit_summary = aggregate_results(
        results,
        ["business_unit"],
    )

    with pd.ExcelWriter(
        RESULT_FILE,
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
            EXCEL_FAILURE_SAMPLE_LIMIT
        ).to_excel(
            writer,
            sheet_name="Failure Samples",
            index=False,
        )

    failures.to_csv(
        FULL_FAILURE_FILE,
        index=False,
    )

    summary_row = summary.iloc[0]

    print()
    print("Batch DQ execution completed.")
    print(
        f"Source files: "
        f"{summary_row['source_files']}"
    )
    print(
        f"Source records: "
        f"{summary_row['source_records']:,}"
    )
    print(
        f"Planned assessments: "
        f"{summary_row['planned_assessments']}"
    )
    print(
        f"Executed rules: "
        f"{summary_row['executed_rules']}"
    )
    print(
        f"Passed rules: "
        f"{summary_row['passed_rules']}"
    )
    print(
        f"Failed rules: "
        f"{summary_row['failed_rules']}"
    )
    print(
        f"Not Executed: "
        f"{summary_row['not_executed_rules']}"
    )
    print(
        f"Not Applicable: "
        f"{summary_row['not_applicable_assessments']}"
    )
    print(
        f"Record-level failures: "
        f"{summary_row['record_failures']:,}"
    )
    print(f"Saved: {RESULT_FILE}")
    print(f"Saved: {FULL_FAILURE_FILE}")
    print()


if __name__ == "__main__":
    run_batch_dq_execution()