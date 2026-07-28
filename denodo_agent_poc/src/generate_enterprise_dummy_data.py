from pathlib import Path
from datetime import datetime, timedelta
import random

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

SOURCE_DIR = PROJECT_DIR / "data" / "source"
METADATA_DIR = PROJECT_DIR / "data" / "metadata"
REFERENCE_DIR = PROJECT_DIR / "data" / "reference"

ROWS_PER_BUSINESS_UNIT = 8000
RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


DATASETS = {
    "PHO": {
        "file_name": "pho_source.xlsx",
        "table_name": "phosphate_production",
        "id_column": "production_record_id",
        "id_prefix": "PHO",
        "entity_column": "mine_site_code",
        "entities": ["MWZ", "JAL", "RAS"],
        "category_column": "phosphate_grade",
        "categories": ["GRADE_A", "GRADE_B", "GRADE_C"],
        "measure_column": "production_tons",
        "measure_range": (50, 5000),
        "date_column": "sample_date",
        "status_column": "equipment_status",
        "statuses": ["ACTIVE", "MAINTENANCE", "STOPPED"],
    },
    "ALU": {
        "file_name": "alu_source.xlsx",
        "table_name": "aluminum_production",
        "id_column": "smelter_batch_id",
        "id_prefix": "ALU",
        "entity_column": "smelter_code",
        "entities": ["SMT_01", "SMT_02", "SMT_03"],
        "category_column": "aluminum_grade",
        "categories": ["A1000", "A3000", "A5000"],
        "measure_column": "output_tons",
        "measure_range": (20, 3000),
        "date_column": "production_date",
        "status_column": "batch_status",
        "statuses": ["COMPLETED", "IN_PROGRESS", "HELD"],
    },
    "PRO": {
        "file_name": "pro_source.xlsx",
        "table_name": "procurement_orders",
        "id_column": "purchase_order_id",
        "id_prefix": "PRO",
        "entity_column": "vendor_code",
        "entities": ["V001", "V002", "V003", "V004", "V005"],
        "category_column": "procurement_category",
        "categories": [
            "EQUIPMENT",
            "SERVICES",
            "MATERIALS",
            "LOGISTICS",
        ],
        "measure_column": "order_value_sar",
        "measure_range": (1000, 2_000_000),
        "date_column": "order_date",
        "status_column": "order_status",
        "statuses": [
            "OPEN",
            "APPROVED",
            "CLOSED",
            "CANCELLED",
        ],
    },
    "GGM": {
        "file_name": "ggm_source.xlsx",
        "table_name": "gold_extraction",
        "id_column": "extraction_record_id",
        "id_prefix": "GGM",
        "entity_column": "mine_code",
        "entities": ["MINE_01", "MINE_02", "MINE_03"],
        "category_column": "ore_grade",
        "categories": ["HIGH", "MEDIUM", "LOW"],
        "measure_column": "extracted_tons",
        "measure_range": (10, 2500),
        "date_column": "extraction_date",
        "status_column": "operation_status",
        "statuses": ["ACTIVE", "PAUSED", "MAINTENANCE"],
    },
    "FIN": {
        "file_name": "fin_source.xlsx",
        "table_name": "financial_transactions",
        "id_column": "transaction_id",
        "id_prefix": "FIN",
        "entity_column": "cost_center",
        "entities": ["CC100", "CC200", "CC300", "CC400"],
        "category_column": "transaction_type",
        "categories": ["CAPEX", "OPEX", "PAYROLL", "REVENUE"],
        "measure_column": "amount_sar",
        "measure_range": (100, 5_000_000),
        "date_column": "posting_date",
        "status_column": "approval_status",
        "statuses": ["PENDING", "APPROVED", "REJECTED"],
    },
    "HR": {
        "file_name": "hr_source.xlsx",
        "table_name": "employee_master",
        "id_column": "employee_id",
        "id_prefix": "HR",
        "entity_column": "department_code",
        "entities": ["HR", "FIN", "D_AI", "OPS", "PROC"],
        "category_column": "job_family",
        "categories": [
            "MANAGEMENT",
            "TECHNICAL",
            "OPERATIONS",
            "ADMINISTRATION",
        ],
        "measure_column": "monthly_salary_sar",
        "measure_range": (5000, 60000),
        "date_column": "hire_date",
        "status_column": "account_status",
        "statuses": ["ACTIVE", "INACTIVE", "SUSPENDED"],
    },
    "PDE": {
        "file_name": "pde_source.xlsx",
        "table_name": "project_delivery",
        "id_column": "project_record_id",
        "id_prefix": "PDE",
        "entity_column": "project_code",
        "entities": ["PRJ_100", "PRJ_200", "PRJ_300", "PRJ_400"],
        "category_column": "project_phase",
        "categories": [
            "PLANNING",
            "DESIGN",
            "EXECUTION",
            "CLOSURE",
        ],
        "measure_column": "budget_sar",
        "measure_range": (100_000, 100_000_000),
        "date_column": "milestone_date",
        "status_column": "project_status",
        "statuses": [
            "ON_TRACK",
            "AT_RISK",
            "DELAYED",
            "COMPLETED",
        ],
    },
}


FIRST_NAMES = [
    "Lyan",
    "Moath",
    "Sara",
    "Khalid",
    "Maha",
    "Fahad",
    "Noura",
    "Abdullah",
    "Reem",
    "Omar",
    "Hind",
    "Saud",
]

LAST_NAMES = [
    "Esmat",
    "AlSoqair",
    "AlHarbi",
    "AlOtaibi",
    "AlEnezi",
    "AlQahtani",
    "AlDosari",
    "AlGhamdi",
    "AlZahrani",
    "AlShammari",
]


def random_date(maximum_days_old):
    return datetime.now() - timedelta(
        days=random.randint(0, maximum_days_old)
    )


def create_email(index):
    first_name = FIRST_NAMES[
        index % len(FIRST_NAMES)
    ]

    last_name = LAST_NAMES[
        (index // len(FIRST_NAMES))
        % len(LAST_NAMES)
    ]

    return (
        f"{first_name.lower()}."
        f"{last_name.lower()}{index}"
        "@dummy-company.com"
    )


def choose_indices(row_count, percentage):
    number_of_rows = max(
        1,
        int(row_count * percentage),
    )

    return np.random.choice(
        row_count,
        size=number_of_rows,
        replace=False,
    )


def add_defect(
    manifest,
    business_unit,
    source_row,
    record_id,
    column_name,
    dimension,
    issue,
):
    manifest.append(
        {
            "business_unit": business_unit,
            "source_row": source_row + 2,
            "record_id": record_id,
            "column_name": column_name,
            "dq_dimension": dimension,
            "expected_issue": issue,
        }
    )


def create_clean_dataset(business_unit, config):
    minimum, maximum = config["measure_range"]

    dataframe = pd.DataFrame(
        {
            config["id_column"]: [
                f"{config['id_prefix']}-{index:07d}"
                for index in range(
                    1,
                    ROWS_PER_BUSINESS_UNIT + 1,
                )
            ],
            "business_unit": business_unit,
            config["entity_column"]: np.random.choice(
                config["entities"],
                size=ROWS_PER_BUSINESS_UNIT,
            ),
            config["category_column"]: np.random.choice(
                config["categories"],
                size=ROWS_PER_BUSINESS_UNIT,
            ),
            config["measure_column"]: np.round(
                np.random.uniform(
                    minimum,
                    maximum,
                    size=ROWS_PER_BUSINESS_UNIT,
                ),
                2,
            ),
            config["date_column"]: [
                random_date(730)
                for _ in range(
                    ROWS_PER_BUSINESS_UNIT
                )
            ],
            config["status_column"]: np.random.choice(
                config["statuses"],
                size=ROWS_PER_BUSINESS_UNIT,
            ),
            "record_owner_email": [
                create_email(index)
                for index in range(
                    ROWS_PER_BUSINESS_UNIT
                )
            ],
            "last_updated": [
                random_date(300)
                for _ in range(
                    ROWS_PER_BUSINESS_UNIT
                )
            ],
        }
    )

    return dataframe


def inject_defects(
    dataframe,
    business_unit,
    config,
    manifest,
):
    id_column = config["id_column"]
    entity_column = config["entity_column"]
    category_column = config["category_column"]
    measure_column = config["measure_column"]
    status_column = config["status_column"]

    # Completeness: missing email values.
    for index in choose_indices(
        len(dataframe),
        0.03,
    ):
        record_id = dataframe.at[index, id_column]
        dataframe.at[index, "record_owner_email"] = None

        add_defect(
            manifest,
            business_unit,
            index,
            record_id,
            "record_owner_email",
            "Completeness",
            "Required owner email is missing.",
        )

    # Uniqueness: duplicate identifiers.
    for index in choose_indices(
        len(dataframe),
        0.01,
    ):
        source_index = max(0, index - 1)

        duplicate_id = dataframe.at[
            source_index,
            id_column,
        ]

        dataframe.at[index, id_column] = duplicate_id

        add_defect(
            manifest,
            business_unit,
            index,
            duplicate_id,
            id_column,
            "Uniqueness",
            "Record identifier is duplicated.",
        )

    # Validity: malformed emails.
    for index in choose_indices(
        len(dataframe),
        0.015,
    ):
        record_id = dataframe.at[index, id_column]

        dataframe.at[
            index,
            "record_owner_email",
        ] = f"invalid-email-{index}"

        add_defect(
            manifest,
            business_unit,
            index,
            record_id,
            "record_owner_email",
            "Validity",
            "Email format is invalid.",
        )

    # Accuracy: unknown reference codes.
    for index in choose_indices(
        len(dataframe),
        0.012,
    ):
        record_id = dataframe.at[index, id_column]

        dataframe.at[
            index,
            entity_column,
        ] = f"UNKNOWN_{business_unit}"

        add_defect(
            manifest,
            business_unit,
            index,
            record_id,
            entity_column,
            "Accuracy",
            "Code is not present in approved reference data.",
        )

    # Validity: impossible negative measures.
    for index in choose_indices(
        len(dataframe),
        0.01,
    ):
        record_id = dataframe.at[index, id_column]

        original_value = dataframe.at[
            index,
            measure_column,
        ]

        dataframe.at[
            index,
            measure_column,
        ] = -abs(float(original_value))

        add_defect(
            manifest,
            business_unit,
            index,
            record_id,
            measure_column,
            "Validity",
            "Numeric value is below the accepted minimum.",
        )

    # Consistency: inconsistent formatting.
    for index in choose_indices(
        len(dataframe),
        0.02,
    ):
        record_id = dataframe.at[index, id_column]

        original_value = str(
            dataframe.at[
                index,
                category_column,
            ]
        )

        dataframe.at[
            index,
            category_column,
        ] = f" {original_value.lower()} "

        add_defect(
            manifest,
            business_unit,
            index,
            record_id,
            category_column,
            "Consistency",
            "Category has inconsistent spacing or casing.",
        )

    # Validity: unsupported statuses.
    for index in choose_indices(
        len(dataframe),
        0.01,
    ):
        record_id = dataframe.at[index, id_column]

        dataframe.at[
            index,
            status_column,
        ] = "UNKNOWN_STATUS"

        add_defect(
            manifest,
            business_unit,
            index,
            record_id,
            status_column,
            "Validity",
            "Status is outside the accepted value list.",
        )

    # Timeliness: stale metadata dates.
    for index in choose_indices(
        len(dataframe),
        0.05,
    ):
        record_id = dataframe.at[index, id_column]

        dataframe.at[
            index,
            "last_updated",
        ] = datetime.now() - timedelta(
            days=random.randint(400, 900)
        )

        add_defect(
            manifest,
            business_unit,
            index,
            record_id,
            "last_updated",
            "Timeliness",
            "Metadata is older than 365 days.",
        )

    return dataframe


def infer_data_type(column_name, series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return "TIMESTAMP"

    if pd.api.types.is_numeric_dtype(series):
        return "DECIMAL(18,2)"

    if column_name.endswith("_id"):
        return "VARCHAR(50)"

    return "VARCHAR(255)"


def create_technical_metadata(
    business_unit,
    config,
    dataframe,
):
    metadata_rows = []

    for column_name in dataframe.columns:
        metadata_rows.append(
            {
                "source_system": (
                    f"DUMMY_{business_unit}_SYSTEM"
                ),
                "database_name": "enterprise_dummy_data",
                "schema_name": business_unit.lower(),
                "table_name": config["table_name"],
                "column_name": column_name,
                "data_type": infer_data_type(
                    column_name,
                    dataframe[column_name],
                ),
                "nullable": (
                    "NO"
                    if column_name
                    in {
                        config["id_column"],
                        "business_unit",
                    }
                    else "YES"
                ),
                "business_unit": business_unit,
                "description": (
                    column_name
                    .replace("_", " ")
                    .title()
                ),
            }
        )

    return metadata_rows


def create_reference_data():
    reference_rows = []

    for business_unit, config in DATASETS.items():
        reference_groups = [
            (
                config["entity_column"],
                config["entities"],
            ),
            (
                config["category_column"],
                config["categories"],
            ),
            (
                config["status_column"],
                config["statuses"],
            ),
        ]

        for reference_type, values in reference_groups:
            for value in values:
                reference_rows.append(
                    {
                        "business_unit": business_unit,
                        "reference_type": reference_type,
                        "approved_value": value,
                    }
                )

    return pd.DataFrame(reference_rows)


def generate_all_data():
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

    all_metadata = []
    defect_manifest = []
    summary_rows = []

    for business_unit, config in DATASETS.items():
        print(
            f"Generating {business_unit}: "
            f"{ROWS_PER_BUSINESS_UNIT:,} rows..."
        )

        dataframe = create_clean_dataset(
            business_unit,
            config,
        )

        dataframe = inject_defects(
            dataframe,
            business_unit,
            config,
            defect_manifest,
        )

        output_file = (
            SOURCE_DIR
            / config["file_name"]
        )

        dataframe.to_excel(
            output_file,
            index=False,
        )

        all_metadata.extend(
            create_technical_metadata(
                business_unit,
                config,
                dataframe,
            )
        )

        summary_rows.append(
            {
                "business_unit": business_unit,
                "file_name": config["file_name"],
                "table_name": config["table_name"],
                "row_count": len(dataframe),
                "column_count": len(
                    dataframe.columns
                ),
            }
        )

        print(f"Saved: {output_file}")

    metadata_dataframe = pd.DataFrame(
        all_metadata
    )

    defect_dataframe = pd.DataFrame(
        defect_manifest
    )

    summary_dataframe = pd.DataFrame(
        summary_rows
    )

    reference_dataframe = (
        create_reference_data()
    )

    metadata_dataframe.to_excel(
        METADATA_DIR / "technical_metadata.xlsx",
        index=False,
    )

    summary_dataframe.to_excel(
        METADATA_DIR / "generation_summary.xlsx",
        index=False,
    )

    reference_dataframe.to_excel(
        REFERENCE_DIR / "reference_data.xlsx",
        index=False,
    )

    defect_dataframe.to_excel(
        REFERENCE_DIR
        / "expected_defect_manifest.xlsx",
        index=False,
    )

    total_rows = int(
        summary_dataframe["row_count"].sum()
    )

    print()
    print("Enterprise dummy data generated successfully.")
    print(f"Business units: {len(DATASETS)}")
    print(
        "Rows per business unit: "
        f"{ROWS_PER_BUSINESS_UNIT:,}"
    )
    print(f"Total source rows: {total_rows:,}")
    print(
        "Technical metadata rows: "
        f"{len(metadata_dataframe)}"
    )
    print(
        "Expected defect entries: "
        f"{len(defect_dataframe):,}"
    )
    print(f"Project folder: {PROJECT_DIR}")


if __name__ == "__main__":
    generate_all_data()