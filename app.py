import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from dq_engine import execute_data_quality
from mapping_engine import generate_steward_mappings


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

MAPPING_PATH = (
    OUTPUT_DIR / "business_term_steward_mapping.xlsx"
)

DQ_RESULTS_PATH = (
    OUTPUT_DIR / "data_quality_results.xlsx"
)


app = FastAPI(
    title="Data Quality Excellence Portal",
    description=(
        "Business Term to Data Steward metadata "
        "mapping and Data Quality API"
    ),
    version="1.0.0",
)


def dataframe_to_records(dataframe):
    return json.loads(
        dataframe.to_json(
            orient="records",
            date_format="iso",
        )
    )


def require_file(file_path, message):
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=message,
        )


def read_mapping_sheet(sheet_name="All Results"):
    require_file(
        MAPPING_PATH,
        (
            "Mapping results were not found. "
            "Run the pipeline first."
        ),
    )

    return pd.read_excel(
        MAPPING_PATH,
        sheet_name=sheet_name,
    )


def read_dq_sheet(sheet_name):
    require_file(
        DQ_RESULTS_PATH,
        (
            "Data Quality results were not found. "
            "Run the pipeline first."
        ),
    )

    return pd.read_excel(
        DQ_RESULTS_PATH,
        sheet_name=sheet_name,
    )


@app.get(
    "/",
    include_in_schema=False,
)
def home():
    return RedirectResponse(
        url="/docs",
    )


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "application": (
            "Data Quality Excellence Portal"
        ),
        "mapping_results_available":
            MAPPING_PATH.exists(),
        "dq_results_available":
            DQ_RESULTS_PATH.exists(),
    }


@app.post("/api/run-pipeline")
def run_pipeline():
    try:
        mapping_results = (
            generate_steward_mappings()
        )

        execute_data_quality()

        summary = read_dq_sheet("Summary")
        summary_record = dataframe_to_records(
            summary
        )[0]

        return {
            "message": (
                "Mapping and Data Quality "
                "pipeline completed successfully."
            ),
            "business_terms_processed":
                len(mapping_results),
            "summary": summary_record,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@app.get("/api/dashboard")
def get_dashboard():
    summary = read_dq_sheet("Summary")
    dimensions = read_dq_sheet(
        "Dimension Scores"
    )
    rules = read_dq_sheet("Rule Results")
    recommendations = read_dq_sheet(
        "Recommendations"
    )

    summary_record = dataframe_to_records(
        summary
    )[0]

    dimension_records = dataframe_to_records(
        dimensions
    )

    rule_records = dataframe_to_records(
        rules
    )

    recommendation_records = (
        dataframe_to_records(
            recommendations
        )
    )

    return {
        "summary": summary_record,
        "dimensions": dimension_records,
        "rules": rule_records,
        "recommendations":
            recommendation_records,
    }


@app.get("/api/mappings")
def get_mappings(
    status: str | None = None,
):
    mappings = read_mapping_sheet(
        "All Results"
    )

    if status:
        mappings = mappings[
            mappings[
                "mapping_status"
            ].str.lower()
            == status.lower()
        ]

    return {
        "total": len(mappings),
        "records": dataframe_to_records(
            mappings
        ),
    }


@app.get("/api/mappings/matched")
def get_matched_mappings():
    mappings = read_mapping_sheet(
        "Matched"
    )

    return {
        "total": len(mappings),
        "records": dataframe_to_records(
            mappings
        ),
    }


@app.get("/api/mappings/review")
def get_review_mappings():
    mappings = read_mapping_sheet(
        "Needs Review"
    )

    return {
        "total": len(mappings),
        "records": dataframe_to_records(
            mappings
        ),
    }


@app.get("/api/mappings/unmatched")
def get_unmatched_mappings():
    mappings = read_mapping_sheet(
        "Unmatched"
    )

    return {
        "total": len(mappings),
        "records": dataframe_to_records(
            mappings
        ),
    }


@app.get("/api/dq/rules")
def get_rule_results():
    rules = read_dq_sheet(
        "Rule Results"
    )

    return {
        "total": len(rules),
        "records": dataframe_to_records(
            rules
        ),
    }


@app.get("/api/dq/dimensions")
def get_dimension_scores():
    dimensions = read_dq_sheet(
        "Dimension Scores"
    )

    return {
        "total": len(dimensions),
        "records": dataframe_to_records(
            dimensions
        ),
    }


@app.get("/api/dq/failed-records")
def get_failed_records():
    failed_records = read_dq_sheet(
        "Failed Records"
    )

    return {
        "total": len(failed_records),
        "records": dataframe_to_records(
            failed_records
        ),
    }


@app.get("/api/recommendations")
def get_recommendations():
    recommendations = read_dq_sheet(
        "Recommendations"
    )

    return {
        "total": len(recommendations),
        "records": dataframe_to_records(
            recommendations
        ),
    }


@app.get("/api/download/mappings")
def download_mapping_results():
    require_file(
        MAPPING_PATH,
        "Mapping output does not exist.",
    )

    return FileResponse(
        path=MAPPING_PATH,
        filename=(
            "business_term_steward_mapping.xlsx"
        ),
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
    )


@app.get("/api/download/dq-results")
def download_dq_results():
    require_file(
        DQ_RESULTS_PATH,
        "DQ output does not exist.",
    )

    return FileResponse(
        path=DQ_RESULTS_PATH,
        filename="data_quality_results.xlsx",
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
    )