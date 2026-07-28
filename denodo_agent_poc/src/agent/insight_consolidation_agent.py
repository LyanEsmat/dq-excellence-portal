from pathlib import Path
from datetime import datetime, timezone
import json

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[2]

INSIGHTS_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_agent_insights.xlsx"
)

RULE_REGISTRY_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_rule_registry.xlsx"
)

OUTPUT_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "consolidated_dq_insights.xlsx"
)

OUTPUT_JSON_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "consolidated_dq_insights.json"
)


PRIORITY_ORDER = {
    "Critical": 1,
    "High": 2,
    "Medium": 3,
    "Low": 4,
}


def clean_value(value):
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def choose_highest_priority(values):
    priorities = [
        value
        for value in values
        if value in PRIORITY_ORDER
    ]

    if not priorities:
        return "Low"

    return min(
        priorities,
        key=lambda value: PRIORITY_ORDER[value],
    )


def join_unique(values):
    cleaned = sorted(
        {
            str(value).strip()
            for value in values
            if not pd.isna(value)
            and str(value).strip()
        }
    )

    return ", ".join(cleaned)


def create_issue_title(row):
    dimension = row["dq_dimension"]
    business_unit = row["business_unit"]
    table_name = row["table_name"]
    execution_column = row["execution_column"]
    failed_records = int(
        row["affected_records"]
    )

    if dimension == "Timeliness":
        return (
            f"{business_unit}: {failed_records:,} "
            f"records in {table_name} contain stale "
            f"or invalid {execution_column} values."
        )

    return (
        f"{business_unit}: {failed_records:,} "
        f"records failed {dimension} for "
        f"{execution_column}."
    )


def create_consolidated_explanation(row):
    affected_terms = int(
        row["affected_business_term_count"]
    )

    rule_occurrences = int(
        row["combined_rule_count"]
    )

    if row["dq_dimension"] == "Timeliness":
        return (
            f"This is one underlying Timeliness issue "
            f"on the supporting column "
            f"'{row['execution_column']}'. It appeared "
            f"in {rule_occurrences} rule results because "
            f"{affected_terms} mapped Business Terms use "
            f"the same source-record freshness timestamp. "
            f"The affected-record count is not multiplied."
        )

    if rule_occurrences > 1:
        return (
            f"This issue consolidates "
            f"{rule_occurrences} related rule results "
            f"affecting {affected_terms} Business Terms "
            f"on the same technical field."
        )

    return (
        "This issue represents one failed DQ rule "
        "on one mapped technical field."
    )


def load_and_prepare():
    if not INSIGHTS_FILE.exists():
        raise FileNotFoundError(
            f"DQ insights file missing: "
            f"{INSIGHTS_FILE}"
        )

    if not RULE_REGISTRY_FILE.exists():
        raise FileNotFoundError(
            f"Rule registry missing: "
            f"{RULE_REGISTRY_FILE}"
        )

    insights = pd.read_excel(
        INSIGHTS_FILE,
        sheet_name="Prioritized Insights",
    )

    registry = pd.read_excel(
        RULE_REGISTRY_FILE,
        sheet_name="Rule Registry",
    )

    supporting_columns = registry[
        [
            "rule_id",
            "supporting_column",
        ]
    ].drop_duplicates(
        subset=["rule_id"]
    )

    insights = insights.merge(
        supporting_columns,
        on="rule_id",
        how="left",
    )

    insights["execution_column"] = (
        insights["supporting_column"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    missing_execution_column = (
        insights["execution_column"] == ""
    )

    insights.loc[
        missing_execution_column,
        "execution_column",
    ] = insights.loc[
        missing_execution_column,
        "column_name",
    ]

    return insights


def consolidate_insights(insights):
    group_columns = [
        "business_unit",
        "table_name",
        "dq_dimension",
        "rule_type",
        "execution_column",
    ]

    consolidated_rows = []

    for group_key, group in insights.groupby(
        group_columns,
        dropna=False,
    ):
        (
            business_unit,
            table_name,
            dimension,
            rule_type,
            execution_column,
        ) = group_key

        affected_bt_ids = join_unique(
            group["bt_id"]
        )

        affected_bt_names = join_unique(
            group["business_term_name"]
        )

        unique_bt_count = group[
            "bt_id"
        ].nunique()

        # The same physical failed records may support
        # several BT rules. Use the maximum, not the sum,
        # to prevent duplicated impact counts.
        affected_records = int(
            group["failed_records"].max()
        )

        evaluated_records = int(
            group["evaluated_records"].max()
        )

        failure_rate = (
            round(
                (
                    affected_records
                    / evaluated_records
                )
                * 100,
                2,
            )
            if evaluated_records > 0
            else 0.0
        )

        priority = choose_highest_priority(
            group["priority"].tolist()
        )

        priority_score = round(
            float(
                group["priority_score"].max()
            ),
            2,
        )

        dq_score = round(
            float(group["dq_score"].min()),
            2,
        )

        row = {
            "consolidated_insight_id": (
                f"CON-{len(consolidated_rows) + 1:05d}"
            ),
            "priority": priority,
            "priority_score": priority_score,
            "business_unit": business_unit,
            "table_name": table_name,
            "dq_dimension": dimension,
            "rule_type": rule_type,
            "execution_column": execution_column,
            "dq_score": dq_score,
            "evaluated_records": evaluated_records,
            "affected_records": affected_records,
            "failure_rate": failure_rate,
            "combined_rule_count": len(group),
            "affected_business_term_count": (
                unique_bt_count
            ),
            "affected_bt_ids": affected_bt_ids,
            "affected_business_terms": (
                affected_bt_names
            ),
            "root_cause": group.iloc[0][
                "root_cause"
            ],
            "recommendation": group.iloc[0][
                "recommendation"
            ],
        }

        row["issue_title"] = create_issue_title(
            row
        )

        row["consolidation_explanation"] = (
            create_consolidated_explanation(row)
        )

        consolidated_rows.append(row)

    consolidated = pd.DataFrame(
        consolidated_rows
    )

    consolidated["_priority_order"] = (
        consolidated["priority"].map(
            PRIORITY_ORDER
        )
    )

    consolidated = (
        consolidated.sort_values(
            by=[
                "_priority_order",
                "priority_score",
                "affected_records",
            ],
            ascending=[True, False, False],
        )
        .drop(columns=["_priority_order"])
        .reset_index(drop=True)
    )

    return consolidated


def build_summary(
    original_insights,
    consolidated,
):
    repeated_alerts_removed = (
        len(original_insights)
        - len(consolidated)
    )

    priority_counts = (
        consolidated["priority"]
        .value_counts()
        .to_dict()
    )

    return pd.DataFrame(
        [
            {
                "generated_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "original_rule_insights": len(
                    original_insights
                ),
                "consolidated_issues": len(
                    consolidated
                ),
                "repeated_alerts_removed": (
                    repeated_alerts_removed
                ),
                "critical_issues": (
                    priority_counts.get(
                        "Critical",
                        0,
                    )
                ),
                "high_issues": (
                    priority_counts.get(
                        "High",
                        0,
                    )
                ),
                "medium_issues": (
                    priority_counts.get(
                        "Medium",
                        0,
                    )
                ),
                "low_issues": (
                    priority_counts.get(
                        "Low",
                        0,
                    )
                ),
                "top_issue": (
                    consolidated.iloc[0][
                        "issue_title"
                    ]
                    if not consolidated.empty
                    else None
                ),
            }
        ]
    )


def write_json(summary, consolidated):
    payload = {
        "summary": {
            key: clean_value(value)
            for key, value in (
                summary.iloc[0]
                .to_dict()
                .items()
            )
        },
        "consolidated_insights": [
            {
                key: clean_value(value)
                for key, value in row.items()
            }
            for row in (
                consolidated
                .to_dict(orient="records")
            )
        ],
    }

    with open(
        OUTPUT_JSON_FILE,
        "w",
        encoding="utf-8",
    ) as output:
        json.dump(
            payload,
            output,
            indent=2,
            ensure_ascii=False,
        )


def run_consolidation_agent():
    original_insights = load_and_prepare()

    consolidated = consolidate_insights(
        original_insights
    )

    summary = build_summary(
        original_insights,
        consolidated,
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

        consolidated.to_excel(
            writer,
            sheet_name="Consolidated Insights",
            index=False,
        )

        original_insights.to_excel(
            writer,
            sheet_name="Original Rule Insights",
            index=False,
        )

    write_json(summary, consolidated)

    result = summary.iloc[0]

    print()
    print("Insight Consolidation Agent completed.")
    print(
        f"Original rule insights: "
        f"{result['original_rule_insights']}"
    )
    print(
        f"Consolidated issues: "
        f"{result['consolidated_issues']}"
    )
    print(
        f"Repeated alerts removed: "
        f"{result['repeated_alerts_removed']}"
    )
    print(
        f"Critical issues: "
        f"{result['critical_issues']}"
    )
    print(
        f"High issues: "
        f"{result['high_issues']}"
    )
    print(
        f"Top issue: {result['top_issue']}"
    )
    print(f"Saved: {OUTPUT_FILE}")
    print(f"Saved: {OUTPUT_JSON_FILE}")
    print()


if __name__ == "__main__":
    run_consolidation_agent()