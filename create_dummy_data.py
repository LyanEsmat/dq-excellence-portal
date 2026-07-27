from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DUMMY_DATA_DIR = BASE_DIR / "dummy_data"

DUMMY_DATA_DIR.mkdir(exist_ok=True)


EMPLOYEES = [
    {
        "employee_id": "EMP-1001",
        "employee_name": "Layan Esmat",
        "email": "layan.esmat@dummy-company.com",
        "department": "Data and AI",
        "job_title": "Data Analyst",
        "account_status": "Active",
        "last_updated": datetime.now() - timedelta(days=3),
    },
    {
        "employee_id": "EMP-1002",
        "employee_name": "Moath AlSoqair",
        "email": "moath.alsoqair@dummy-company.com",
        "department": "Data Governance",
        "job_title": "Data Governance Lead",
        "account_status": "Active",
        "last_updated": datetime.now() - timedelta(days=2),
    },
    {
        "employee_id": "EMP-1003",
        "employee_name": "Sara Alharbi",
        "email": "sara.alharbi@dummy-company.com",
        "department": "Human Resources",
        "job_title": "HR Manager",
        "account_status": "Active",
        "last_updated": datetime.now() - timedelta(days=5),
    },
    {
        "employee_id": "EMP-1004",
        "employee_name": "Khalid Alotaibi",
        "email": "khalid.alotaibi@dummy-company.com",
        "department": "Finance",
        "job_title": "Finance Director",
        "account_status": "Active",
        "last_updated": datetime.now() - timedelta(days=6),
    },
    {
        "employee_id": "EMP-1005",
        "employee_name": "Noura Mohamed",
        "email": "noura.mohamed@dummy-company.com",
        "department": "Procurement",
        "job_title": "Procurement Specialist",
        "account_status": "Active",
        "last_updated": datetime.now() - timedelta(days=4),
    },
    {
        "employee_id": "EMP-1006",
        "employee_name": "Fahad Alqahtani",
        "email": "fahad.alqahtani@dummy-company.com",
        "department": "Projects and Engineering",
        "job_title": "Principal Engineer",
        "account_status": "Active",
        "last_updated": datetime.now() - timedelta(days=8),
    },
    {
        "employee_id": "EMP-1007",
        "employee_name": "Reem Alshammari",
        "email": "reem.alshammari@dummy-company.com",
        "department": "Phosphate",
        "job_title": "Operations Manager",
        "account_status": "Active",
        "last_updated": datetime.now() - timedelta(days=7),
    },
    {
        "employee_id": "EMP-1008",
        "employee_name": "Abdullah Almutairi",
        "email": "abdullah.almutairi@dummy-company.com",
        "department": "Aluminum",
        "job_title": "Production Director",
        "account_status": "Active",
        "last_updated": datetime.now() - timedelta(days=12),
    },
    {
        "employee_id": "EMP-1009",
        "employee_name": "Maha Alenezi",
        "email": "maha.alenezi@dummy-company.com",
        "department": "Gold and Base Metals",
        "job_title": "Business Manager",
        "account_status": "Active",
        "last_updated": datetime.now() - timedelta(days=10),
    },
    {
        "employee_id": "EMP-1010",
        "employee_name": "Omar Alshehri",
        "email": None,
        "department": "Information Technology",
        "job_title": "Systems Manager",
        "account_status": "Active",
        "last_updated": datetime.now() - timedelta(days=9),
    },
    {
        "employee_id": "EMP-1011",
        "employee_name": "Hind Aldossari",
        "email": "hind.aldossari@dummy-company.com",
        "department": "Risk and Compliance",
        "job_title": "Risk Director",
        "account_status": "Inactive",
        "last_updated": datetime.now() - timedelta(days=15),
    },
    {
        "employee_id": "EMP-1012",
        "employee_name": "Yousef Alzahrani",
        "email": "invalid-email",
        "department": "Supply Chain",
        "job_title": "Supply Chain Manager",
        "account_status": "Active",
        "last_updated": datetime.now() - timedelta(days=180),
    },
]


BUSINESS_TERMS = [
    {
        "bt_id": "BT-001",
        "business_term_name": "Employee ID",
        "description": "Unique identifier assigned to an employee",
        "data_steward": "Sara Al Harbi",
    },
    {
        "bt_id": "BT-002",
        "business_term_name": "Employee Name",
        "description": "Full legal name of an employee",
        "data_steward": "sara alharbi",
    },
    {
        "bt_id": "BT-003",
        "business_term_name": "Employee Email",
        "description": "Official employee email address",
        "data_steward": "Sara Alharbi",
    },
    {
        "bt_id": "BT-004",
        "business_term_name": "Hire Date",
        "description": "Date on which an employee joined",
        "data_steward": "Layan Esmat",
    },
    {
        "bt_id": "BT-005",
        "business_term_name": "Transaction ID",
        "description": "Unique financial transaction identifier",
        "data_steward": "Khalid Al Otaibi",
    },
    {
        "bt_id": "BT-006",
        "business_term_name": "Cost Center",
        "description": "Organizational cost center code",
        "data_steward": "Khalid Alotaibi",
    },
    {
        "bt_id": "BT-007",
        "business_term_name": "GL Account",
        "description": "General ledger account code",
        "data_steward": "Khalid Alotaibi",
    },
    {
        "bt_id": "BT-008",
        "business_term_name": "Transaction Amount",
        "description": "Financial value of a transaction",
        "data_steward": "Layan  Esmat",
    },
    {
        "bt_id": "BT-009",
        "business_term_name": "Vendor ID",
        "description": "Unique identifier assigned to a supplier",
        "data_steward": "Noura Mohammed",
    },
    {
        "bt_id": "BT-010",
        "business_term_name": "Vendor Name",
        "description": "Registered supplier business name",
        "data_steward": "Noura Mohamed",
    },
    {
        "bt_id": "BT-011",
        "business_term_name": "Supplier Email",
        "description": "Primary email address of a supplier",
        "data_steward": "Noura Mohamed",
    },
    {
        "bt_id": "BT-012",
        "business_term_name": "Purchase Order Amount",
        "description": "Total value of a purchase order",
        "data_steward": "Yousef Al Zahrani",
    },
    {
        "bt_id": "BT-013",
        "business_term_name": "Project ID",
        "description": "Unique engineering project identifier",
        "data_steward": "Fahad Al Qahtani",
    },
    {
        "bt_id": "BT-014",
        "business_term_name": "Project Name",
        "description": "Official name of an engineering project",
        "data_steward": "Fahad Alqahtani",
    },
    {
        "bt_id": "BT-015",
        "business_term_name": "Project Budget",
        "description": "Approved project financial budget",
        "data_steward": "Fahad Alqahtani",
    },
    {
        "bt_id": "BT-016",
        "business_term_name": "Project Status",
        "description": "Current lifecycle status of a project",
        "data_steward": "Moath AlSoqair",
    },
    {
        "bt_id": "BT-017",
        "business_term_name": "Shipment ID",
        "description": "Unique identifier for a phosphate shipment",
        "data_steward": "Reem Al Shammari",
    },
    {
        "bt_id": "BT-018",
        "business_term_name": "Phosphate Grade",
        "description": "Measured phosphate concentration",
        "data_steward": "Reem Alshammari",
    },
    {
        "bt_id": "BT-019",
        "business_term_name": "Shipment Quantity",
        "description": "Quantity of a phosphate shipment",
        "data_steward": "Reem Alshammari",
    },
    {
        "bt_id": "BT-020",
        "business_term_name": "Inspection Date",
        "description": "Date of shipment quality inspection",
        "data_steward": "Omar Alshehri",
    },
    {
        "bt_id": "BT-021",
        "business_term_name": "Batch ID",
        "description": "Unique aluminum production batch identifier",
        "data_steward": "Abdullah Al Mutairi",
    },
    {
        "bt_id": "BT-022",
        "business_term_name": "Alloy Grade",
        "description": "Approved aluminum alloy classification",
        "data_steward": "Abdullah Almutairi",
    },
    {
        "bt_id": "BT-023",
        "business_term_name": "Production Weight",
        "description": "Weight of an aluminum production batch",
        "data_steward": "Abdullah Almutairi",
    },
    {
        "bt_id": "BT-024",
        "business_term_name": "Quality Status",
        "description": "Quality inspection result of a batch",
        "data_steward": "Hind Al Dossari",
    },
    {
        "bt_id": "BT-025",
        "business_term_name": "Mine Record ID",
        "description": "Unique mine production record identifier",
        "data_steward": "Maha Al Enezi",
    },
    {
        "bt_id": "BT-026",
        "business_term_name": "Ore Grade",
        "description": "Measured mineral concentration",
        "data_steward": "Maha Alenezi",
    },
    {
        "bt_id": "BT-027",
        "business_term_name": "Extraction Volume",
        "description": "Volume of extracted mine material",
        "data_steward": None,
    },
    {
        "bt_id": "BT-028",
        "business_term_name": "Sample Date",
        "description": "Date on which an ore sample was collected",
        "data_steward": "Unknown Person",
    },
]


def remove_old_dummy_files():
    files_to_remove = [
        DUMMY_DATA_DIR / "technical_metadata.xlsx",
        DUMMY_DATA_DIR / "source_data.xlsx",
        DUMMY_DATA_DIR / "active_directory.xlsx",
        DUMMY_DATA_DIR / "metadata.xlsx",
    ]

    for file_path in files_to_remove:
        if file_path.exists():
            file_path.unlink()


def create_dummy_files():
    remove_old_dummy_files()

    business_terms_dataframe = pd.DataFrame(
        BUSINESS_TERMS
    )

    metadata_dataframe = pd.DataFrame(
        EMPLOYEES
    )

    business_terms_path = (
        DUMMY_DATA_DIR / "business_terms.xlsx"
    )

    metadata_path = (
        DUMMY_DATA_DIR / "steward_metadata.xlsx"
    )

    business_terms_dataframe.to_excel(
        business_terms_path,
        index=False,
    )

    metadata_dataframe.to_excel(
        metadata_path,
        index=False,
    )

    print()
    print("Dummy files created successfully.")
    print(
        f"Business terms: "
        f"{len(business_terms_dataframe)}"
    )
    print(
        f"Steward metadata employees: "
        f"{len(metadata_dataframe)}"
    )
    print(f"Saved: {business_terms_path}")
    print(f"Saved: {metadata_path}")
    print()


if __name__ == "__main__":
    create_dummy_files()