from pathlib import Path
import re

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[2]

BUSINESS_TERMS_FILE = (
    PROJECT_DIR
    / "data"
    / "metadata"
    / "business_terms.xlsx"
)

TECHNICAL_METADATA_FILE = (
    PROJECT_DIR
    / "data"
    / "metadata"
    / "technical_metadata.xlsx"
)

CANDIDATE_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "bt_mapping_candidates_v2.xlsx"
)

AGENT_MAPPING_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "agent_bt_technical_mappings.xlsx"
)

AGENT_REASONING_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "agent_mapping_reasoning.xlsx"
)


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


def classify_business_term_role(
    term_name,
    description,
):
    text = normalize_text(
        f"{term_name} {description}"
    )

    if contains_any(
        text,
        {"email", "mail"},
    ):
        return "email"

    if (
        "last updated" in text
        or "updated timestamp" in text
        or "update timestamp" in text
    ):
        return "timestamp"

    if contains_any(
        text,
        {"identifier", "identification", "id", "key"},
    ):
        return "identifier"

    if contains_any(
        text,
        {"date", "day"},
    ):
        return "date"

    if contains_any(
        text,
        {"status", "state"},
    ):
        return "status"

    if contains_any(
        text,
        {
            "amount",
            "value",
            "quantity",
            "volume",
            "tons",
            "output",
            "salary",
            "budget",
        },
    ):
        return "measure"

    if contains_any(
        text,
        {
            "grade",
            "category",
            "type",
            "phase",
            "family",
            "classification",
        },
    ):
        return "category"

    if contains_any(
        text,
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

    return "unknown"


def classify_column_role(
    column_name,
    data_type,
):
    column = normalize_text(column_name)
    data_type = normalize_text(data_type)

    if "email" in column:
        return "email"

    if column == "last updated":
        return "timestamp"

    if column.endswith(" id"):
        return "identifier"

    if (
        column.endswith(" date")
        or column == "date"
    ):
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
        or "number" in data_type
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

    return "unknown"


def calculate_role_adjustment(
    term_role,
    column_role,
):
    if term_role == column_role:
        return 30

    if term_role == "unknown":
        return 0

    if column_role == "unknown":
        return -5

    compatible_roles = {
        ("timestamp", "date"),
        ("date", "timestamp"),
        ("category", "code"),
        ("code", "category"),
    }

    if (
        term_role,
        column_role,
    ) in compatible_roles:
        return 5

    severe_conflicts = {
        ("measure", "identifier"),
        ("measure", "date"),
        ("measure", "timestamp"),
        ("identifier", "measure"),
        ("identifier", "date"),
        ("date", "identifier"),
        ("date", "measure"),
        ("email", "identifier"),
        ("email", "measure"),
        ("status", "measure"),
    }

    if (
        term_role,
        column_role,
    ) in severe_conflicts:
        return -45

    return -20


def merge_candidate_metadata(
    candidates,
    technical_metadata,
):
    metadata_columns = technical_metadata[
        [
            "source_system",
            "schema_name",
            "table_name",
            "column_name",
            "data_type",
        ]
    ].drop_duplicates()

    return candidates.merge(
        metadata_columns,
        on=[
            "source_system",
            "schema_name",
            "table_name",
            "column_name",
        ],
        how="left",
    )


def reason_about_candidates(
    business_terms,
    candidates,
):
    term_lookup = business_terms.set_index(
        "bt_id"
    ).to_dict(orient="index")

    reasoning_rows = []

    for _, candidate in candidates.iterrows():
        bt_id = candidate["bt_id"]
        business_term = term_lookup[bt_id]

        term_role = classify_business_term_role(
            business_term[
                "business_term_name"
            ],
            business_term["description"],
        )

        column_role = classify_column_role(
            candidate["column_name"],
            candidate.get("data_type", ""),
        )

        role_adjustment = calculate_role_adjustment(
            term_role,
            column_role,
        )

        original_score = float(
            candidate["mapping_score"]
        )

        semantic_score = round(
            min(
                100,
                max(
                    0,
                    original_score
                    + role_adjustment,
                ),
            ),
            2,
        )

        if term_role == column_role:
            compatibility = "Compatible"
            explanation = (
                f"The Business Term requires a "
                f"{term_role} field and the candidate "
                f"column has the same semantic role."
            )
        elif role_adjustment <= -20:
            compatibility = "Conflict"
            explanation = (
                f"The Business Term requires a "
                f"{term_role} field, but the candidate "
                f"column represents {column_role}."
            )
        else:
            compatibility = "Partial"
            explanation = (
                f"The Business Term role {term_role} "
                f"is partially compatible with the "
                f"candidate role {column_role}."
            )

        reasoning_row = candidate.to_dict()

        reasoning_row.update(
            {
                "term_semantic_role": term_role,
                "column_semantic_role": column_role,
                "role_compatibility": compatibility,
                "role_adjustment": role_adjustment,
                "agent_semantic_score": semantic_score,
                "agent_explanation": explanation,
            }
        )

        reasoning_rows.append(reasoning_row)

    return pd.DataFrame(reasoning_rows)


def select_agent_mappings(reasoning):
    selected_rows = []

    for _, bt_candidates in reasoning.groupby(
        "bt_id"
    ):
        business_unit = bt_candidates.iloc[0][
            "bt_business_unit"
        ]

        if business_unit == "ENTERPRISE":
            grouped_candidates = (
                bt_candidates.groupby(
                    [
                        "schema_name",
                        "table_name",
                    ]
                )
            )

            for _, table_candidates in (
                grouped_candidates
            ):
                selected_rows.append(
                    table_candidates
                    .sort_values(
                        by=[
                            "agent_semantic_score",
                            "mapping_score",
                        ],
                        ascending=False,
                    )
                    .iloc[0]
                    .copy()
                )

        else:
            selected_rows.append(
                bt_candidates
                .sort_values(
                    by=[
                        "agent_semantic_score",
                        "mapping_score",
                    ],
                    ascending=False,
                )
                .iloc[0]
                .copy()
            )

    mappings = pd.DataFrame(selected_rows)

    mappings = mappings.sort_values(
        by=[
            "bt_id",
            "technical_business_unit",
            "schema_name",
            "table_name",
            "column_name",
        ]
    ).reset_index(drop=True)

    mappings["agent_decision"] = mappings[
        "agent_semantic_score"
    ].apply(
        lambda score: (
            "Approved"
            if score >= 75
            else (
                "Needs Review"
                if score >= 55
                else "Rejected"
            )
        )
    )

    mappings.insert(
        0,
        "agent_mapping_id",
        [
            f"AGENT-MAP-{index:05d}"
            for index in range(
                1,
                len(mappings) + 1,
            )
        ],
    )

    return mappings


def run_semantic_mapping_agent():
    for required_file in [
        BUSINESS_TERMS_FILE,
        TECHNICAL_METADATA_FILE,
        CANDIDATE_FILE,
    ]:
        if not required_file.exists():
            raise FileNotFoundError(
                f"Required file not found: "
                f"{required_file}"
            )

    business_terms = pd.read_excel(
        BUSINESS_TERMS_FILE
    )

    technical_metadata = pd.read_excel(
        TECHNICAL_METADATA_FILE
    )

    candidates = pd.read_excel(
        CANDIDATE_FILE
    )

    candidates = merge_candidate_metadata(
        candidates,
        technical_metadata,
    )

    reasoning = reason_about_candidates(
        business_terms,
        candidates,
    )

    agent_mappings = select_agent_mappings(
        reasoning
    )

    reasoning.to_excel(
        AGENT_REASONING_FILE,
        index=False,
    )

    agent_mappings.to_excel(
        AGENT_MAPPING_FILE,
        index=False,
    )

    approved = int(
        (
            agent_mappings["agent_decision"]
            == "Approved"
        ).sum()
    )

    needs_review = int(
        (
            agent_mappings["agent_decision"]
            == "Needs Review"
        ).sum()
    )

    rejected = int(
        (
            agent_mappings["agent_decision"]
            == "Rejected"
        ).sum()
    )

    print()
    print("Semantic Mapping Agent completed.")
    print(
        f"Candidate mappings reviewed: "
        f"{len(reasoning)}"
    )
    print(
        f"Final agent mappings: "
        f"{len(agent_mappings)}"
    )
    print(f"Approved: {approved}")
    print(f"Needs Review: {needs_review}")
    print(f"Rejected: {rejected}")
    print(f"Saved: {AGENT_MAPPING_FILE}")
    print(f"Saved: {AGENT_REASONING_FILE}")
    print()


if __name__ == "__main__":
    run_semantic_mapping_agent()