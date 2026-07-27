from pathlib import Path
import subprocess
import sys

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent

MAPPING_FILE = (
    BASE_DIR
    / "outputs"
    / "business_term_steward_mapping.xlsx"
)

DQ_FILE = (
    BASE_DIR
    / "outputs"
    / "data_quality_results_v2.xlsx"
)

DASHBOARD_FILE = (
    BASE_DIR
    / "templates"
    / "dq_dashboard_v2.html"
)


app = FastAPI(
    title="Data Quality Excellence Portal V2",
    description=(
        "Business Term mapping and detailed "
        "Data Quality assessment API."
    ),
    version="2.0.0",
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


def clean_value(value):
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if hasattr(value, "item"):
        return value.item()

    return value


def dataframe_to_records(dataframe):
    records = []

    for record in dataframe.to_dict(orient="records"):
        records.append(
            {
                str(key): clean_value(value)
                for key, value in record.items()
            }
        )

    return records


def read_excel_sheet(file_path, sheet_name):
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Required file was not found: {file_path.name}",
        )

    try:
        return pd.read_excel(
            file_path,
            sheet_name=sheet_name,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Sheet '{sheet_name}' was not found "
                f"inside {file_path.name}."
            ),
        ) from error


@app.get("/", include_in_schema=False)
def dashboard_home():
    if not DASHBOARD_FILE.exists():
        return {
            "message": (
                "The V2 API is working. "
                "The V2 dashboard file has not been created yet."
            ),
            "next_file": "templates/dq_dashboard_v2.html",
            "api_documentation": "/docs",
        }

    return FileResponse(DASHBOARD_FILE)


@app.get("/api/v2/health")
def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "mapping_file_available": MAPPING_FILE.exists(),
        "dq_file_available": DQ_FILE.exists(),
        "dashboard_available": DASHBOARD_FILE.exists(),
    }


@app.get("/api/v2/dashboard")
def get_dashboard_data():
    summary = read_excel_sheet(
        DQ_FILE,
        "Summary",
    )

    dimensions = read_excel_sheet(
        DQ_FILE,
        "Dimension Scores",
    )

    business_terms = read_excel_sheet(
        DQ_FILE,
        "BT Scores",
    )

    columns = read_excel_sheet(
        DQ_FILE,
        "Column Scores",
    )

    failures = read_excel_sheet(
        DQ_FILE,
        "Failures",
    )

    return {
        "summary": dataframe_to_records(summary)[0],
        "dimension_scores": dataframe_to_records(
            dimensions
        ),
        "business_term_scores": dataframe_to_records(
            business_terms
        ),
        "column_scores": dataframe_to_records(columns),
        "failures": dataframe_to_records(failures),
    }


@app.get("/api/v2/dq/executions")
def get_dq_executions(
    status: str | None = None,
    dimension: str | None = None,
    business_term: str | None = None,
):
    dataframe = read_excel_sheet(
        DQ_FILE,
        "All DQ Executions",
    )

    if status:
        dataframe = dataframe[
            dataframe["execution_status"]
            .astype(str)
            .str.lower()
            == status.strip().lower()
        ]

    if dimension:
        dataframe = dataframe[
            dataframe["dq_dimension"]
            .astype(str)
            .str.lower()
            == dimension.strip().lower()
        ]

    if business_term:
        dataframe = dataframe[
            dataframe["business_term_name"]
            .astype(str)
            .str.contains(
                business_term,
                case=False,
                na=False,
            )
        ]

    return {
        "count": len(dataframe),
        "results": dataframe_to_records(dataframe),
    }


@app.get("/api/v2/dq/failures")
def get_dq_failures():
    dataframe = read_excel_sheet(
        DQ_FILE,
        "Failures",
    )

    return {
        "count": len(dataframe),
        "results": dataframe_to_records(dataframe),
    }


@app.get("/api/v2/dq/dimensions")
def get_dimension_scores():
    dataframe = read_excel_sheet(
        DQ_FILE,
        "Dimension Scores",
    )

    return {
        "count": len(dataframe),
        "results": dataframe_to_records(dataframe),
    }


@app.get("/api/v2/dq/business-terms")
def get_business_term_scores():
    dataframe = read_excel_sheet(
        DQ_FILE,
        "BT Scores",
    )

    return {
        "count": len(dataframe),
        "results": dataframe_to_records(dataframe),
    }


@app.get("/api/v2/dq/columns")
def get_column_scores():
    dataframe = read_excel_sheet(
        DQ_FILE,
        "Column Scores",
    )

    return {
        "count": len(dataframe),
        "results": dataframe_to_records(dataframe),
    }


@app.get("/api/v2/mappings")
def get_mappings():
    dataframe = read_excel_sheet(
        MAPPING_FILE,
        "All Results",
    )

    # Confidence remains available inside the Excel output,
    # but it is removed from the dashboard API.
    confidence_columns = [
        column
        for column in dataframe.columns
        if "confidence" in str(column).lower()
    ]

    dataframe = dataframe.drop(
        columns=confidence_columns,
        errors="ignore",
    )

    # Correct the displayed name.
    dataframe = dataframe.replace(
        {
            "Layan Esmat": "Lyan Esmat",
            "layan esmat": "Lyan Esmat",
        }
    )

    return {
        "count": len(dataframe),
        "results": dataframe_to_records(dataframe),
    }


@app.post("/api/v2/run-pipeline")
def run_pipeline():
    commands = [
        [sys.executable, "mapping_engine.py"],
        [sys.executable, "dq_engine_v2.py"],
    ]

    execution_log = []

    for command in commands:
        result = subprocess.run(
            command,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        execution_log.append(
            {
                "command": " ".join(command),
                "return_code": result.returncode,
                "output": result.stdout,
                "error": result.stderr,
            }
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "The pipeline failed.",
                    "failed_command": " ".join(command),
                    "output": result.stdout,
                    "error": result.stderr,
                },
            )

    summary = read_excel_sheet(
        DQ_FILE,
        "Summary",
    )

    return {
        "message": "The V2 pipeline completed successfully.",
        "summary": dataframe_to_records(summary)[0],
        "execution_log": execution_log,
    }


@app.get("/api/v2/download/mappings")
def download_mappings():
    if not MAPPING_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="The mapping output has not been generated.",
        )

    return FileResponse(
        MAPPING_FILE,
        filename="business_term_steward_mapping.xlsx",
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )


@app.get("/api/v2/download/dq-results")
def download_dq_results():
    if not DQ_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="The V2 DQ output has not been generated.",
        )

    return FileResponse(
        DQ_FILE,
        filename="data_quality_results_v2.xlsx",
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )