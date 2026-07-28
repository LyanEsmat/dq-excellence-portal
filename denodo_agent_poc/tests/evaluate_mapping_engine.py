from pathlib import Path
import sys

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

PREDICTED_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "bt_technical_mappings_v2.xlsx"
)

GROUND_TRUTH_FILE = (
    PROJECT_DIR
    / "data"
    / "reference"
    / "bt_mapping_ground_truth.xlsx"
)

EVALUATION_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "mapping_evaluation.xlsx"
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


def load_files():
    if not PREDICTED_FILE.exists():
        raise FileNotFoundError(
            f"Predicted mappings not found: "
            f"{PREDICTED_FILE}"
        )

    if not GROUND_TRUTH_FILE.exists():
        raise FileNotFoundError(
            f"Ground truth not found: "
            f"{GROUND_TRUTH_FILE}"
        )

    predicted = pd.read_excel(PREDICTED_FILE)
    ground_truth = pd.read_excel(
        GROUND_TRUTH_FILE
    )

    return predicted, ground_truth


def prepare_dataframes(
    predicted,
    ground_truth,
):
    for column in MAPPING_KEY:
        predicted[column] = (
            predicted[column]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        ground_truth[column] = (
            ground_truth[column]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

    predicted["predicted_mapping"] = True
    ground_truth["expected_mapping_flag"] = True

    return predicted, ground_truth


def evaluate_mappings(
    predicted,
    ground_truth,
):
    comparison = predicted.merge(
        ground_truth[
            MAPPING_KEY
            + [
                "business_unit",
                "expected_mapping_flag",
            ]
        ],
        on=MAPPING_KEY,
        how="outer",
        suffixes=(
            "_predicted",
            "_expected",
        ),
        indicator=True,
    )

    correct = comparison[
        comparison["_merge"] == "both"
    ].copy()

    incorrect = comparison[
        comparison["_merge"] == "left_only"
    ].copy()

    missing = comparison[
        comparison["_merge"] == "right_only"
    ].copy()

    true_positives = len(correct)
    false_positives = len(incorrect)
    false_negatives = len(missing)

    precision = percentage(
        true_positives,
        true_positives + false_positives,
    )

    recall = percentage(
        true_positives,
        true_positives + false_negatives,
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
        true_positives,
        len(ground_truth),
    )

    return {
        "comparison": comparison,
        "correct": correct,
        "incorrect": incorrect,
        "missing": missing,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "exact_accuracy": exact_accuracy,
    }


def build_bt_summary(
    predicted,
    ground_truth,
):
    business_terms = sorted(
        set(predicted["bt_id"])
        | set(ground_truth["bt_id"])
    )

    rows = []

    for bt_id in business_terms:
        predicted_bt = predicted[
            predicted["bt_id"] == bt_id
        ]

        expected_bt = ground_truth[
            ground_truth["bt_id"] == bt_id
        ]

        predicted_keys = set(
            predicted_bt[MAPPING_KEY]
            .apply(tuple, axis=1)
            .tolist()
        )

        expected_keys = set(
            expected_bt[MAPPING_KEY]
            .apply(tuple, axis=1)
            .tolist()
        )

        correct_count = len(
            predicted_keys & expected_keys
        )

        incorrect_count = len(
            predicted_keys - expected_keys
        )

        missing_count = len(
            expected_keys - predicted_keys
        )

        bt_name = ""

        if not predicted_bt.empty:
            bt_name = predicted_bt.iloc[0].get(
                "business_term_name",
                "",
            )

        rows.append(
            {
                "bt_id": bt_id.upper(),
                "business_term_name": bt_name,
                "expected_mappings": len(
                    expected_keys
                ),
                "predicted_mappings": len(
                    predicted_keys
                ),
                "correct_mappings": correct_count,
                "incorrect_mappings": (
                    incorrect_count
                ),
                "missing_mappings": missing_count,
                "mapping_accuracy": percentage(
                    correct_count,
                    len(expected_keys),
                ),
            }
        )

    return pd.DataFrame(rows)


def build_status_summary(predicted, correct):
    correct_keys = set(
        correct[MAPPING_KEY]
        .apply(tuple, axis=1)
        .tolist()
    )

    evaluation_rows = []

    for _, row in predicted.iterrows():
        key = tuple(
            row[column]
            for column in MAPPING_KEY
        )

        evaluation_rows.append(
            {
                "bt_id": row["bt_id"].upper(),
                "business_term_name": row[
                    "business_term_name"
                ],
                "schema_name": row["schema_name"],
                "table_name": row["table_name"],
                "column_name": row["column_name"],
                "mapping_score": row[
                    "mapping_score"
                ],
                "mapping_status": row[
                    "mapping_status"
                ],
                "is_correct": (
                    "YES"
                    if key in correct_keys
                    else "NO"
                ),
            }
        )

    return pd.DataFrame(evaluation_rows)


def main():
    predicted, ground_truth = load_files()

    predicted, ground_truth = prepare_dataframes(
        predicted,
        ground_truth,
    )

    evaluation = evaluate_mappings(
        predicted,
        ground_truth,
    )

    bt_summary = build_bt_summary(
        predicted,
        ground_truth,
    )

    status_summary = build_status_summary(
        predicted,
        evaluation["correct"],
    )

    summary = pd.DataFrame(
        [
            {
                "expected_mappings": len(
                    ground_truth
                ),
                "predicted_mappings": len(
                    predicted
                ),
                "correct_mappings": evaluation[
                    "true_positives"
                ],
                "incorrect_mappings": evaluation[
                    "false_positives"
                ],
                "missing_mappings": evaluation[
                    "false_negatives"
                ],
                "precision": evaluation[
                    "precision"
                ],
                "recall": evaluation["recall"],
                "f1_score": evaluation[
                    "f1_score"
                ],
                "exact_mapping_accuracy": evaluation[
                    "exact_accuracy"
                ],
                "business_terms_evaluated": (
                    bt_summary["bt_id"].nunique()
                ),
                "fully_correct_business_terms": int(
                    (
                        bt_summary[
                            "mapping_accuracy"
                        ]
                        == 100
                    ).sum()
                ),
            }
        ]
    )

    with pd.ExcelWriter(
        EVALUATION_FILE,
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

        status_summary.to_excel(
            writer,
            sheet_name="Mapping Assessment",
            index=False,
        )

        evaluation["correct"].to_excel(
            writer,
            sheet_name="Correct Mappings",
            index=False,
        )

        evaluation["incorrect"].to_excel(
            writer,
            sheet_name="Incorrect Mappings",
            index=False,
        )

        evaluation["missing"].to_excel(
            writer,
            sheet_name="Missing Mappings",
            index=False,
        )

    summary_row = summary.iloc[0]

    print()
    print("Mapping Evaluation completed.")
    print(
        f"Expected mappings: "
        f"{summary_row['expected_mappings']}"
    )
    print(
        f"Predicted mappings: "
        f"{summary_row['predicted_mappings']}"
    )
    print(
        f"Correct mappings: "
        f"{summary_row['correct_mappings']}"
    )
    print(
        f"Incorrect mappings: "
        f"{summary_row['incorrect_mappings']}"
    )
    print(
        f"Missing mappings: "
        f"{summary_row['missing_mappings']}"
    )
    print(
        f"Precision: "
        f"{summary_row['precision']}%"
    )
    print(
        f"Recall: "
        f"{summary_row['recall']}%"
    )
    print(
        f"F1 score: "
        f"{summary_row['f1_score']}%"
    )
    print(
        f"Exact mapping accuracy: "
        f"{summary_row['exact_mapping_accuracy']}%"
    )
    print(
        f"Fully correct Business Terms: "
        f"{summary_row['fully_correct_business_terms']}"
        f"/{summary_row['business_terms_evaluated']}"
    )
    print(f"Saved: {EVALUATION_FILE}")
    print()

    if (
        summary_row["expected_mappings"]
        != 63
    ):
        print(
            "WARNING: Expected mapping count "
            "should be 63."
        )

    if (
        summary_row["predicted_mappings"]
        != 63
    ):
        print(
            "WARNING: Predicted mapping count "
            "should be 63."
        )


if __name__ == "__main__":
    main()