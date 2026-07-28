from pathlib import Path
import json
import re

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[2]

MAPPINGS_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "agent_bt_technical_mappings.xlsx"
)

REFERENCE_FILE = (
    PROJECT_DIR
    / "data"
    / "reference"
    / "reference_data.xlsx"
)

RULE_REGISTRY_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_rule_registry.xlsx"
)

RULE_SUMMARY_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_rule_planning_summary.xlsx"
)


DIMENSIONS = [
    "Completeness",
    "Validity",
    "Accuracy",
    "Consistency",
    "Uniqueness",
    "Timeliness",
]


def normalize_text(value):
    if pd.isna(value):
        return ""

    text = str(value).lower()
    text = text.replace("_", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)

    return " ".join(text.split())


def contains_any(text, words):
    tokens = set(normalize_text(text).split())

    return bool(tokens & set(words))


def classify_role(column_name, data_type):
    column = normalize_text(column_name)
    data_type = normalize_text(data_type)

    if "email" in column:
        return "email"

    if column == "last updated":
        return "timestamp"

    if column.endswith(" id"):
        return "identifier"

    if column.endswith(" date"):
        return "date"

    if "status" in column:
        return "status"

    if contains_any(
        column,
        {
            "amount",
            "value",
            "quantity",
            "tons",
            "output",
            "salary",
            "budget",
        },
    ):
        return "measure"

    if (
        "decimal" in data_type
        or "numeric" in data_type
    ):
        return "measure"

    if contains_any(
        column,
        {
            "grade",
            "category",
            "type",
            "phase",
            "family",
        },
    ):
        return "category"

    if contains_any(
        column,
        {
            "code",
            "unit",
            "department",
            "center",
            "vendor",
            "site",
            "mine",
            "smelter",
        },
    ):
        return "code"

    return "text"


def reference_values_for(
    reference_data,
    business_unit,
    column_name,
):
    matches = reference_data[
        (
            reference_data["business_unit"]
            == business_unit
        )
        & (
            reference_data["reference_type"]
            == column_name
        )
    ]

    return (
        matches["approved_value"]
        .dropna()
        .astype(str)
        .tolist()
    )


def create_plan(
    dimension,
    role,
    mapping,
    reference_values,
):
    column_name = mapping["column_name"]
    criticality = mapping.get(
        "criticality",
        "High",
    )

    base = {
        "dq_dimension": dimension,
        "target_column": column_name,
        "supporting_column": "",
        "applicability": "Applicable",
        "planning_status": "Ready",
        "rule_type": "",
        "rule_parameters": "{}",
        "severity": (
            "Critical"
            if criticality
            in {"Critical", "Restricted"}
            else "High"
        ),
        "planning_reason": "",
    }

    if dimension == "Completeness":
        base.update(
            {
                "rule_type": "not_null",
                "planning_reason": (
                    "Completeness applies because the "
                    "mapped Business Term requires a "
                    "populated technical value."
                ),
            }
        )

        return base

    if dimension == "Validity":
        if role == "email":
            base.update(
                {
                    "rule_type": "email_format",
                    "rule_parameters": json.dumps(
                        {
                            "pattern": (
                                r"^[^@\\s]+@[^@\\s]+\\."
                                r"[^@\\s]+$"
                            )
                        }
                    ),
                    "planning_reason": (
                        "Email values must follow a "
                        "valid corporate email format."
                    ),
                }
            )

        elif role == "measure":
            base.update(
                {
                    "rule_type": "numeric_minimum",
                    "rule_parameters": json.dumps(
                        {"minimum": 0}
                    ),
                    "planning_reason": (
                        "Numeric business measures cannot "
                        "contain negative values."
                    ),
                }
            )

        elif role == "identifier":
            base.update(
                {
                    "rule_type": "identifier_format",
                    "rule_parameters": json.dumps(
                        {
                            "pattern": (
                                r"^[A-Z]+-[0-9]{7}$"
                            )
                        }
                    ),
                    "planning_reason": (
                        "Identifiers must follow the "
                        "approved prefix-number format."
                    ),
                }
            )

        elif role in {"date", "timestamp"}:
            base.update(
                {
                    "rule_type": "valid_date",
                    "planning_reason": (
                        "Date values must be interpretable "
                        "as valid dates."
                    ),
                }
            )

        elif reference_values:
            base.update(
                {
                    "rule_type": "allowed_values",
                    "rule_parameters": json.dumps(
                        {
                            "allowed_values": (
                                reference_values
                            )
                        }
                    ),
                    "planning_reason": (
                        "The value must be present in the "
                        "approved reference-value list."
                    ),
                }
            )

        else:
            base.update(
                {
                    "rule_type": "non_blank_text",
                    "planning_reason": (
                        "Text values must contain usable "
                        "non-whitespace content."
                    ),
                }
            )

        return base

    if dimension == "Accuracy":
        if reference_values:
            base.update(
                {
                    "rule_type": "reference_match",
                    "rule_parameters": json.dumps(
                        {
                            "approved_values": (
                                reference_values
                            )
                        }
                    ),
                    "planning_reason": (
                        "Accuracy can be verified against "
                        "approved reference data."
                    ),
                }
            )

        elif role == "email":
            base.update(
                {
                    "rule_type": "corporate_email_domain",
                    "rule_parameters": json.dumps(
                        {
                            "accepted_domain": (
                                "dummy-company.com"
                            )
                        }
                    ),
                    "planning_reason": (
                        "Email accuracy can be assessed "
                        "against the approved corporate "
                        "domain."
                    ),
                }
            )

        else:
            base.update(
                {
                    "applicability": "Not Applicable",
                    "planning_status": "Not Applicable",
                    "rule_type": "",
                    "planning_reason": (
                        "No trusted reference source is "
                        "available to verify the accuracy "
                        "of this technical value."
                    ),
                }
            )

        return base

    if dimension == "Consistency":
        if role in {
            "code",
            "category",
            "status",
            "email",
        }:
            base.update(
                {
                    "rule_type": "normalized_format",
                    "rule_parameters": json.dumps(
                        {
                            "trim_whitespace": True,
                            "expected_case": (
                                "lower"
                                if role == "email"
                                else "upper"
                            ),
                        }
                    ),
                    "planning_reason": (
                        "The value has an expected casing "
                        "and whitespace convention."
                    ),
                }
            )

        else:
            base.update(
                {
                    "applicability": "Not Applicable",
                    "planning_status": "Not Applicable",
                    "rule_type": "",
                    "planning_reason": (
                        "No cross-field or formatting "
                        "consistency requirement is defined "
                        "for this semantic role."
                    ),
                }
            )

        return base

    if dimension == "Uniqueness":
        if role == "identifier":
            base.update(
                {
                    "rule_type": "unique_value",
                    "planning_reason": (
                        "Identifier Business Terms must "
                        "uniquely identify source records."
                    ),
                }
            )

        else:
            base.update(
                {
                    "applicability": "Not Applicable",
                    "planning_status": "Not Applicable",
                    "rule_type": "",
                    "planning_reason": (
                        "This Business Term is not a "
                        "record identifier and is not "
                        "expected to be unique."
                    ),
                }
            )

        return base

    if dimension == "Timeliness":
        supporting_column = (
            column_name
            if role == "timestamp"
            else "last_updated"
        )

        base.update(
            {
                "target_column": column_name,
                "supporting_column": supporting_column,
                "rule_type": "maximum_age_days",
                "rule_parameters": json.dumps(
                    {"maximum_age_days": 365}
                ),
                "planning_reason": (
                    "Timeliness is assessed using the "
                    "record's last-updated timestamp."
                ),
            }
        )

        return base

    raise ValueError(
        f"Unsupported DQ dimension: {dimension}"
    )


def run_rule_planning_agent():
    if not MAPPINGS_FILE.exists():
        raise FileNotFoundError(
            f"Agent mappings were not found: "
            f"{MAPPINGS_FILE}"
        )

    if not REFERENCE_FILE.exists():
        raise FileNotFoundError(
            f"Reference data was not found: "
            f"{REFERENCE_FILE}"
        )

    mappings = pd.read_excel(MAPPINGS_FILE)
    reference_data = pd.read_excel(
        REFERENCE_FILE
    )

    rule_rows = []
    rule_number = 1

    for _, mapping in mappings.iterrows():
        role = classify_role(
            mapping["column_name"],
            mapping.get("data_type", ""),
        )

        reference_values = reference_values_for(
            reference_data,
            mapping["technical_business_unit"],
            mapping["column_name"],
        )

        for dimension in DIMENSIONS:
            plan = create_plan(
                dimension,
                role,
                mapping,
                reference_values,
            )

            rule_rows.append(
                {
                    "rule_id": (
                        f"DQ-{rule_number:05d}"
                    ),
                    "agent_mapping_id": mapping[
                        "agent_mapping_id"
                    ],
                    "bt_id": mapping["bt_id"],
                    "business_term_name": mapping[
                        "business_term_name"
                    ],
                    "business_unit": mapping[
                        "technical_business_unit"
                    ],
                    "source_system": mapping[
                        "source_system"
                    ],
                    "schema_name": mapping[
                        "schema_name"
                    ],
                    "table_name": mapping[
                        "table_name"
                    ],
                    "column_name": mapping[
                        "column_name"
                    ],
                    "semantic_role": role,
                    **plan,
                }
            )

            rule_number += 1

    registry = pd.DataFrame(rule_rows)

    applicable = int(
        (
            registry["applicability"]
            == "Applicable"
        ).sum()
    )

    not_applicable = int(
        (
            registry["applicability"]
            == "Not Applicable"
        ).sum()
    )

    summary_rows = []

    for dimension in DIMENSIONS:
        group = registry[
            registry["dq_dimension"]
            == dimension
        ]

        summary_rows.append(
            {
                "dq_dimension": dimension,
                "total_assessments": len(group),
                "applicable_rules": int(
                    (
                        group["applicability"]
                        == "Applicable"
                    ).sum()
                ),
                "not_applicable_rules": int(
                    (
                        group["applicability"]
                        == "Not Applicable"
                    ).sum()
                ),
            }
        )

    summary = pd.DataFrame(summary_rows)

    with pd.ExcelWriter(
        RULE_REGISTRY_FILE,
        engine="openpyxl",
    ) as writer:
        registry.to_excel(
            writer,
            sheet_name="Rule Registry",
            index=False,
        )

        registry[
            registry["applicability"]
            == "Applicable"
        ].to_excel(
            writer,
            sheet_name="Applicable Rules",
            index=False,
        )

        registry[
            registry["applicability"]
            == "Not Applicable"
        ].to_excel(
            writer,
            sheet_name="Not Applicable",
            index=False,
        )

    summary.to_excel(
        RULE_SUMMARY_FILE,
        index=False,
    )

    print()
    print("DQ Rule Planning Agent completed.")
    print(f"Physical mappings: {len(mappings)}")
    print(
        f"Dimensions per mapping: "
        f"{len(DIMENSIONS)}"
    )
    print(
        f"Total rule assessments: "
        f"{len(registry)}"
    )
    print(f"Applicable rules: {applicable}")
    print(
        f"Not Applicable: {not_applicable}"
    )
    print(f"Saved: {RULE_REGISTRY_FILE}")
    print(f"Saved: {RULE_SUMMARY_FILE}")
    print()

    print("Dimension planning summary:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    run_rule_planning_agent()