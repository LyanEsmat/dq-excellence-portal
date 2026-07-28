from pathlib import Path
import json

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[2]

RULE_FILE = (
    PROJECT_DIR
    / "data"
    / "results"
    / "dq_rule_registry.xlsx"
)


def repair_email_rule():
    if not RULE_FILE.exists():
        raise FileNotFoundError(
            f"Rule registry not found: {RULE_FILE}"
        )

    registry = pd.read_excel(
        RULE_FILE,
        sheet_name="Rule Registry",
    )

    email_mask = (
        registry["rule_type"]
        == "email_format"
    )

    email_rule_count = int(email_mask.sum())

    correct_parameters = json.dumps(
        {
            "pattern": (
                r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
            )
        }
    )

    registry.loc[
        email_mask,
        "rule_parameters",
    ] = correct_parameters

    applicable = registry[
        registry["applicability"]
        == "Applicable"
    ]

    not_applicable = registry[
        registry["applicability"]
        == "Not Applicable"
    ]

    with pd.ExcelWriter(
        RULE_FILE,
        engine="openpyxl",
    ) as writer:
        registry.to_excel(
            writer,
            sheet_name="Rule Registry",
            index=False,
        )

        applicable.to_excel(
            writer,
            sheet_name="Applicable Rules",
            index=False,
        )

        not_applicable.to_excel(
            writer,
            sheet_name="Not Applicable",
            index=False,
        )

    print()
    print("Email rule repaired successfully.")
    print(
        f"Email-format rules updated: "
        f"{email_rule_count}"
    )
    print(
        f"Correct pattern: "
        f"{correct_parameters}"
    )
    print(f"Saved: {RULE_FILE}")
    print()


if __name__ == "__main__":
    repair_email_rule()