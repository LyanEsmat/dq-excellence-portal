import re
import unicodedata
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz


BASE_DIR = Path(__file__).resolve().parent
DUMMY_DATA_DIR = BASE_DIR / "dummy_data"
OUTPUT_DIR = BASE_DIR / "outputs"

OUTPUT_DIR.mkdir(exist_ok=True)

BUSINESS_TERMS_PATH = DUMMY_DATA_DIR / "business_terms.xlsx"
OUTPUT_PATH = OUTPUT_DIR / "business_term_steward_mapping.xlsx"

MATCHED_THRESHOLD = 90
REVIEW_THRESHOLD = 75


def locate_metadata_file():
    possible_files = [
        DUMMY_DATA_DIR / "steward_metadata.xlsx",
        DUMMY_DATA_DIR / "active_directory.xlsx",
        DUMMY_DATA_DIR / "metadata.xlsx",
    ]

    for file_path in possible_files:
        if file_path.exists():
            return file_path

    raise FileNotFoundError(
        "No steward metadata file was found. Expected one of: "
        "steward_metadata.xlsx, active_directory.xlsx or metadata.xlsx."
    )


def remove_diacritics(value):
    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )


def normalize_name(value):
    if pd.isna(value) or value is None:
        return ""

    text = str(value).strip().lower()
    text = remove_diacritics(text)

    text = re.sub(
        r"[^a-z0-9\u0600-\u06FF\s]",
        " ",
        text,
    )

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def compact_name(value):
    return normalize_name(value).replace(" ", "")


def calculate_name_score(steward_name, employee_name):
    normalized_steward = normalize_name(steward_name)
    normalized_employee = normalize_name(employee_name)

    if not normalized_steward or not normalized_employee:
        return 0.0

    if normalized_steward == normalized_employee:
        return 100.0

    if compact_name(steward_name) == compact_name(employee_name):
        return 98.0

    token_score = fuzz.token_set_ratio(
        normalized_steward,
        normalized_employee,
    )

    weighted_score = fuzz.WRatio(
        normalized_steward,
        normalized_employee,
    )

    score = max(
        token_score,
        weighted_score,
    )

    return round(float(score), 2)


def determine_match_status(confidence):
    if confidence >= MATCHED_THRESHOLD:
        return "Matched"

    if confidence >= REVIEW_THRESHOLD:
        return "Needs Review"

    return "Not Matched"


def create_explanation(
    steward_name,
    employee_name,
    confidence,
    status,
):
    if not normalize_name(steward_name):
        return "No Data Steward name was provided in the Business Terms file."

    if status == "Matched":
        if confidence == 100:
            return (
                "Exact normalized-name match between the Data Steward "
                "and employee metadata."
            )

        if confidence >= 98:
            return (
                "Strong name match after removing spaces, punctuation "
                "and formatting differences."
            )

        return (
            "High-confidence fuzzy name match between the Data Steward "
            f"and {employee_name}."
        )

    if status == "Needs Review":
        return (
            f"Possible match with {employee_name}, but the spelling "
            "difference requires manual review."
        )

    return (
        "No employee metadata record met the minimum matching threshold."
    )


def find_best_employee(steward_name, metadata):
    if not normalize_name(steward_name):
        return None, 0.0

    best_employee = None
    best_score = 0.0

    for _, employee in metadata.iterrows():
        employee_name = employee.get(
            "employee_name"
        )

        score = calculate_name_score(
            steward_name,
            employee_name,
        )

        if score > best_score:
            best_score = score
            best_employee = employee

    return best_employee, best_score


def clean_output_value(value):
    if value is None or pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    return value


def create_mapping_row(
    business_term,
    best_employee,
    confidence,
):
    steward_name = business_term.get(
        "data_steward"
    )

    status = determine_match_status(confidence)

    if best_employee is None:
        employee_name = None
    else:
        employee_name = best_employee.get(
            "employee_name"
        )

    explanation = create_explanation(
        steward_name=steward_name,
        employee_name=employee_name,
        confidence=confidence,
        status=status,
    )

    row = {
        "bt_id": clean_output_value(
            business_term.get("bt_id")
        ),
        "business_term_name": clean_output_value(
            business_term.get("business_term_name")
        ),
        "description": clean_output_value(
            business_term.get("description")
        ),
        "data_steward_input": clean_output_value(
            steward_name
        ),
        "matched_employee_id": None,
        "matched_employee_name": None,
        "email": None,
        "department": None,
        "job_title": None,
        "account_status": None,
        "metadata_last_updated": None,
        "mapping_confidence": round(confidence, 2),
        "mapping_status": status,
        "mapping_explanation": explanation,
    }

    # Keep employee details for Matched and Needs Review records.
    # Do not enrich low-confidence Not Matched records.
    if (
        best_employee is not None
        and status in ["Matched", "Needs Review"]
    ):
        row.update(
            {
                "matched_employee_id": clean_output_value(
                    best_employee.get("employee_id")
                ),
                "matched_employee_name": clean_output_value(
                    best_employee.get("employee_name")
                ),
                "email": clean_output_value(
                    best_employee.get("email")
                ),
                "department": clean_output_value(
                    best_employee.get("department")
                ),
                "job_title": clean_output_value(
                    best_employee.get("job_title")
                ),
                "account_status": clean_output_value(
                    best_employee.get("account_status")
                ),
                "metadata_last_updated": clean_output_value(
                    best_employee.get("last_updated")
                ),
            }
        )

    return row


def validate_columns(
    dataframe,
    required_columns,
    file_description,
):
    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{file_description} is missing these columns: "
            f"{', '.join(missing_columns)}"
        )


def generate_steward_mappings():
    if not BUSINESS_TERMS_PATH.exists():
        raise FileNotFoundError(
            "business_terms.xlsx was not found inside dummy_data."
        )

    metadata_path = locate_metadata_file()

    business_terms = pd.read_excel(
        BUSINESS_TERMS_PATH
    )

    metadata = pd.read_excel(
        metadata_path
    )

    validate_columns(
        business_terms,
        [
            "bt_id",
            "business_term_name",
            "description",
            "data_steward",
        ],
        "Business Terms file",
    )

    validate_columns(
        metadata,
        [
            "employee_id",
            "employee_name",
            "email",
            "department",
            "job_title",
            "account_status",
            "last_updated",
        ],
        "Steward Metadata file",
    )

    mapping_rows = []

    for _, business_term in business_terms.iterrows():
        steward_name = business_term.get(
            "data_steward"
        )

        best_employee, confidence = find_best_employee(
            steward_name,
            metadata,
        )

        mapping_row = create_mapping_row(
            business_term=business_term,
            best_employee=best_employee,
            confidence=confidence,
        )

        mapping_rows.append(mapping_row)

    results = pd.DataFrame(mapping_rows)

    matched = results[
        results["mapping_status"] == "Matched"
    ].copy()

    needs_review = results[
        results["mapping_status"] == "Needs Review"
    ].copy()

    unmatched = results[
        results["mapping_status"] == "Not Matched"
    ].copy()

    with pd.ExcelWriter(
        OUTPUT_PATH,
        engine="openpyxl",
    ) as writer:
        results.to_excel(
            writer,
            sheet_name="All Results",
            index=False,
        )

        matched.to_excel(
            writer,
            sheet_name="Matched",
            index=False,
        )

        needs_review.to_excel(
            writer,
            sheet_name="Needs Review",
            index=False,
        )

        unmatched.to_excel(
            writer,
            sheet_name="Unmatched",
            index=False,
        )

    print()
    print("Steward mapping completed successfully.")
    print(f"Business terms processed: {len(results)}")
    print(f"Matched: {len(matched)}")
    print(f"Needs review: {len(needs_review)}")
    print(f"Not matched: {len(unmatched)}")
    print(f"Output saved to: {OUTPUT_PATH}")
    print()

    display_columns = [
        "business_term_name",
        "data_steward_input",
        "matched_employee_name",
        "email",
        "mapping_confidence",
        "mapping_status",
    ]

    print(
        results[display_columns].to_string(
            index=False
        )
    )

    return results


if __name__ == "__main__":
    generate_steward_mappings()