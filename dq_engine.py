import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from mapping_engine import calculate_name_score


BASE_DIR = Path(__file__).resolve().parent
DUMMY_DATA_DIR = BASE_DIR / "dummy_data"
OUTPUT_DIR = BASE_DIR / "outputs"

MAPPING_PATH = (
    OUTPUT_DIR / "business_term_steward_mapping.xlsx"
)

DQ_OUTPUT_PATH = (
    OUTPUT_DIR / "data_quality_results.xlsx"
)

MAX_METADATA_AGE_DAYS = 90


def locate_metadata_file():
    possible_files = [
        DUMMY_DATA_DIR / "steward_metadata.xlsx",
        DUMMY_DATA_DIR / "active_directory.xlsx",
        DUMMY_DATA_DIR / "metadata.xlsx",
    ]

    for file_path in possible_files:
        if file_path.exists():
            return file_path

    raise FileNotFoundError(
        "The steward metadata file was not found."
    )


def is_present(value):
    if value is None or pd.isna(value):
        return False

    return bool(str(value).strip())


def valid_email(value):
    if not is_present(value):
        return False

    email_pattern = (
        r"^[A-Za-z0-9._%+-]+@"
        r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    return bool(
        re.fullmatch(
            email_pattern,
            str(value).strip(),
        )
    )


def valid_bt_id(value):
    if not is_present(value):
        return False

    return bool(
        re.fullmatch(
            r"BT-\d{3,}",
            str(value).strip(),
        )
    )


def expected_mapping_status(confidence):
    if confidence >= 90:
        return "Matched"

    if confidence >= 75:
        return "Needs Review"

    return "Not Matched"


def create_rule_result(
    rule_code,
    rule_name,
    dimension,
    valid_mask,
    record_identifiers,
    threshold=95.0,
):
    valid_mask = valid_mask.fillna(False).astype(bool)

    total_records = len(valid_mask)
    passed_records = int(valid_mask.sum())
    failed_records = total_records - passed_records

    if total_records == 0:
        score = 0.0
    else:
        score = round(
            passed_records / total_records * 100,
            2,
        )

    failed_identifiers = (
        record_identifiers[~valid_mask]
        .dropna()
        .astype(str)
        .head(10)
        .tolist()
    )

    status = (
        "Passed"
        if score >= threshold
        else "Failed"
    )

    return {
        "rule_code": rule_code,
        "rule_name": rule_name,
        "dimension": dimension,
        "total_records": total_records,
        "passed_records": passed_records,
        "failed_records": failed_records,
        "score": score,
        "threshold": threshold,
        "status": status,
        "failure_examples": ", ".join(
            failed_identifiers
        ),
    }


def build_required_fields_mask(
    dataframe,
    columns,
):
    mask = pd.Series(
        True,
        index=dataframe.index,
    )

    for column in columns:
        mask = mask & dataframe[column].apply(
            is_present
        )

    return mask


def calculate_mapping_quality(mapping, metadata):
    rule_results = []

    bt_identifiers = mapping["bt_id"].fillna(
        "Missing BT ID"
    )

    employee_identifiers = metadata[
        "employee_id"
    ].fillna("Missing Employee ID")

    # -------------------------------------------------
    # COMPLETENESS
    # -------------------------------------------------

    business_term_required_fields = [
        "bt_id",
        "business_term_name",
        "description",
        "data_steward_input",
    ]

    business_term_completeness = (
        build_required_fields_mask(
            mapping,
            business_term_required_fields,
        )
    )

    rule_results.append(
        create_rule_result(
            rule_code="COM-001",
            rule_name=(
                "Business Term required fields "
                "must be complete"
            ),
            dimension="Completeness",
            valid_mask=business_term_completeness,
            record_identifiers=bt_identifiers,
        )
    )

    employee_required_fields = [
        "matched_employee_id",
        "matched_employee_name",
        "email",
        "department",
        "job_title",
        "account_status",
    ]

    employee_completeness = (
        build_required_fields_mask(
            mapping,
            employee_required_fields,
        )
    )

    rule_results.append(
        create_rule_result(
            rule_code="COM-002",
            rule_name=(
                "Matched steward metadata "
                "must be complete"
            ),
            dimension="Completeness",
            valid_mask=employee_completeness,
            record_identifiers=bt_identifiers,
        )
    )

    # -------------------------------------------------
    # VALIDITY
    # -------------------------------------------------

    bt_id_validity = mapping["bt_id"].apply(
        valid_bt_id
    )

    rule_results.append(
        create_rule_result(
            rule_code="VAL-001",
            rule_name="BT ID must follow BT-000 format",
            dimension="Validity",
            valid_mask=bt_id_validity,
            record_identifiers=bt_identifiers,
        )
    )

    email_validity = mapping["email"].apply(
        valid_email
    )

    rule_results.append(
        create_rule_result(
            rule_code="VAL-002",
            rule_name="Steward email must be valid",
            dimension="Validity",
            valid_mask=email_validity,
            record_identifiers=bt_identifiers,
        )
    )

    allowed_statuses = {
        "Active",
        "Inactive",
    }

    account_status_validity = (
        mapping["account_status"]
        .isin(allowed_statuses)
    )

    rule_results.append(
        create_rule_result(
            rule_code="VAL-003",
            rule_name=(
                "Account status must be "
                "Active or Inactive"
            ),
            dimension="Validity",
            valid_mask=account_status_validity,
            record_identifiers=bt_identifiers,
        )
    )

    # -------------------------------------------------
    # UNIQUENESS
    # -------------------------------------------------

    bt_id_uniqueness = (
        mapping["bt_id"].notna()
        & ~mapping["bt_id"].duplicated(
            keep=False
        )
    )

    rule_results.append(
        create_rule_result(
            rule_code="UNI-001",
            rule_name="BT ID must be unique",
            dimension="Uniqueness",
            valid_mask=bt_id_uniqueness,
            record_identifiers=bt_identifiers,
            threshold=100.0,
        )
    )

    employee_id_uniqueness = (
        metadata["employee_id"].notna()
        & ~metadata["employee_id"].duplicated(
            keep=False
        )
    )

    rule_results.append(
        create_rule_result(
            rule_code="UNI-002",
            rule_name=(
                "Employee ID must be unique "
                "in steward metadata"
            ),
            dimension="Uniqueness",
            valid_mask=employee_id_uniqueness,
            record_identifiers=employee_identifiers,
            threshold=100.0,
        )
    )

    # -------------------------------------------------
    # CONSISTENCY
    # -------------------------------------------------

    steward_name_scores = mapping.apply(
        lambda row: calculate_name_score(
            row["data_steward_input"],
            row["matched_employee_name"],
        ),
        axis=1,
    )

    name_consistency = (
        steward_name_scores >= 75
    )

    rule_results.append(
        create_rule_result(
            rule_code="CON-001",
            rule_name=(
                "Steward input must agree with "
                "the matched employee name"
            ),
            dimension="Consistency",
            valid_mask=name_consistency,
            record_identifiers=bt_identifiers,
        )
    )

    status_consistency = mapping.apply(
        lambda row: (
            str(row["mapping_status"]).strip()
            == expected_mapping_status(
                float(
                    row["mapping_confidence"]
                )
            )
        ),
        axis=1,
    )

    rule_results.append(
        create_rule_result(
            rule_code="CON-002",
            rule_name=(
                "Mapping status must agree "
                "with confidence"
            ),
            dimension="Consistency",
            valid_mask=status_consistency,
            record_identifiers=bt_identifiers,
            threshold=100.0,
        )
    )

    # -------------------------------------------------
    # ACCURACY
    # -------------------------------------------------

    confidence_values = pd.to_numeric(
        mapping["mapping_confidence"],
        errors="coerce",
    ).fillna(0)

    high_confidence_mapping = (
        (confidence_values >= 90)
        & (
            mapping["mapping_status"]
            == "Matched"
        )
    )

    rule_results.append(
        create_rule_result(
            rule_code="ACC-001",
            rule_name=(
                "Steward mapping must have at "
                "least 90 percent confidence"
            ),
            dimension="Accuracy",
            valid_mask=high_confidence_mapping,
            record_identifiers=bt_identifiers,
        )
    )

    active_account = (
        mapping["account_status"]
        == "Active"
    )

    rule_results.append(
        create_rule_result(
            rule_code="ACC-002",
            rule_name=(
                "Mapped steward account "
                "must be active"
            ),
            dimension="Accuracy",
            valid_mask=active_account,
            record_identifiers=bt_identifiers,
        )
    )

    # -------------------------------------------------
    # TIMELINESS
    # -------------------------------------------------

    last_updated = pd.to_datetime(
        mapping["metadata_last_updated"],
        errors="coerce",
    )

    current_time = pd.Timestamp.now()

    metadata_age_days = (
        current_time - last_updated
    ).dt.days

    metadata_timeliness = (
        last_updated.notna()
        & metadata_age_days.between(
            0,
            MAX_METADATA_AGE_DAYS,
        )
    )

    rule_results.append(
        create_rule_result(
            rule_code="TIM-001",
            rule_name=(
                "Steward metadata must be "
                "updated within 90 days"
            ),
            dimension="Timeliness",
            valid_mask=metadata_timeliness,
            record_identifiers=bt_identifiers,
        )
    )

    rule_results_dataframe = pd.DataFrame(
        rule_results
    )

    dimension_scores = (
        rule_results_dataframe
        .groupby(
            "dimension",
            as_index=False,
        )
        .agg(
            score=("score", "mean"),
            passed_rules=(
                "status",
                lambda values: (
                    values == "Passed"
                ).sum(),
            ),
            total_rules=("rule_code", "count"),
        )
    )

    dimension_scores["score"] = (
        dimension_scores["score"]
        .round(2)
    )

    overall_score = round(
        dimension_scores["score"].mean(),
        2,
    )

    return (
        rule_results_dataframe,
        dimension_scores,
        overall_score,
        {
            "business_term_completeness":
                business_term_completeness,
            "employee_completeness":
                employee_completeness,
            "bt_id_validity":
                bt_id_validity,
            "email_validity":
                email_validity,
            "account_status_validity":
                account_status_validity,
            "bt_id_uniqueness":
                bt_id_uniqueness,
            "name_consistency":
                name_consistency,
            "status_consistency":
                status_consistency,
            "high_confidence_mapping":
                high_confidence_mapping,
            "active_account":
                active_account,
            "metadata_timeliness":
                metadata_timeliness,
        },
    )


def create_record_results(
    mapping,
    masks,
):
    results = mapping.copy()

    results["completeness_passed"] = (
        masks["business_term_completeness"]
        & masks["employee_completeness"]
    )

    results["validity_passed"] = (
        masks["bt_id_validity"]
        & masks["email_validity"]
        & masks["account_status_validity"]
    )

    results["uniqueness_passed"] = (
        masks["bt_id_uniqueness"]
    )

    results["consistency_passed"] = (
        masks["name_consistency"]
        & masks["status_consistency"]
    )

    results["accuracy_passed"] = (
        masks["high_confidence_mapping"]
        & masks["active_account"]
    )

    results["timeliness_passed"] = (
        masks["metadata_timeliness"]
    )

    dimension_columns = [
        "completeness_passed",
        "validity_passed",
        "uniqueness_passed",
        "consistency_passed",
        "accuracy_passed",
        "timeliness_passed",
    ]

    results["record_dq_score"] = (
        results[dimension_columns]
        .mean(axis=1)
        .mul(100)
        .round(2)
    )

    def failure_reasons(row):
        failures = []

        labels = {
            "completeness_passed":
                "Incomplete required information",
            "validity_passed":
                "Invalid identifier, email or status",
            "uniqueness_passed":
                "Duplicate BT ID",
            "consistency_passed":
                "Steward and mapping are inconsistent",
            "accuracy_passed":
                "Low-confidence or inactive steward",
            "timeliness_passed":
                "Missing or stale metadata",
        }

        for column, message in labels.items():
            if not bool(row[column]):
                failures.append(message)

        return "; ".join(failures)

    results["dq_failure_reasons"] = (
        results.apply(
            failure_reasons,
            axis=1,
        )
    )

    return results


def generate_recommendations(
    rule_results,
):
    recommendations = []

    for _, rule in rule_results.iterrows():
        if rule["status"] == "Passed":
            continue

        recommendations.append(
            {
                "rule_code": rule["rule_code"],
                "dimension": rule["dimension"],
                "severity": (
                    "High"
                    if rule["score"] < 90
                    else "Medium"
                ),
                "issue": rule["rule_name"],
                "score": rule["score"],
                "failed_records":
                    rule["failed_records"],
                "recommendation": (
                    "Review the failed Business Terms, "
                    "correct the source information and "
                    "rerun the mapping pipeline."
                ),
            }
        )

    return pd.DataFrame(recommendations)


def execute_data_quality():
    if not MAPPING_PATH.exists():
        raise FileNotFoundError(
            "The mapping output does not exist. "
            "Run mapping_engine.py first."
        )

    metadata_path = locate_metadata_file()

    mapping = pd.read_excel(
        MAPPING_PATH,
        sheet_name="All Results",
    )

    metadata = pd.read_excel(
        metadata_path,
    )

    (
        rule_results,
        dimension_scores,
        overall_score,
        masks,
    ) = calculate_mapping_quality(
        mapping,
        metadata,
    )

    record_results = create_record_results(
        mapping,
        masks,
    )

    failed_records = record_results[
        record_results["record_dq_score"] < 100
    ].copy()

    recommendations = generate_recommendations(
        rule_results
    )

    summary = pd.DataFrame(
        [
            {
                "execution_time": datetime.now(),
                "total_business_terms":
                    len(mapping),
                "matched_terms": int(
                    (
                        mapping["mapping_status"]
                        == "Matched"
                    ).sum()
                ),
                "needs_review": int(
                    (
                        mapping["mapping_status"]
                        == "Needs Review"
                    ).sum()
                ),
                "not_matched": int(
                    (
                        mapping["mapping_status"]
                        == "Not Matched"
                    ).sum()
                ),
                "total_rules":
                    len(rule_results),
                "passed_rules": int(
                    (
                        rule_results["status"]
                        == "Passed"
                    ).sum()
                ),
                "failed_rules": int(
                    (
                        rule_results["status"]
                        == "Failed"
                    ).sum()
                ),
                "overall_dq_score":
                    overall_score,
            }
        ]
    )

    with pd.ExcelWriter(
        DQ_OUTPUT_PATH,
        engine="openpyxl",
    ) as writer:
        summary.to_excel(
            writer,
            sheet_name="Summary",
            index=False,
        )

        dimension_scores.to_excel(
            writer,
            sheet_name="Dimension Scores",
            index=False,
        )

        rule_results.to_excel(
            writer,
            sheet_name="Rule Results",
            index=False,
        )

        record_results.to_excel(
            writer,
            sheet_name="Record Results",
            index=False,
        )

        failed_records.to_excel(
            writer,
            sheet_name="Failed Records",
            index=False,
        )

        recommendations.to_excel(
            writer,
            sheet_name="Recommendations",
            index=False,
        )

    print()
    print("Data quality execution completed.")
    print(f"Business terms assessed: {len(mapping)}")
    print(f"DQ rules executed: {len(rule_results)}")
    print(
        f"Rules passed: "
        f"{(rule_results['status'] == 'Passed').sum()}"
    )
    print(
        f"Rules failed: "
        f"{(rule_results['status'] == 'Failed').sum()}"
    )
    print(f"Overall DQ score: {overall_score}%")
    print()
    print("Dimension scores:")
    print(
        dimension_scores[
            ["dimension", "score"]
        ].to_string(index=False)
    )
    print()
    print(f"Results saved to: {DQ_OUTPUT_PATH}")


if __name__ == "__main__":
    execute_data_quality()