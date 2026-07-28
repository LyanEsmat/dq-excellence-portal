from pathlib import Path
import re
import unicodedata

import pandas as pd
from rapidfuzz import fuzz


PROJECT_DIR = Path(__file__).resolve().parents[1]

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

RESULTS_DIR = PROJECT_DIR / "data" / "results"

MAPPING_OUTPUT_FILE = (
    RESULTS_DIR
    / "bt_technical_mappings.xlsx"
)

CANDIDATE_OUTPUT_FILE = (
    RESULTS_DIR
    / "bt_mapping_candidates.xlsx"
)


SYNONYMS = {
    "identifier": {"id", "identifier", "number", "key"},
    "quantity": {"quantity", "amount", "volume", "tons", "output"},
    "amount": {"amount", "value", "budget", "salary"},
    "date": {"date", "timestamp", "time"},
    "owner": {"owner", "responsible"},
    "email": {"email", "mail"},
    "status": {"status", "state"},
    "business": {"business", "enterprise"},
    "unit": {"unit", "bu"},
    "updated": {"updated", "modified", "changed"},
    "record": {"record", "row", "entry"},
    "production": {"production", "output", "produced"},
    "extraction": {"extraction", "extracted", "mining"},
    "department": {"department", "dept"},
    "project": {"project", "initiative"},
    "order": {"order", "purchase"},
    "financial": {"financial", "finance", "transaction"},
}


def normalize_text(value):
    if pd.isna(value):
        return ""

    text = unicodedata.normalize(
        "NFKD",
        str(value),
    )

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    text = text.lower()
    text = text.replace("_", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)

    return " ".join(text.split())


def expand_tokens(text):
    tokens = set(normalize_text(text).split())
    expanded = set(tokens)

    for token in tokens:
        for synonym_group in SYNONYMS.values():
            if token in synonym_group:
                expanded.update(synonym_group)

    return expanded


def token_overlap_score(left_text, right_text):
    left_tokens = expand_tokens(left_text)
    right_tokens = expand_tokens(right_text)

    if not left_tokens or not right_tokens:
        return 0.0

    intersection = left_tokens & right_tokens
    union = left_tokens | right_tokens

    return (len(intersection) / len(union)) * 100


def calculate_mapping_score(
    business_term,
    technical_column,
):
    term_name = normalize_text(
        business_term["business_term_name"]
    )

    term_description = normalize_text(
        business_term["description"]
    )

    technical_name = normalize_text(
        technical_column["column_name"]
    )

    technical_description = normalize_text(
        technical_column["description"]
    )

    table_name = normalize_text(
        technical_column["table_name"]
    )

    technical_context = " ".join(
        [
            technical_name,
            technical_description,
            table_name,
            normalize_text(
                technical_column["business_unit"]
            ),
        ]
    )

    name_similarity = fuzz.token_set_ratio(
        term_name,
        technical_name,
    )

    context_similarity = fuzz.token_set_ratio(
        term_name,
        technical_context,
    )

    description_similarity = fuzz.token_set_ratio(
        term_description,
        technical_context,
    )

    overlap = token_overlap_score(
        f"{term_name} {term_description}",
        technical_context,
    )

    compact_term = term_name.replace(" ", "")
    compact_column = technical_name.replace(" ", "")

    compact_similarity = fuzz.ratio(
        compact_term,
        compact_column,
    )

    score = (
        name_similarity * 0.35
        + context_similarity * 0.25
        + description_similarity * 0.15
        + overlap * 0.15
        + compact_similarity * 0.10
    )

    term_business_unit = normalize_text(
        business_term["business_unit"]
    )

    technical_business_unit = normalize_text(
        technical_column["business_unit"]
    )

    if (
        term_business_unit != "enterprise"
        and term_business_unit
        == technical_business_unit
    ):
        score += 10

    if (
        term_business_unit != "enterprise"
        and term_business_unit
        != technical_business_unit
    ):
        score -= 30

    return round(
        min(100, max(0, score)),
        2,
    )


def determine_status(score, rank):
    if rank == 1 and score >= 65:
        return "Mapped"

    if score >= 50:
        return "Needs Review"

    return "Rejected"


def create_reason(
    business_term,
    technical_column,
    score,
    rank,
):
    business_unit = business_term["business_unit"]
    technical_unit = technical_column["business_unit"]

    if business_unit == "ENTERPRISE":
        scope_reason = (
            "Enterprise Business Term evaluated "
            "across all Business Units."
        )
    else:
        scope_reason = (
            f"Business Unit scope matched: "
            f"{business_unit} ↔ {technical_unit}."
        )

    return (
        f"{scope_reason} Candidate rank {rank}; "
        f"semantic and lexical score {score}%."
    )


def generate_candidates(
    business_terms,
    technical_metadata,
):
    candidates = []

    for _, business_term in business_terms.iterrows():
        business_unit = str(
            business_term["business_unit"]
        ).strip()

        if business_unit == "ENTERPRISE":
            eligible_columns = technical_metadata.copy()
        else:
            eligible_columns = technical_metadata[
                technical_metadata["business_unit"]
                == business_unit
            ].copy()

        scored_columns = []

        for _, technical_column in (
            eligible_columns.iterrows()
        ):
            score = calculate_mapping_score(
                business_term,
                technical_column,
            )

            scored_columns.append(
                {
                    "technical_column": technical_column,
                    "mapping_score": score,
                }
            )

        scored_columns.sort(
            key=lambda item: item["mapping_score"],
            reverse=True,
        )

        for rank, candidate in enumerate(
            scored_columns[:5],
            start=1,
        ):
            technical_column = candidate[
                "technical_column"
            ]

            score = candidate["mapping_score"]

            candidates.append(
                {
                    "bt_id": business_term["bt_id"],
                    "business_term_name": business_term[
                        "business_term_name"
                    ],
                    "business_term_description": (
                        business_term["description"]
                    ),
                    "bt_business_unit": business_unit,
                    "source_system": technical_column[
                        "source_system"
                    ],
                    "database_name": technical_column[
                        "database_name"
                    ],
                    "schema_name": technical_column[
                        "schema_name"
                    ],
                    "table_name": technical_column[
                        "table_name"
                    ],
                    "column_name": technical_column[
                        "column_name"
                    ],
                    "technical_description": (
                        technical_column["description"]
                    ),
                    "technical_business_unit": (
                        technical_column["business_unit"]
                    ),
                    "candidate_rank": rank,
                    "mapping_score": score,
                    "mapping_status": determine_status(
                        score,
                        rank,
                    ),
                    "mapping_reason": create_reason(
                        business_term,
                        technical_column,
                        score,
                        rank,
                    ),
                }
            )

    return pd.DataFrame(candidates)


def select_enterprise_mappings(
    business_term_candidates,
):
    selected = []

    for _, table_candidates in (
        business_term_candidates.groupby(
            [
                "schema_name",
                "table_name",
            ]
        )
    ):
        table_candidates = table_candidates.sort_values(
            by="mapping_score",
            ascending=False,
        )

        best_candidate = table_candidates.iloc[0]

        if best_candidate["mapping_score"] >= 50:
            candidate = best_candidate.copy()
            candidate["mapping_status"] = (
                "Mapped"
                if candidate["mapping_score"] >= 65
                else "Needs Review"
            )

            selected.append(candidate)

    return selected


def select_final_mappings(candidates):
    selected_rows = []

    for _, bt_candidates in candidates.groupby(
        "bt_id"
    ):
        business_unit = bt_candidates.iloc[0][
            "bt_business_unit"
        ]

        if business_unit == "ENTERPRISE":
            selected_rows.extend(
                select_enterprise_mappings(
                    bt_candidates
                )
            )
        else:
            sorted_candidates = (
                bt_candidates.sort_values(
                    by="mapping_score",
                    ascending=False,
                )
            )

            best_candidate = sorted_candidates.iloc[0]

            selected_rows.append(
                best_candidate.copy()
            )

    if not selected_rows:
        return pd.DataFrame(
            columns=candidates.columns
        )

    final_mappings = pd.DataFrame(selected_rows)

    final_mappings = final_mappings.sort_values(
        by=[
            "bt_id",
            "technical_business_unit",
            "table_name",
            "column_name",
        ]
    )

    final_mappings.insert(
        0,
        "mapping_id",
        [
            f"MAP-{index:05d}"
            for index in range(
                1,
                len(final_mappings) + 1,
            )
        ],
    )

    return final_mappings


def run_mapping_engine():
    if not BUSINESS_TERMS_FILE.exists():
        raise FileNotFoundError(
            f"Missing Business Terms file: "
            f"{BUSINESS_TERMS_FILE}"
        )

    if not TECHNICAL_METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Missing technical metadata file: "
            f"{TECHNICAL_METADATA_FILE}"
        )

    business_terms = pd.read_excel(
        BUSINESS_TERMS_FILE
    )

    technical_metadata = pd.read_excel(
        TECHNICAL_METADATA_FILE
    )

    candidates = generate_candidates(
        business_terms,
        technical_metadata,
    )

    final_mappings = select_final_mappings(
        candidates
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    candidates.to_excel(
        CANDIDATE_OUTPUT_FILE,
        index=False,
    )

    final_mappings.to_excel(
        MAPPING_OUTPUT_FILE,
        index=False,
    )

    mapped_count = int(
        (
            final_mappings["mapping_status"]
            == "Mapped"
        ).sum()
    )

    review_count = int(
        (
            final_mappings["mapping_status"]
            == "Needs Review"
        ).sum()
    )

    print()
    print("Technical mapping engine completed.")
    print(f"Business Terms: {len(business_terms)}")
    print(
        f"Technical columns: "
        f"{len(technical_metadata)}"
    )
    print(
        f"Candidate mappings generated: "
        f"{len(candidates)}"
    )
    print(
        f"Final mappings selected: "
        f"{len(final_mappings)}"
    )
    print(f"Mapped: {mapped_count}")
    print(f"Needs Review: {review_count}")
    print(f"Saved: {MAPPING_OUTPUT_FILE}")
    print(f"Saved: {CANDIDATE_OUTPUT_FILE}")
    print()


if __name__ == "__main__":
    run_mapping_engine()