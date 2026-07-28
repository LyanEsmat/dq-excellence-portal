from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

METADATA_DIR = PROJECT_DIR / "data" / "metadata"
REFERENCE_DIR = PROJECT_DIR / "data" / "reference"

TECHNICAL_METADATA_FILE = (
    METADATA_DIR
    / "technical_metadata.xlsx"
)

BUSINESS_TERMS_FILE = (
    METADATA_DIR
    / "business_terms.xlsx"
)

GROUND_TRUTH_FILE = (
    REFERENCE_DIR
    / "bt_mapping_ground_truth.xlsx"
)


STEWARDS = {
    "ENTERPRISE": "Lyan Esmat",
    "PHO": "Fahad AlQahtani",
    "ALU": "Noura AlHarbi",
    "PRO": "Khalid AlOtaibi",
    "GGM": "Saud AlDosari",
    "FIN": "Maha AlEnezi",
    "HR": "Lyan Esmat",
    "PDE": "Moath AlSoqair",
}


DOMAIN_TERMS = {
    "PHO": [
        (
            "production_record_id",
            "Phosphate Production Record Identifier",
            "Unique identifier assigned to a phosphate "
            "production record.",
            "Critical",
        ),
        (
            "mine_site_code",
            "Phosphate Mine Site Code",
            "Approved code identifying the phosphate "
            "mine site.",
            "High",
        ),
        (
            "phosphate_grade",
            "Phosphate Material Grade",
            "Business classification describing the "
            "quality grade of phosphate material.",
            "High",
        ),
        (
            "production_tons",
            "Phosphate Production Quantity",
            "Quantity of phosphate material produced, "
            "measured in metric tons.",
            "Critical",
        ),
        (
            "sample_date",
            "Phosphate Sample Date",
            "Date on which the phosphate production "
            "sample was recorded.",
            "High",
        ),
        (
            "equipment_status",
            "Phosphate Equipment Status",
            "Current operational status of phosphate "
            "production equipment.",
            "High",
        ),
    ],
    "ALU": [
        (
            "smelter_batch_id",
            "Aluminum Smelter Batch Identifier",
            "Unique identifier assigned to an aluminum "
            "smelter production batch.",
            "Critical",
        ),
        (
            "smelter_code",
            "Aluminum Smelter Code",
            "Approved code identifying an aluminum "
            "smelter facility.",
            "High",
        ),
        (
            "aluminum_grade",
            "Aluminum Product Grade",
            "Classification describing the grade of "
            "produced aluminum.",
            "High",
        ),
        (
            "output_tons",
            "Aluminum Production Output",
            "Quantity of aluminum output measured in "
            "metric tons.",
            "Critical",
        ),
        (
            "production_date",
            "Aluminum Production Date",
            "Date on which the aluminum batch was "
            "produced.",
            "High",
        ),
        (
            "batch_status",
            "Aluminum Batch Status",
            "Current processing status of the aluminum "
            "production batch.",
            "High",
        ),
    ],
    "PRO": [
        (
            "purchase_order_id",
            "Purchase Order Identifier",
            "Unique identifier assigned to a procurement "
            "purchase order.",
            "Critical",
        ),
        (
            "vendor_code",
            "Procurement Vendor Code",
            "Approved code identifying the vendor linked "
            "to a purchase order.",
            "High",
        ),
        (
            "procurement_category",
            "Procurement Category",
            "Classification of the goods or services "
            "being procured.",
            "High",
        ),
        (
            "order_value_sar",
            "Purchase Order Value",
            "Total monetary value of a purchase order "
            "expressed in Saudi Riyals.",
            "Critical",
        ),
        (
            "order_date",
            "Purchase Order Date",
            "Date on which the purchase order was created.",
            "High",
        ),
        (
            "order_status",
            "Purchase Order Status",
            "Current lifecycle status of a purchase order.",
            "High",
        ),
    ],
    "GGM": [
        (
            "extraction_record_id",
            "Gold Extraction Record Identifier",
            "Unique identifier assigned to a gold "
            "extraction record.",
            "Critical",
        ),
        (
            "mine_code",
            "Gold Mine Code",
            "Approved code identifying a gold mine.",
            "High",
        ),
        (
            "ore_grade",
            "Gold Ore Grade",
            "Classification describing the assessed "
            "quality of extracted gold ore.",
            "Critical",
        ),
        (
            "extracted_tons",
            "Gold Ore Extraction Quantity",
            "Quantity of extracted ore measured in "
            "metric tons.",
            "Critical",
        ),
        (
            "extraction_date",
            "Gold Ore Extraction Date",
            "Date on which the ore extraction activity "
            "was recorded.",
            "High",
        ),
        (
            "operation_status",
            "Gold Mining Operation Status",
            "Current operational status of the gold "
            "mining activity.",
            "High",
        ),
    ],
    "FIN": [
        (
            "transaction_id",
            "Financial Transaction Identifier",
            "Unique identifier assigned to a financial "
            "transaction.",
            "Critical",
        ),
        (
            "cost_center",
            "Financial Cost Center",
            "Approved organizational cost center linked "
            "to a financial transaction.",
            "Critical",
        ),
        (
            "transaction_type",
            "Financial Transaction Type",
            "Business classification assigned to a "
            "financial transaction.",
            "High",
        ),
        (
            "amount_sar",
            "Financial Transaction Amount",
            "Monetary value of a financial transaction "
            "expressed in Saudi Riyals.",
            "Critical",
        ),
        (
            "posting_date",
            "Financial Posting Date",
            "Date on which a financial transaction was "
            "posted.",
            "Critical",
        ),
        (
            "approval_status",
            "Financial Approval Status",
            "Current approval status of a financial "
            "transaction.",
            "High",
        ),
    ],
    "HR": [
        (
            "employee_id",
            "Employee Identifier",
            "Unique enterprise identifier assigned to "
            "an employee.",
            "Critical",
        ),
        (
            "department_code",
            "Employee Department Code",
            "Approved department code associated with "
            "an employee.",
            "High",
        ),
        (
            "job_family",
            "Employee Job Family",
            "Enterprise job-family classification "
            "assigned to an employee.",
            "High",
        ),
        (
            "monthly_salary_sar",
            "Employee Monthly Salary",
            "Employee monthly salary amount expressed "
            "in Saudi Riyals.",
            "Restricted",
        ),
        (
            "hire_date",
            "Employee Hire Date",
            "Official date on which the employee joined "
            "the organization.",
            "High",
        ),
        (
            "account_status",
            "Employee Account Status",
            "Current status of the employee enterprise "
            "account.",
            "High",
        ),
    ],
    "PDE": [
        (
            "project_record_id",
            "Project Delivery Record Identifier",
            "Unique identifier assigned to a project "
            "delivery record.",
            "Critical",
        ),
        (
            "project_code",
            "Enterprise Project Code",
            "Approved code identifying an enterprise "
            "project.",
            "Critical",
        ),
        (
            "project_phase",
            "Project Delivery Phase",
            "Current lifecycle phase of an enterprise "
            "project.",
            "High",
        ),
        (
            "budget_sar",
            "Project Approved Budget",
            "Approved project budget expressed in "
            "Saudi Riyals.",
            "Critical",
        ),
        (
            "milestone_date",
            "Project Milestone Date",
            "Planned or actual date associated with a "
            "project milestone.",
            "High",
        ),
        (
            "project_status",
            "Project Delivery Status",
            "Current delivery status of an enterprise "
            "project.",
            "High",
        ),
    ],
}


SHARED_TERMS = [
    {
        "business_term_name": "Business Unit Code",
        "description": (
            "Approved code identifying the Business Unit "
            "responsible for a business record."
        ),
        "technical_column": "business_unit",
        "criticality": "High",
    },
    {
        "business_term_name": "Record Owner Email",
        "description": (
            "Corporate email address of the person "
            "responsible for a business record."
        ),
        "technical_column": "record_owner_email",
        "criticality": "High",
    },
    {
        "business_term_name": "Record Last Updated Timestamp",
        "description": (
            "Date and time when a business record was "
            "most recently updated."
        ),
        "technical_column": "last_updated",
        "criticality": "High",
    },
]


def add_mapping(
    mappings,
    bt_id,
    metadata_row,
):
    mappings.append(
        {
            "bt_id": bt_id,
            "source_system": metadata_row["source_system"],
            "database_name": metadata_row["database_name"],
            "schema_name": metadata_row["schema_name"],
            "table_name": metadata_row["table_name"],
            "column_name": metadata_row["column_name"],
            "business_unit": metadata_row["business_unit"],
            "expected_mapping": "YES",
        }
    )


def create_catalog():
    if not TECHNICAL_METADATA_FILE.exists():
        raise FileNotFoundError(
            "Technical metadata was not found. "
            "Run the enterprise dummy-data generator first."
        )

    technical_metadata = pd.read_excel(
        TECHNICAL_METADATA_FILE
    )

    business_terms = []
    mappings = []
    bt_number = 1

    # Shared enterprise Business Terms.
    for shared_term in SHARED_TERMS:
        bt_id = f"BT-{bt_number:04d}"

        business_terms.append(
            {
                "bt_id": bt_id,
                "business_term_name": shared_term[
                    "business_term_name"
                ],
                "description": shared_term[
                    "description"
                ],
                "data_steward": STEWARDS["ENTERPRISE"],
                "business_unit": "ENTERPRISE",
                "criticality": shared_term["criticality"],
                "approval_status": "Approved",
            }
        )

        matching_columns = technical_metadata[
            technical_metadata["column_name"]
            == shared_term["technical_column"]
        ]

        for _, metadata_row in matching_columns.iterrows():
            add_mapping(
                mappings,
                bt_id,
                metadata_row,
            )

        bt_number += 1

    # Domain-specific Business Terms.
    for business_unit, terms in DOMAIN_TERMS.items():
        for (
            technical_column,
            term_name,
            description,
            criticality,
        ) in terms:
            bt_id = f"BT-{bt_number:04d}"

            business_terms.append(
                {
                    "bt_id": bt_id,
                    "business_term_name": term_name,
                    "description": description,
                    "data_steward": STEWARDS[
                        business_unit
                    ],
                    "business_unit": business_unit,
                    "criticality": criticality,
                    "approval_status": "Approved",
                }
            )

            matching_columns = technical_metadata[
                (
                    technical_metadata["business_unit"]
                    == business_unit
                )
                & (
                    technical_metadata["column_name"]
                    == technical_column
                )
            ]

            if matching_columns.empty:
                raise ValueError(
                    f"No technical column found for "
                    f"{business_unit}.{technical_column}"
                )

            for _, metadata_row in matching_columns.iterrows():
                add_mapping(
                    mappings,
                    bt_id,
                    metadata_row,
                )

            bt_number += 1

    business_terms_dataframe = pd.DataFrame(
        business_terms
    )

    mapping_dataframe = pd.DataFrame(mappings)

    business_terms_dataframe.to_excel(
        BUSINESS_TERMS_FILE,
        index=False,
    )

    mapping_dataframe.to_excel(
        GROUND_TRUTH_FILE,
        index=False,
    )

    print()
    print("Business Term catalog created successfully.")
    print(
        f"Business Terms: "
        f"{len(business_terms_dataframe)}"
    )
    print(
        f"Expected technical mappings: "
        f"{len(mapping_dataframe)}"
    )
    print(
        f"Shared enterprise terms: "
        f"{len(SHARED_TERMS)}"
    )
    print(
        f"Domain-specific terms: "
        f"{len(business_terms_dataframe) - len(SHARED_TERMS)}"
    )
    print(f"Saved: {BUSINESS_TERMS_FILE}")
    print(f"Saved: {GROUND_TRUTH_FILE}")
    print()


if __name__ == "__main__":
    create_catalog()