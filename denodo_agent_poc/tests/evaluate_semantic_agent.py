from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

AGENT_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "agent_bt_technical_mappings.xlsx"
)

GROUND_TRUTH_FILE = (
    PROJECT_DIR
    / "data"
    / "reference"
    / "bt_mapping_ground_truth.xlsx"
)

OUTPUT_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "semantic_agent_evaluation.xlsx"
)


MAPPING_KEY = [
    "bt_id",
    "schema_name",
    "table_name",
    "column_name",
]


def percentage(numerator, denominator):
    if denominator == 0:
        return 0.0

    return round(
        (numerator / denominator) * 100,
        2,
    )


def normalize_columns(dataframe):
    dataframe = dataframe.copy()

    for column in MAPPING_KEY:
        dataframe[column] = (
            dataframe[column]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

    return dataframe


def main():
    if not AGENT_FILE.exists():
        raise FileNotFoundError(
            f"Agent mapping file missing: {AGENT_FILE}"
        )

    if not GROUND_TRUTH_FILE.exists():
        raise FileNotFoundError(
            f"Ground-truth file missing: "
            f"{GROUND_TRUTH_FILE}"
        )

    agent_mappings = normalize_columns(
        pd.read_excel(AGENT_FILE)
    )

    ground_truth = normalize_columns(
        pd.read_excel(GROUND_TRUTH_FILE)
    )

    agent_keys = set(
        agent_mappings[MAPPING_KEY]
        .apply(tuple, axis=1)
        .tolist()
    )

    expected_keys = set(
        ground_truth[MAPPING_KEY]
        .apply(tuple, axis=1)
        .tolist()
    )

    correct_keys = agent_keys & expected_keys
    incorrect_keys = agent_keys - expected_keys
    missing_keys = expected_keys - agent_keys

    correct = agent_mappings[
        agent_mappings[MAPPING_KEY]
        .apply(tuple, axis=1)
        .isin(correct_keys)
    ].copy()

    incorrect = agent_mappings[
        agent_mappings[MAPPING_KEY]
        .apply(tuple, axis=1)
        .isin(incorrect_keys)
    ].copy()

    missing = ground_truth[
        ground_truth[MAPPING_KEY]
        .apply(tuple, axis=1)
        .isin(missing_keys)
    ].copy()

    true_positive = len(correct_keys)
    false_positive = len(incorrect_keys)
    false_negative = len(missing_keys)

    precision = percentage(
        true_positive,
        true_positive + false_positive,
    )

    recall = percentage(
        true_positive,
        true_positive + false_negative,
    )

    if precision + recall == 0:
        f1_score = 0.0
    else:
        f1_score = round(
            2
            * precision
            * recall
            / (precision + recall),
            2,
        )

    exact_accuracy = percentage(
        true_positive,
        len(expected_keys),
    )

    baseline_accuracy = 95.24

    improvement = round(
        exact_accuracy - baseline_accuracy,
        2,
    )

    bt_rows = []

    for bt_id in sorted(
        set(agent_mappings["bt_id"])
        | set(ground_truth["bt_id"])
    ):
        predicted_bt = agent_mappings[
            agent_mappings["bt_id"] == bt_id
        ]

        expected_bt = ground_truth[
            ground_truth["bt_id"] == bt_id
        ]

        predicted_bt_keys = set(
            predicted_bt[MAPPING_KEY]
            .apply(tuple, axis=1)
            .tolist()
        )

        expected_bt_keys = set(
            expected_bt[MAPPING_KEY]
            .apply(tuple, axis=1)
            .tolist()
        )

        correct_count = len(
            predicted_bt_keys
            & expected_bt_keys
        )

        term_name = ""

        if not predicted_bt.empty:
            term_name = predicted_bt.iloc[0][
                "business_term_name"
            ]

        bt_rows.append(
            {
                "bt_id": bt_id.upper(),
                "business_term_name": term_name,
                "expected_mappings": len(
                    expected_bt_keys
                ),
                "agent_mappings": len(
                    predicted_bt_keys
                ),
                "correct_mappings": correct_count,
                "incorrect_mappings": len(
                    predicted_bt_keys
                    - expected_bt_keys
                ),
                "missing_mappings": len(
                    expected_bt_keys
                    - predicted_bt_keys
                ),
                "accuracy": percentage(
                    correct_count,
                    len(expected_bt_keys),
                ),
            }
        )

    bt_summary = pd.DataFrame(bt_rows)

    summary = pd.DataFrame(
        [
            {
                "expected_mappings": len(
                    expected_keys
                ),
                "agent_mappings": len(agent_keys),
                "correct_mappings": true_positive,
                "incorrect_mappings": false_positive,
                "missing_mappings": false_negative,
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
                "exact_mapping_accuracy": (
                    exact_accuracy
                ),
                "baseline_accuracy": (
                    baseline_accuracy
                ),
                "agent_improvement": improvement,
                "fully_correct_business_terms": int(
                    (
                        bt_summary["accuracy"]
                        == 100
                    ).sum()
                ),
                "business_terms_evaluated": len(
                    bt_summary
                ),
            }
        ]
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

        bt_summary.to_excel(
            writer,
            sheet_name="BT Accuracy",
            index=False,
        )

        correct.to_excel(
            writer,
            sheet_name="Correct Mappings",
            index=False,
        )

        incorrect.to_excel(
            writer,
            sheet_name="Incorrect Mappings",
            index=False,
        )

        missing.to_excel(
            writer,
            sheet_name="Missing Mappings",
            index=False,
        )

    result = summary.iloc[0]

    print()
    print("Semantic Agent Evaluation completed.")
    print(
        f"Expected mappings: "
        f"{result['expected_mappings']}"
    )
    print(
        f"Agent mappings: "
        f"{result['agent_mappings']}"
    )
    print(
        f"Correct mappings: "
        f"{result['correct_mappings']}"
    )
    print(
        f"Incorrect mappings: "
        f"{result['incorrect_mappings']}"
    )
    print(
        f"Missing mappings: "
        f"{result['missing_mappings']}"
    )
    print(
        f"Precision: {result['precision']}%"
    )
    print(f"Recall: {result['recall']}%")
    print(f"F1 score: {result['f1_score']}%")
    print(
        "Exact mapping accuracy: "
        f"{result['exact_mapping_accuracy']}%"
    )
    print(
        "Improvement over baseline: "
        f"{result['agent_improvement']} "
        "percentage points"
    )
    print(
        "Fully correct Business Terms: "
        f"{result['fully_correct_business_terms']}"
        f"/{result['business_terms_evaluated']}"
    )
    print(f"Saved: {OUTPUT_FILE}")
    print()


if __name__ == "__main__":
    main()