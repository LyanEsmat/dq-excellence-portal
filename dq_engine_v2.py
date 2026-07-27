from pathlib import Path
from datetime import datetime, timezone
import re
import unicodedata

import pandas as pd
from rapidfuzz.fuzz import ratio


BASE_DIR = Path(__file__).resolve().parent
MAPPING_FILE = BASE_DIR / "outputs" / "business_term_steward_mapping.xlsx"
OUTPUT_FILE = BASE_DIR / "outputs" / "data_quality_results_v2.xlsx"

DQ_DIMENSIONS = [
    "Completeness",
    "Validity",
    "Accuracy",
    "Consistency",
    "Uniqueness",
    "Timeliness",
]


COLUMN_ALIASES = {
    "bt_id": [
        "bt_id",
        "business_term_id",
        "business term id",
        "business_term_identifier",
    ],
    "business_term_name": [
        "business_term_name",
        "business term",
        "business term name",
        "term_name",
    ],
    "description": [
        "description",
        "business_term_description",
        "business term description",
    ],
    "data_steward": [
        "data_steward",
        "data steward",
        "steward_input",
        "steward input",
    ],
    "matched_employee_name": [
        "matched_employee_name",
        "matched employee",
        "employee_name",
        "employee name",
    ],
    "employee_id": [
        "employee_id",
        "employee id",
        "matched_employee_id",
    ],
    "email": [
        "email",
        "employee_email",
        "employee email",
        "matched_email",
    ],
    "department": [
        "department",
        "department_name",
        "department name",
    ],
    "job_title": [
        "job_title",
        "job title",
        "employee_job_title",
    ],
    "account_status": [
        "account_status",
        "account status",
        "employee_status",
    ],
    "last_updated": [
        "last_updated",
        "last updated",
        "updated_at",
        "modified_date",
    ],
    "mapping_status": [
        "mapping_status",
        "mapping status",
        "match_status",
        "match status",
        "status",
    ],
}


def normalize_column_name(value):
    value = str(value).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def normalize_text(value):
    if pd.isna(value):
        return ""

    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def is_missing(value):
    if pd.isna(value):
        return True

    text = str(value).strip().lower()
    return text in {"", "nan", "none", "null", "n/a", "na"}


def find_column(dataframe, canonical_name):
    normalized_columns = {
        normalize_column_name(column): column
        for column in dataframe.columns
    }

    aliases = COLUMN_ALIASES.get(canonical_name, [canonical_name])

    for alias in aliases:
        normalized_alias = normalize_column_name(alias)

        if normalized_alias in normalized_columns:
            return normalized_columns[normalized_alias]

    return None


def get_value(row, columns, canonical_name):
    actual_column = columns.get(canonical_name)

    if actual_column is None:
        return None

    return row.get(actual_column)


def create_result(
    bt_id,
    business_term,
    dimension,
    target_column,
    status,
    score,
    actual_value,
    reason,
    recommendation,
):
    return {
        "bt_id": bt_id,
        "business_term_name": business_term,
        "dq_dimension": dimension,
        "target_column": target_column,
        "execution_status": status,
        "score": score,
        "actual_value": (
            ""
            if is_missing(actual_value)
            else str(actual_value)
        ),
        "reason": reason,
        "recommendation": recommendation,
    }


def evaluate_completeness(row, columns, bt_id, business_term):
    required_fields = [
        "bt_id",
        "business_term_name",
        "description",
        "data_steward",
        "matched_employee_name",
        "email",
        "department",
    ]

    missing_fields = []

    for field in required_fields:
        if is_missing(get_value(row, columns, field)):
            missing_fields.append(field)

    if not missing_fields:
        return create_result(
            bt_id,
            business_term,
            "Completeness",
            ", ".join(required_fields),
            "Passed",
            100,
            "All required values are populated",
            "All required business-term and steward fields are available.",
            "No action is required.",
        )

    return create_result(
        bt_id,
        business_term,
        "Completeness",
        ", ".join(missing_fields),
        "Failed",
        round(
            ((len(required_fields) - len(missing_fields))
             / len(required_fields)) * 100,
            2,
        ),
        ", ".join(missing_fields),
        "Required values are missing: "
        + ", ".join(missing_fields),
        "Populate the missing values before publishing this business term.",
    )


def evaluate_validity(row, columns, bt_id, business_term):
    bt_value = get_value(row, columns, "bt_id")
    email = get_value(row, columns, "email")

    issues = []

    if is_missing(bt_value):
        issues.append("The Business Term ID is missing.")
    elif not re.fullmatch(
        r"BT[-_ ]?\d+",
        str(bt_value).strip(),
        flags=re.IGNORECASE,
    ):
        issues.append(
            "The Business Term ID does not follow the expected BT-000 format."
        )

    if is_missing(email):
        issues.append("The employee email is missing.")
    elif not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        str(email).strip(),
    ):
        issues.append("The employee email format is invalid.")

    if issues:
        return create_result(
            bt_id,
            business_term,
            "Validity",
            "bt_id, email",
            "Failed",
            0,
            f"BT ID: {bt_value}; Email: {email}",
            " ".join(issues),
            "Correct the Business Term ID or employee email format.",
        )

    return create_result(
        bt_id,
        business_term,
        "Validity",
        "bt_id, email",
        "Passed",
        100,
        f"BT ID: {bt_value}; Email: {email}",
        "The Business Term ID and employee email use valid formats.",
        "No action is required.",
    )


def evaluate_accuracy(row, columns, bt_id, business_term):
    mapping_status = get_value(row, columns, "mapping_status")
    matched_employee = get_value(
        row,
        columns,
        "matched_employee_name",
    )

    if is_missing(mapping_status):
        return create_result(
            bt_id,
            business_term,
            "Accuracy",
            "mapping_status",
            "Not Executed",
            None,
            mapping_status,
            "Accuracy could not be assessed because mapping_status is missing.",
            "Run the mapping process and store a mapping status.",
        )

    normalized_status = normalize_text(mapping_status)

    if normalized_status in {"matched", "approved"}:
        return create_result(
            bt_id,
            business_term,
            "Accuracy",
            "matched_employee_name",
            "Passed",
            100,
            matched_employee,
            "The steward was successfully mapped to an employee record.",
            "No action is required.",
        )

    if normalized_status in {
        "needs review",
        "review",
        "manual review",
    }:
        return create_result(
            bt_id,
            business_term,
            "Accuracy",
            "matched_employee_name",
            "Failed",
            50,
            matched_employee,
            "The employee match is uncertain and requires manual validation.",
            "Ask a Data Governance reviewer to validate the suggested employee.",
        )

    return create_result(
        bt_id,
        business_term,
        "Accuracy",
        "matched_employee_name",
        "Failed",
        0,
        matched_employee,
        "No accepted employee record was found for the Data Steward.",
        "Correct the steward name or add the person to the metadata file.",
    )


def evaluate_consistency(row, columns, bt_id, business_term):
    steward = get_value(row, columns, "data_steward")
    employee = get_value(row, columns, "matched_employee_name")

    if is_missing(steward) or is_missing(employee):
        return create_result(
            bt_id,
            business_term,
            "Consistency",
            "data_steward, matched_employee_name",
            "Not Executed",
            None,
            f"Steward: {steward}; Employee: {employee}",
            "Consistency could not be assessed because one or both names are missing.",
            "Populate the steward and matched employee names, then rerun DQ.",
        )

    similarity = ratio(
        normalize_text(steward),
        normalize_text(employee),
    )

    if similarity >= 85:
        return create_result(
            bt_id,
            business_term,
            "Consistency",
            "data_steward, matched_employee_name",
            "Passed",
            round(similarity, 2),
            f"{steward} ↔ {employee}",
            "The steward name is consistent with the matched employee name.",
            "No action is required.",
        )

    return create_result(
        bt_id,
        business_term,
        "Consistency",
        "data_steward, matched_employee_name",
        "Failed",
        round(similarity, 2),
        f"{steward} ↔ {employee}",
        "The steward and matched employee names are not sufficiently similar.",
        "Review the employee mapping and correct the steward name if necessary.",
    )


def evaluate_uniqueness(
    row,
    columns,
    dataframe,
    bt_id,
    business_term,
):
    bt_column = columns.get("bt_id")

    if bt_column is None or is_missing(bt_id):
        return create_result(
            bt_id,
            business_term,
            "Uniqueness",
            "bt_id",
            "Not Executed",
            None,
            bt_id,
            "Uniqueness could not be assessed because the Business Term ID is missing.",
            "Assign a Business Term ID, then rerun DQ.",
        )

    normalized_ids = (
        dataframe[bt_column]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    occurrence_count = int(
        (normalized_ids == str(bt_id).strip().lower()).sum()
    )

    if occurrence_count == 1:
        return create_result(
            bt_id,
            business_term,
            "Uniqueness",
            "bt_id",
            "Passed",
            100,
            bt_id,
            "The Business Term ID occurs exactly once.",
            "No action is required.",
        )

    return create_result(
        bt_id,
        business_term,
        "Uniqueness",
        "bt_id",
        "Failed",
        0,
        bt_id,
        f"The Business Term ID occurs {occurrence_count} times.",
        "Assign a unique identifier to each business term.",
    )


def evaluate_timeliness(row, columns, bt_id, business_term):
    last_updated = get_value(row, columns, "last_updated")

    if is_missing(last_updated):
        return create_result(
            bt_id,
            business_term,
            "Timeliness",
            "last_updated",
            "Not Executed",
            None,
            last_updated,
            "Timeliness could not be assessed because last_updated is missing.",
            "Add a metadata update date and rerun DQ.",
        )

    parsed_date = pd.to_datetime(
        last_updated,
        errors="coerce",
        utc=True,
    )

    if pd.isna(parsed_date):
        return create_result(
            bt_id,
            business_term,
            "Timeliness",
            "last_updated",
            "Failed",
            0,
            last_updated,
            "The metadata update date could not be interpreted.",
            "Replace the value with a valid date.",
        )

    current_date = pd.Timestamp.now(tz="UTC")
    age_days = int((current_date - parsed_date).days)

    if age_days <= 365:
        score = max(
            0,
            round(100 - ((age_days / 365) * 20), 2),
        )

        return create_result(
            bt_id,
            business_term,
            "Timeliness",
            "last_updated",
            "Passed",
            score,
            parsed_date.date(),
            f"The employee metadata was updated {age_days} days ago.",
            "No action is required.",
        )

    return create_result(
        bt_id,
        business_term,
        "Timeliness",
        "last_updated",
        "Failed",
        0,
        parsed_date.date(),
        f"The employee metadata is stale because it was updated {age_days} days ago.",
        "Verify the employee record and refresh the metadata.",
    )


def load_mapping_data():
    if not MAPPING_FILE.exists():
        raise FileNotFoundError(
            "Mapping output was not found. Run mapping_engine.py first.\n"
            f"Expected file: {MAPPING_FILE}"
        )

    try:
        return pd.read_excel(
            MAPPING_FILE,
            sheet_name="All Results",
        )
    except ValueError:
        return pd.read_excel(MAPPING_FILE)


def build_dimension_summary(results):
    executed = results[
        results["execution_status"] != "Not Executed"
    ].copy()

    rows = []

    for dimension in DQ_DIMENSIONS:
        all_dimension_rows = results[
            results["dq_dimension"] == dimension
        ]

        executed_rows = executed[
            executed["dq_dimension"] == dimension
        ]

        passed = int(
            (
                all_dimension_rows["execution_status"]
                == "Passed"
            ).sum()
        )

        failed = int(
            (
                all_dimension_rows["execution_status"]
                == "Failed"
            ).sum()
        )

        not_executed = int(
            (
                all_dimension_rows["execution_status"]
                == "Not Executed"
            ).sum()
        )

        if executed_rows.empty:
            score = 0
        else:
            score = round(
                executed_rows["score"].fillna(0).mean(),
                2,
            )

        rows.append(
            {
                "dimension": dimension,
                "score": score,
                "passed": passed,
                "failed": failed,
                "not_executed": not_executed,
                "total_business_terms": len(
                    all_dimension_rows
                ),
            }
        )

    return pd.DataFrame(rows)


def build_business_term_summary(results):
    rows = []

    for (bt_id, term_name), group in results.groupby(
        ["bt_id", "business_term_name"],
        dropna=False,
    ):
        executed = group[
            group["execution_status"] != "Not Executed"
        ]

        if executed.empty:
            score = 0
        else:
            score = round(
                executed["score"].fillna(0).mean(),
                2,
            )

        rows.append(
            {
                "bt_id": bt_id,
                "business_term_name": term_name,
                "dq_score": score,
                "passed": int(
                    (group["execution_status"] == "Passed").sum()
                ),
                "failed": int(
                    (group["execution_status"] == "Failed").sum()
                ),
                "not_executed": int(
                    (
                        group["execution_status"]
                        == "Not Executed"
                    ).sum()
                ),
                "total_dimensions": len(group),
            }
        )

    return pd.DataFrame(rows)


def build_column_summary(results):
    rows = []

    for column_name, group in results.groupby(
        "target_column",
        dropna=False,
    ):
        executed = group[
            group["execution_status"] != "Not Executed"
        ]

        if executed.empty:
            score = 0
        else:
            score = round(
                executed["score"].fillna(0).mean(),
                2,
            )

        rows.append(
            {
                "target_column": column_name,
                "dq_score": score,
                "passed": int(
                    (group["execution_status"] == "Passed").sum()
                ),
                "failed": int(
                    (group["execution_status"] == "Failed").sum()
                ),
                "not_executed": int(
                    (
                        group["execution_status"]
                        == "Not Executed"
                    ).sum()
                ),
                "total_executions": len(group),
            }
        )

    return pd.DataFrame(rows)


def run_data_quality_v2():
    dataframe = load_mapping_data()

    columns = {
        name: find_column(dataframe, name)
        for name in COLUMN_ALIASES
    }

    missing_core_columns = [
        name
        for name in [
            "bt_id",
            "business_term_name",
        ]
        if columns.get(name) is None
    ]

    if missing_core_columns:
        raise ValueError(
            "Required mapping columns were not found: "
            + ", ".join(missing_core_columns)
            + "\nAvailable columns: "
            + ", ".join(map(str, dataframe.columns))
        )

    results = []

    for _, row in dataframe.iterrows():
        bt_id = get_value(row, columns, "bt_id")
        business_term = get_value(
            row,
            columns,
            "business_term_name",
        )

        results.append(
            evaluate_completeness(
                row,
                columns,
                bt_id,
                business_term,
            )
        )

        results.append(
            evaluate_validity(
                row,
                columns,
                bt_id,
                business_term,
            )
        )

        results.append(
            evaluate_accuracy(
                row,
                columns,
                bt_id,
                business_term,
            )
        )

        results.append(
            evaluate_consistency(
                row,
                columns,
                bt_id,
                business_term,
            )
        )

        results.append(
            evaluate_uniqueness(
                row,
                columns,
                dataframe,
                bt_id,
                business_term,
            )
        )

        results.append(
            evaluate_timeliness(
                row,
                columns,
                bt_id,
                business_term,
            )
        )

    result_dataframe = pd.DataFrame(results)

    dimension_summary = build_dimension_summary(
        result_dataframe
    )

    business_term_summary = build_business_term_summary(
        result_dataframe
    )

    column_summary = build_column_summary(
        result_dataframe
    )

    passed_count = int(
        (
            result_dataframe["execution_status"]
            == "Passed"
        ).sum()
    )

    failed_count = int(
        (
            result_dataframe["execution_status"]
            == "Failed"
        ).sum()
    )

    not_executed_count = int(
        (
            result_dataframe["execution_status"]
            == "Not Executed"
        ).sum()
    )

    executed_results = result_dataframe[
        result_dataframe["execution_status"]
        != "Not Executed"
    ]

    if executed_results.empty:
        overall_score = 0
    else:
        overall_score = round(
            executed_results["score"].fillna(0).mean(),
            2,
        )

    summary = pd.DataFrame(
        [
            {
                "execution_time": datetime.now(
                    timezone.utc
                ).isoformat(),
                "business_terms_assessed": len(dataframe),
                "dimensions_per_business_term": 6,
                "total_dq_executions": len(
                    result_dataframe
                ),
                "passed": passed_count,
                "failed": failed_count,
                "not_executed": not_executed_count,
                "overall_dq_score": overall_score,
            }
        ]
    )

    failed_results = result_dataframe[
        result_dataframe["execution_status"]
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

        result_dataframe.to_excel(
            writer,
            sheet_name="All DQ Executions",
            index=False,
        )

        failed_results.to_excel(
            writer,
            sheet_name="Failures",
            index=False,
        )

    print()
    print("Data Quality V2 execution completed.")
    print(f"Business terms assessed: {len(dataframe)}")
    print("DQ dimensions per Business Term: 6")
    print(
        f"Total DQ executions: {len(result_dataframe)}"
    )
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print(f"Not executed: {not_executed_count}")
    print(f"Overall DQ score: {overall_score}%")
    print(f"Results saved to: {OUTPUT_FILE}")
    print()

    print("Dimension scores:")
    print(
        dimension_summary.to_string(index=False)
    )

    return {
        "summary": summary.iloc[0].to_dict(),
        "dimension_scores": (
            dimension_summary.to_dict(orient="records")
        ),
        "business_term_scores": (
            business_term_summary.to_dict(
                orient="records"
            )
        ),
        "column_scores": (
            column_summary.to_dict(orient="records")
        ),
        "dq_executions": (
            result_dataframe.to_dict(
                orient="records"
            )
        ),
        "failures": (
            failed_results.to_dict(
                orient="records"
            )
        ),
    }


if __name__ == "__main__":
    run_data_quality_v2()