from pathlib import Path
from datetime import datetime, timezone
import json

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[2]

DQ_RESULTS_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_execution_results.xlsx"
)

RULE_REGISTRY_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_rule_registry.xlsx"
)

FAILED_RECORDS_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_failed_records.csv"
)

INSIGHTS_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_agent_insights.xlsx"
)

INSIGHTS_JSON_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_agent_insights.json"
)


REMEDIATIONS = {
    "not_null": (
        "Make the field mandatory at the source and "
        "prevent records with missing values from being "
        "submitted."
    ),
    "email_format": (
        "Validate email syntax during data entry and "
        "correct existing malformed email values."
    ),
    "numeric_minimum": (
        "Apply a non-negative numeric constraint and "
        "review records containing negative values."
    ),
    "identifier_format": (
        "Standardize identifier generation and reject "
        "values outside the approved identifier format."
    ),
    "valid_date": (
        "Enforce a valid date format and correct values "
        "that cannot be interpreted as dates."
    ),
    "allowed_values": (
        "Restrict data entry to approved reference values "
        "and reconcile unsupported values."
    ),
    "non_blank_text": (
        "Trim whitespace and require meaningful text "
        "before saving the record."
    ),
    "reference_match": (
        "Reconcile invalid codes against the approved "
        "reference dataset and strengthen source-system "
        "reference validation."
    ),
    "corporate_email_domain": (
        "Restrict owner emails to the approved corporate "
        "domain and review external or malformed values."
    ),
    "normalized_format": (
        "Normalize casing and whitespace during ingestion "
        "and correct inconsistent existing values."
    ),
    "unique_value": (
        "Investigate duplicate identifiers, merge or "
        "correct duplicate records, and enforce a unique "
        "constraint at the source."
    ),
    "maximum_age_days": (
        "Refresh stale records and introduce a scheduled "
        "metadata update process with freshness monitoring."
    ),
}


ROOT_CAUSES = {
    "not_null": (
        "Required values are not consistently captured "
        "by the source process."
    ),
    "email_format": (
        "The source allows free-text emails without "
        "format validation."
    ),
    "numeric_minimum": (
        "Numeric source controls allow values below the "
        "accepted business minimum."
    ),
    "identifier_format": (
        "Identifier creation is not consistently following "
        "the approved naming convention."
    ),
    "valid_date": (
        "Date values are entered or transformed without "
        "a consistent date standard."
    ),
    "allowed_values": (
        "The source is not fully controlled by approved "
        "reference-value lists."
    ),
    "non_blank_text": (
        "Whitespace or empty text is accepted as a usable "
        "business value."
    ),
    "reference_match": (
        "Source codes are not fully synchronized with "
        "approved enterprise reference data."
    ),
    "corporate_email_domain": (
        "Email-domain validation is missing from the "
        "source workflow."
    ),
    "normalized_format": (
        "Formatting standards are applied inconsistently "
        "across source records."
    ),
    "unique_value": (
        "Duplicate-prevention controls are missing or "
        "ineffective at the source."
    ),
    "maximum_age_days": (
        "Records are not refreshed within the required "
        "metadata freshness period."
    ),
}


SEVERITY_WEIGHT = {
    "Critical": 1.5,
    "High": 1.2,
    "Medium": 1.0,
    "Low": 0.8,
}


def clean_value(value):
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def calculate_priority(
    failure_rate,
    severity,
    failed_records,
):
    severity_weight = SEVERITY_WEIGHT.get(
        str(severity),
        1.0,
    )

    volume_factor = min(
        20,
        failed_records / 100,
    )

    score = (
        failure_rate * severity_weight
        + volume_factor
    )

    return round(min(100, score), 2)


def assign_priority(priority_score):
    if priority_score >= 20:
        return "Critical"

    if priority_score >= 10:
        return "High"

    if priority_score >= 3:
        return "Medium"

    return "Low"


def sample_failed_values(
    failures,
    rule_id,
):
    rule_failures = failures[
        failures["rule_id"] == rule_id
    ]

    if rule_failures.empty:
        return []

    values = (
        rule_failures["failed_value"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .head(5)
        .tolist()
    )

    return values


def build_rule_insights(
    rule_results,
    registry,
    failures,
):
    failed_rules = rule_results[
        rule_results["execution_status"]
        == "Failed"
    ].copy()

    registry_details = registry[
        [
            "rule_id",
            "severity",
            "planning_reason",
        ]
    ].drop_duplicates()

    failed_rules = failed_rules.merge(
        registry_details,
        on="rule_id",
        how="left",
    )

    insights = []

    for _, rule in failed_rules.iterrows():
        evaluated = int(
            rule["evaluated_records"]
        )

        failed = int(rule["failed_records"])

        failure_rate = (
            round((failed / evaluated) * 100, 2)
            if evaluated > 0
            else 0.0
        )

        priority_score = calculate_priority(
            failure_rate,
            rule.get("severity", "High"),
            failed,
        )

        priority = assign_priority(
            priority_score
        )

        rule_type = rule["rule_type"]

        insights.append(
            {
                "insight_id": (
                    f"INS-{len(insights) + 1:05d}"
                ),
                "priority": priority,
                "priority_score": priority_score,
                "rule_id": rule["rule_id"],
                "bt_id": rule["bt_id"],
                "business_term_name": rule[
                    "business_term_name"
                ],
                "business_unit": rule[
                    "business_unit"
                ],
                "table_name": rule["table_name"],
                "column_name": rule[
                    "column_name"
                ],
                "dq_dimension": rule[
                    "dq_dimension"
                ],
                "rule_type": rule_type,
                "dq_score": rule["dq_score"],
                "evaluated_records": evaluated,
                "failed_records": failed,
                "failure_rate": failure_rate,
                "root_cause": ROOT_CAUSES.get(
                    rule_type,
                    (
                        "The source process does not "
                        "consistently satisfy this rule."
                    ),
                ),
                "recommendation": REMEDIATIONS.get(
                    rule_type,
                    (
                        "Review the affected source records "
                        "and strengthen the related control."
                    ),
                ),
                "sample_failed_values": json.dumps(
                    sample_failed_values(
                        failures,
                        rule["rule_id"],
                    ),
                    ensure_ascii=False,
                ),
            }
        )

    insights_dataframe = pd.DataFrame(insights)

    if not insights_dataframe.empty:
        priority_order = {
            "Critical": 1,
            "High": 2,
            "Medium": 3,
            "Low": 4,
        }

        insights_dataframe[
            "_priority_order"
        ] = insights_dataframe[
            "priority"
        ].map(priority_order)

        insights_dataframe = (
            insights_dataframe.sort_values(
                by=[
                    "_priority_order",
                    "priority_score",
                    "failed_records",
                ],
                ascending=[True, False, False],
            )
            .drop(
                columns=["_priority_order"]
            )
            .reset_index(drop=True)
        )

    return insights_dataframe


def build_executive_summary(
    execution_summary,
    insights,
):
    result = execution_summary.iloc[0]

    overall_score = float(
        result["overall_dq_score"]
    )

    if overall_score >= 95:
        health = "Good"
    elif overall_score >= 85:
        health = "Requires Attention"
    else:
        health = "Critical"

    priority_counts = (
        insights["priority"]
        .value_counts()
        .to_dict()
        if not insights.empty
        else {}
    )

    top_issue = None

    if not insights.empty:
        top = insights.iloc[0]

        top_issue = (
            f"{top['business_term_name']} in "
            f"{top['business_unit']} has "
            f"{int(top['failed_records']):,} "
            f"{top['dq_dimension']} failures."
        )

    return pd.DataFrame(
        [
            {
                "generated_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "overall_dq_score": overall_score,
                "data_quality_health": health,
                "execution_coverage": result[
                    "execution_coverage"
                ],
                "source_records": result[
                    "source_records"
                ],
                "executed_rules": result[
                    "executed_rules"
                ],
                "failed_rules": result[
                    "failed_rules"
                ],
                "failed_record_checks": result[
                    "failed_record_checks"
                ],
                "critical_insights": (
                    priority_counts.get(
                        "Critical",
                        0,
                    )
                ),
                "high_insights": (
                    priority_counts.get(
                        "High",
                        0,
                    )
                ),
                "medium_insights": (
                    priority_counts.get(
                        "Medium",
                        0,
                    )
                ),
                "low_insights": (
                    priority_counts.get(
                        "Low",
                        0,
                    )
                ),
                "top_issue_summary": top_issue,
            }
        ]
    )


def build_group_summary(
    rule_results,
    group_column,
):
    rows = []

    for group_value, group in rule_results.groupby(
        group_column
    ):
        executed = group[
            group["execution_status"]
            .isin(["Passed", "Failed"])
        ]

        evaluated = int(
            executed["evaluated_records"].sum()
        )

        passed = int(
            executed["passed_records"].sum()
        )

        failed = int(
            executed["failed_records"].sum()
        )

        score = (
            round((passed / evaluated) * 100, 2)
            if evaluated > 0
            else None
        )

        rows.append(
            {
                group_column: group_value,
                "dq_score": score,
                "executed_rules": len(executed),
                "failed_rules": int(
                    (
                        group["execution_status"]
                        == "Failed"
                    ).sum()
                ),
                "evaluated_record_checks": evaluated,
                "failed_record_checks": failed,
            }
        )

    return pd.DataFrame(rows).sort_values(
        by="dq_score",
        ascending=True,
    )


def write_json(
    executive_summary,
    insights,
    bu_summary,
    dimension_summary,
):
    payload = {
        "executive_summary": {
            key: clean_value(value)
            for key, value in (
                executive_summary.iloc[0]
                .to_dict()
                .items()
            )
        },
        "top_insights": [
            {
                key: clean_value(value)
                for key, value in row.items()
            }
            for row in (
                insights.head(20)
                .to_dict(orient="records")
            )
        ],
        "business_unit_summary": [
            {
                key: clean_value(value)
                for key, value in row.items()
            }
            for row in (
                bu_summary
                .to_dict(orient="records")
            )
        ],
        "dimension_summary": [
            {
                key: clean_value(value)
                for key, value in row.items()
            }
            for row in (
                dimension_summary
                .to_dict(orient="records")
            )
        ],
    }

    with open(
        INSIGHTS_JSON_FILE,
        "w",
        encoding="utf-8",
    ) as output:
        json.dump(
            payload,
            output,
            indent=2,
            ensure_ascii=False,
        )


def run_insights_agent():
    for file_path in [
        DQ_RESULTS_FILE,
        RULE_REGISTRY_FILE,
        FAILED_RECORDS_FILE,
    ]:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file missing: {file_path}"
            )

    execution_summary = pd.read_excel(
        DQ_RESULTS_FILE,
        sheet_name="Summary",
    )

    rule_results = pd.read_excel(
        DQ_RESULTS_FILE,
        sheet_name="Rule Results",
    )

    registry = pd.read_excel(
        RULE_REGISTRY_FILE,
        sheet_name="Rule Registry",
    )

    failures = pd.read_csv(
        FAILED_RECORDS_FILE
    )

    insights = build_rule_insights(
        rule_results,
        registry,
        failures,
    )

    executive_summary = build_executive_summary(
        execution_summary,
        insights,
    )

    bu_summary = build_group_summary(
        rule_results,
        "business_unit",
    )

    dimension_summary = build_group_summary(
        rule_results,
        "dq_dimension",
    )

    with pd.ExcelWriter(
        INSIGHTS_FILE,
        engine="openpyxl",
    ) as writer:
        executive_summary.to_excel(
            writer,
            sheet_name="Executive Summary",
            index=False,
        )

        insights.to_excel(
            writer,
            sheet_name="Prioritized Insights",
            index=False,
        )

        bu_summary.to_excel(
            writer,
            sheet_name="BU Summary",
            index=False,
        )

        dimension_summary.to_excel(
            writer,
            sheet_name="Dimension Summary",
            index=False,
        )

    write_json(
        executive_summary,
        insights,
        bu_summary,
        dimension_summary,
    )

    summary = executive_summary.iloc[0]

    print()
    print("DQ Insights Agent completed.")
    print(
        f"Overall DQ score: "
        f"{summary['overall_dq_score']}%"
    )
    print(
        f"Data Quality health: "
        f"{summary['data_quality_health']}"
    )
    print(
        f"Prioritized insights: "
        f"{len(insights)}"
    )
    print(
        f"Critical insights: "
        f"{summary['critical_insights']}"
    )
    print(
        f"High insights: "
        f"{summary['high_insights']}"
    )
    print(
        f"Top issue: "
        f"{summary['top_issue_summary']}"
    )
    print(f"Saved: {INSIGHTS_FILE}")
    print(f"Saved: {INSIGHTS_JSON_FILE}")
    print()


if __name__ == "__main__":
    run_insights_agent()