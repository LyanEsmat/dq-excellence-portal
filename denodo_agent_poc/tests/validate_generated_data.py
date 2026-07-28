from pathlib import Path
import sys

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

SOURCE_DIR = PROJECT_DIR / "data" / "source"
METADATA_DIR = PROJECT_DIR / "data" / "metadata"
REFERENCE_DIR = PROJECT_DIR / "data" / "reference"

EXPECTED_FILES = {
    "pho_source.xlsx": "PHO",
    "alu_source.xlsx": "ALU",
    "pro_source.xlsx": "PRO",
    "ggm_source.xlsx": "GGM",
    "fin_source.xlsx": "FIN",
    "hr_source.xlsx": "HR",
    "pde_source.xlsx": "PDE",
}

EXPECTED_ROWS_PER_FILE = 8000
EXPECTED_COLUMNS_PER_FILE = 9
EXPECTED_TOTAL_ROWS = 56000
EXPECTED_METADATA_ROWS = 63

EXPECTED_DIMENSIONS = {
    "Completeness",
    "Validity",
    "Accuracy",
    "Consistency",
    "Uniqueness",
    "Timeliness",
}


def fail(message):
    print(f"FAILED: {message}")
    sys.exit(1)


def validate_source_files():
    total_rows = 0

    print("Validating source datasets...")

    for file_name, business_unit in EXPECTED_FILES.items():
        file_path = SOURCE_DIR / file_name

        if not file_path.exists():
            fail(f"Missing source file: {file_path}")

        dataframe = pd.read_excel(file_path)

        row_count = len(dataframe)
        column_count = len(dataframe.columns)

        if row_count != EXPECTED_ROWS_PER_FILE:
            fail(
                f"{file_name} contains {row_count} rows; "
                f"expected {EXPECTED_ROWS_PER_FILE}."
            )

        if column_count != EXPECTED_COLUMNS_PER_FILE:
            fail(
                f"{file_name} contains {column_count} columns; "
                f"expected {EXPECTED_COLUMNS_PER_FILE}."
            )

        if "business_unit" not in dataframe.columns:
            fail(
                f"{file_name} is missing business_unit."
            )

        actual_units = set(
            dataframe["business_unit"]
            .dropna()
            .astype(str)
            .unique()
        )

        if actual_units != {business_unit}:
            fail(
                f"{file_name} contains unexpected "
                f"Business Units: {actual_units}"
            )

        total_rows += row_count

        print(
            f"PASSED: {business_unit} — "
            f"{row_count:,} rows, "
            f"{column_count} columns"
        )

    if total_rows != EXPECTED_TOTAL_ROWS:
        fail(
            f"Total source rows are {total_rows}; "
            f"expected {EXPECTED_TOTAL_ROWS}."
        )

    print(
        f"PASSED: Total source rows — "
        f"{total_rows:,}"
    )


def validate_metadata():
    metadata_file = (
        METADATA_DIR
        / "technical_metadata.xlsx"
    )

    summary_file = (
        METADATA_DIR
        / "generation_summary.xlsx"
    )

    if not metadata_file.exists():
        fail("technical_metadata.xlsx is missing.")

    if not summary_file.exists():
        fail("generation_summary.xlsx is missing.")

    metadata = pd.read_excel(metadata_file)
    summary = pd.read_excel(summary_file)

    required_metadata_columns = {
        "source_system",
        "database_name",
        "schema_name",
        "table_name",
        "column_name",
        "data_type",
        "nullable",
        "business_unit",
        "description",
    }

    missing_columns = (
        required_metadata_columns
        - set(metadata.columns)
    )

    if missing_columns:
        fail(
            "Technical metadata is missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    if len(metadata) != EXPECTED_METADATA_ROWS:
        fail(
            f"Technical metadata contains "
            f"{len(metadata)} rows; "
            f"expected {EXPECTED_METADATA_ROWS}."
        )

    if len(summary) != len(EXPECTED_FILES):
        fail(
            "Generation summary must contain "
            "one row per Business Unit."
        )

    if int(summary["row_count"].sum()) != EXPECTED_TOTAL_ROWS:
        fail(
            "Generation summary total does not equal "
            f"{EXPECTED_TOTAL_ROWS}."
        )

    print(
        f"PASSED: Technical metadata — "
        f"{len(metadata)} columns documented"
    )


def validate_reference_data():
    reference_file = (
        REFERENCE_DIR
        / "reference_data.xlsx"
    )

    manifest_file = (
        REFERENCE_DIR
        / "expected_defect_manifest.xlsx"
    )

    if not reference_file.exists():
        fail("reference_data.xlsx is missing.")

    if not manifest_file.exists():
        fail(
            "expected_defect_manifest.xlsx is missing."
        )

    reference_data = pd.read_excel(reference_file)
    manifest = pd.read_excel(manifest_file)

    required_reference_columns = {
        "business_unit",
        "reference_type",
        "approved_value",
    }

    if not required_reference_columns.issubset(
        reference_data.columns
    ):
        fail(
            "Reference data has an invalid structure."
        )

    required_manifest_columns = {
        "business_unit",
        "source_row",
        "record_id",
        "column_name",
        "dq_dimension",
        "expected_issue",
    }

    if not required_manifest_columns.issubset(
        manifest.columns
    ):
        fail(
            "Defect manifest has an invalid structure."
        )

    found_dimensions = set(
        manifest["dq_dimension"]
        .dropna()
        .astype(str)
        .unique()
    )

    missing_dimensions = (
        EXPECTED_DIMENSIONS - found_dimensions
    )

    if missing_dimensions:
        fail(
            "Defect manifest does not contain: "
            + ", ".join(sorted(missing_dimensions))
        )

    if manifest.empty:
        fail("Defect manifest is empty.")

    print(
        f"PASSED: Reference data — "
        f"{len(reference_data):,} approved values"
    )

    print(
        f"PASSED: Defect manifest — "
        f"{len(manifest):,} expected defects"
    )

    print(
        "PASSED: All six DQ dimensions are represented"
    )


def main():
    print()
    print("Enterprise Dummy Data Validation")
    print("=" * 40)

    validate_source_files()
    validate_metadata()
    validate_reference_data()

    print("=" * 40)
    print("ALL VALIDATION CHECKS PASSED")
    print()


if __name__ == "__main__":
    main()