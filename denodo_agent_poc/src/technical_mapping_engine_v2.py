from pathlib import Path

import pandas as pd

import technical_mapping_engine as mapping_v1


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
    / "bt_technical_mappings_v2.xlsx"
)

CANDIDATE_OUTPUT_FILE = (
    RESULTS_DIR
    / "bt_mapping_candidates_v2.xlsx"
)


def create_candidate_row(
    business_term,
    technical_column,
    score,
    rank,
):
    status = mapping_v1.determine_status(
        score,
        rank,
    )

    return {
        "bt_id": business_term["bt_id"],
        "business_term_name": business_term[
            "business_term_name"
        ],
        "business_term_description": business_term[
            "description"
        ],
        "bt_business_unit": business_term[
            "business_unit"
        ],
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
        "technical_description": technical_column[
            "description"
        ],
        "technical_business_unit": technical_column[
            "business_unit"
        ],
        "candidate_rank": rank,
        "mapping_score": score,
        "mapping_status": status,
        "mapping_reason": mapping_v1.create_reason(
            business_term,
            technical_column,
            score,
            rank,
        ),
    }


def score_columns(
    business_term,
    technical_columns,
):
    scored = []

    for _, technical_column in (
        technical_columns.iterrows()
    ):
        score = mapping_v1.calculate_mapping_score(
            business_term,
            technical_column,
        )

        scored.append(
            {
                "technical_column": technical_column,
                "score": score,
            }
        )

    scored.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return scored


def generate_enterprise_candidates(
    business_term,
    technical_metadata,
):
    candidates = []

    grouped_metadata = technical_metadata.groupby(
        [
            "schema_name",
            "table_name",
        ]
    )

    for _, table_columns in grouped_metadata:
        scored_columns = score_columns(
            business_term,
            table_columns,
        )

        # Keep the best three candidates from every
        # technical table, not five globally.
        for rank, candidate in enumerate(
            scored_columns[:3],
            start=1,
        ):
            candidates.append(
                create_candidate_row(
                    business_term,
                    candidate["technical_column"],
                    candidate["score"],
                    rank,
                )
            )

    return candidates


def generate_domain_candidates(
    business_term,
    technical_metadata,
):
    business_unit = business_term[
        "business_unit"
    ]

    eligible_columns = technical_metadata[
        technical_metadata["business_unit"]
        == business_unit
    ]

    scored_columns = score_columns(
        business_term,
        eligible_columns,
    )

    candidates = []

    for rank, candidate in enumerate(
        scored_columns[:5],
        start=1,
    ):
        candidates.append(
            create_candidate_row(
                business_term,
                candidate["technical_column"],
                candidate["score"],
                rank,
            )
        )

    return candidates


def generate_candidates(
    business_terms,
    technical_metadata,
):
    all_candidates = []

    for _, business_term in (
        business_terms.iterrows()
    ):
        if (
            business_term["business_unit"]
            == "ENTERPRISE"
        ):
            all_candidates.extend(
                generate_enterprise_candidates(
                    business_term,
                    technical_metadata,
                )
            )
        else:
            all_candidates.extend(
                generate_domain_candidates(
                    business_term,
                    technical_metadata,
                )
            )

    return pd.DataFrame(all_candidates)


def select_final_mappings(candidates):
    selected_rows = []

    for _, bt_candidates in candidates.groupby(
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
                best_candidate = (
                    table_candidates
                    .sort_values(
                        by="mapping_score",
                        ascending=False,
                    )
                    .iloc[0]
                    .copy()
                )

                best_candidate["mapping_status"] = (
                    "Mapped"
                    if best_candidate[
                        "mapping_score"
                    ] >= 65
                    else "Needs Review"
                )

                selected_rows.append(
                    best_candidate
                )

        else:
            best_candidate = (
                bt_candidates
                .sort_values(
                    by="mapping_score",
                    ascending=False,
                )
                .iloc[0]
                .copy()
            )

            best_candidate["mapping_status"] = (
                "Mapped"
                if best_candidate[
                    "mapping_score"
                ] >= 65
                else "Needs Review"
            )

            selected_rows.append(
                best_candidate
            )

    final_mappings = pd.DataFrame(
        selected_rows
    )

    final_mappings = final_mappings.sort_values(
        by=[
            "bt_id",
            "technical_business_unit",
            "table_name",
            "column_name",
        ]
    ).reset_index(drop=True)

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


def run_mapping_engine_v2():
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

    mapped = int(
        (
            final_mappings["mapping_status"]
            == "Mapped"
        ).sum()
    )

    needs_review = int(
        (
            final_mappings["mapping_status"]
            == "Needs Review"
        ).sum()
    )

    print()
    print("Technical Mapping Engine V2 completed.")
    print(f"Business Terms: {len(business_terms)}")
    print(
        f"Technical columns: "
        f"{len(technical_metadata)}"
    )
    print(
        f"Candidate mappings: "
        f"{len(candidates)}"
    )
    print(
        f"Final mappings selected: "
        f"{len(final_mappings)}"
    )
    print(f"Mapped: {mapped}")
    print(f"Needs Review: {needs_review}")
    print(f"Saved: {MAPPING_OUTPUT_FILE}")
    print()


if __name__ == "__main__":
    run_mapping_engine_v2()