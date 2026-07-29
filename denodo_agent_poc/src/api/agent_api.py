from pathlib import Path
import json
import subprocess
import sys

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse


PROJECT_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_DIR = PROJECT_DIR.parent

RESULTS_DIR = PROJECT_DIR / "data" / "results"

DQ_RESULTS_FILE = (
    RESULTS_DIR / "dq_execution_results.xlsx"
)

MAPPINGS_FILE = (
    RESULTS_DIR
    / "agent_bt_technical_mappings.xlsx"
)

RULE_REGISTRY_FILE = (
    RESULTS_DIR / "dq_rule_registry.xlsx"
)

CONSOLIDATED_INSIGHTS_FILE = (
    RESULTS_DIR
    / "consolidated_dq_insights.xlsx"
)

CONSOLIDATED_INSIGHTS_JSON = (
    RESULTS_DIR
    / "consolidated_dq_insights.json"
)

LATEST_PIPELINE_LOG = (
    RESULTS_DIR / "latest_pipeline_run.json"
)

PIPELINE_HISTORY_FILE = (
    RESULTS_DIR / "pipeline_run_history.csv"
)

FAILED_RECORDS_FILE = (
    RESULTS_DIR / "dq_failed_records.csv"
)

ORCHESTRATOR_FILE = (
    PROJECT_DIR
    / "src"
    / "agent"
    / "pipeline_orchestrator.py"
)


app = FastAPI(
    title="Agentic Data Quality API",
    description=(
        "API for semantic mapping, DQ execution, "
        "agent insights and pipeline monitoring."
    ),
    version="1.0.0",
)


def clean_value(value):
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if hasattr(value, "item"):
        return value.item()

    return value


def dataframe_records(dataframe):
    return [
        {
            str(key): clean_value(value)
            for key, value in row.items()
        }
        for row in dataframe.to_dict(
            orient="records"
        )
    ]


def read_sheet(file_path, sheet_name):
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Required result file is missing: "
                f"{file_path.name}"
            ),
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
                f"Sheet '{sheet_name}' is missing "
                f"from {file_path.name}."
            ),
        ) from error


def read_json(file_path):
    if not file_path.exists():
        return None

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as input_file:
        return json.load(input_file)


def paginate(dataframe, page, page_size):
    total_records = len(dataframe)
    total_pages = max(
        1,
        (
            total_records + page_size - 1
        )
        // page_size,
    )

    page = min(page, total_pages)

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "page": page,
        "page_size": page_size,
        "total_records": total_records,
        "total_pages": total_pages,
        "results": dataframe_records(
            dataframe.iloc[start:end]
        ),
    }


@app.get("/", include_in_schema=False)
def api_home():
    return {
        "name": "Agentic Data Quality API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
def health():
    required_files = {
        "dq_results": DQ_RESULTS_FILE,
        "mappings": MAPPINGS_FILE,
        "rule_registry": RULE_REGISTRY_FILE,
        "consolidated_insights": (
            CONSOLIDATED_INSIGHTS_FILE
        ),
        "pipeline_log": LATEST_PIPELINE_LOG,
    }

    file_status = {
        name: file_path.exists()
        for name, file_path
        in required_files.items()
    }

    return {
        "status": (
            "healthy"
            if all(file_status.values())
            else "incomplete"
        ),
        "files": file_status,
    }


@app.get("/api/dashboard")
def dashboard():
    execution_summary = read_sheet(
        DQ_RESULTS_FILE,
        "Summary",
    )

    dimension_scores = read_sheet(
        DQ_RESULTS_FILE,
        "Dimension Scores",
    )

    business_unit_scores = read_sheet(
        DQ_RESULTS_FILE,
        "BU Scores",
    )

    bt_scores = read_sheet(
        DQ_RESULTS_FILE,
        "BT Scores",
    )

    column_scores = read_sheet(
        DQ_RESULTS_FILE,
        "Column Scores",
    )

    consolidated_summary = read_sheet(
        CONSOLIDATED_INSIGHTS_FILE,
        "Summary",
    )

    insights = read_sheet(
        CONSOLIDATED_INSIGHTS_FILE,
        "Consolidated Insights",
    )

    pipeline_log = read_json(
        LATEST_PIPELINE_LOG
    )

    return {
        "execution_summary": (
            dataframe_records(
                execution_summary
            )[0]
        ),
        "dimension_scores": (
            dataframe_records(
                dimension_scores
            )
        ),
        "business_unit_scores": (
            dataframe_records(
                business_unit_scores
            )
        ),
        "business_term_scores": (
            dataframe_records(bt_scores)
        ),
        "column_scores": (
            dataframe_records(
                column_scores
            )
        ),
        "insight_summary": (
            dataframe_records(
                consolidated_summary
            )[0]
        ),
        "top_insights": (
            dataframe_records(
                insights.head(20)
            )
        ),
        "latest_pipeline_run": pipeline_log,
    }


@app.get("/api/business-units")
def business_units():
    dataframe = read_sheet(
        DQ_RESULTS_FILE,
        "BU Scores",
    )

    return {
        "count": len(dataframe),
        "results": dataframe_records(dataframe),
    }


@app.get("/api/dimensions")
def dimensions():
    dataframe = read_sheet(
        DQ_RESULTS_FILE,
        "Dimension Scores",
    )

    return {
        "count": len(dataframe),
        "results": dataframe_records(dataframe),
    }


@app.get("/api/business-terms")
def business_terms(
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=25,
        ge=1,
        le=200,
    ),
):
    dataframe = read_sheet(
        DQ_RESULTS_FILE,
        "BT Scores",
    )

    if search:
        search_text = search.strip()

        dataframe = dataframe[
            dataframe["bt_id"]
            .astype(str)
            .str.contains(
                search_text,
                case=False,
                na=False,
            )
            |
            dataframe[
                "business_term_name"
            ]
            .astype(str)
            .str.contains(
                search_text,
                case=False,
                na=False,
            )
        ]

    return paginate(
        dataframe,
        page,
        page_size,
    )


@app.get("/api/columns")
def columns(
    business_unit: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=25,
        ge=1,
        le=200,
    ),
):
    dataframe = read_sheet(
        DQ_RESULTS_FILE,
        "Column Scores",
    )

    if business_unit:
        dataframe = dataframe[
            dataframe["business_unit"]
            .astype(str)
            .str.upper()
            == business_unit.strip().upper()
        ]

    return paginate(
        dataframe,
        page,
        page_size,
    )


@app.get("/api/mappings")
def mappings(
    business_unit: str | None = None,
    decision: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=25,
        ge=1,
        le=200,
    ),
):
    if not MAPPINGS_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Agent mapping file is missing.",
        )

    dataframe = pd.read_excel(MAPPINGS_FILE)

    if business_unit:
        dataframe = dataframe[
            dataframe[
                "technical_business_unit"
            ]
            .astype(str)
            .str.upper()
            == business_unit.strip().upper()
        ]

    if decision:
        dataframe = dataframe[
            dataframe["agent_decision"]
            .astype(str)
            .str.lower()
            == decision.strip().lower()
        ]

    return paginate(
        dataframe,
        page,
        page_size,
    )


@app.get("/api/rules")
def rules(
    dimension: str | None = None,
    applicability: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=25,
        ge=1,
        le=200,
    ),
):
    dataframe = read_sheet(
        RULE_REGISTRY_FILE,
        "Rule Registry",
    )

    if dimension:
        dataframe = dataframe[
            dataframe["dq_dimension"]
            .astype(str)
            .str.lower()
            == dimension.strip().lower()
        ]

    if applicability:
        dataframe = dataframe[
            dataframe["applicability"]
            .astype(str)
            .str.lower()
            == applicability.strip().lower()
        ]

    return paginate(
        dataframe,
        page,
        page_size,
    )


@app.get("/api/rule-results")
def rule_results(
    status: str | None = None,
    dimension: str | None = None,
    business_unit: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=25,
        ge=1,
        le=200,
    ),
):
    dataframe = read_sheet(
        DQ_RESULTS_FILE,
        "Rule Results",
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

    if business_unit:
        dataframe = dataframe[
            dataframe["business_unit"]
            .astype(str)
            .str.upper()
            == business_unit.strip().upper()
        ]

    return paginate(
        dataframe,
        page,
        page_size,
    )


@app.get("/api/insights")
def insights(
    priority: str | None = None,
    business_unit: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=20,
        ge=1,
        le=200,
    ),
):
    dataframe = read_sheet(
        CONSOLIDATED_INSIGHTS_FILE,
        "Consolidated Insights",
    )

    if priority:
        dataframe = dataframe[
            dataframe["priority"]
            .astype(str)
            .str.lower()
            == priority.strip().lower()
        ]

    if business_unit:
        dataframe = dataframe[
            dataframe["business_unit"]
            .astype(str)
            .str.upper()
            == business_unit.strip().upper()
        ]

    return paginate(
        dataframe,
        page,
        page_size,
    )


@app.get("/api/pipeline/latest")
def latest_pipeline():
    pipeline_log = read_json(
        LATEST_PIPELINE_LOG
    )

    if pipeline_log is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No pipeline execution log exists."
            ),
        )

    return pipeline_log


@app.get("/api/pipeline/history")
def pipeline_history():
    if not PIPELINE_HISTORY_FILE.exists():
        return {
            "count": 0,
            "results": [],
        }

    dataframe = pd.read_csv(
        PIPELINE_HISTORY_FILE
    )

    dataframe = dataframe.sort_values(
        by="started_at",
        ascending=False,
    )

    return {
        "count": len(dataframe),
        "results": dataframe_records(dataframe),
    }


@app.post("/api/pipeline/run")
def run_pipeline():
    if not ORCHESTRATOR_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Pipeline orchestrator is missing.",
        )

    result = subprocess.run(
        [
            sys.executable,
            str(ORCHESTRATOR_FILE),
        ],
        cwd=REPOSITORY_DIR,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Agent pipeline failed.",
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
        )

    return {
        "message": (
            "Agent pipeline completed successfully."
        ),
        "latest_run": read_json(
            LATEST_PIPELINE_LOG
        ),
        "output": result.stdout,
    }


@app.get("/api/download/dq-results")
def download_dq_results():
    return FileResponse(
        DQ_RESULTS_FILE,
        filename="dq_execution_results.xlsx",
    )


@app.get("/api/download/mappings")
def download_mappings():
    return FileResponse(
        MAPPINGS_FILE,
        filename=(
            "agent_bt_technical_mappings.xlsx"
        ),
    )


@app.get("/api/download/insights")
def download_insights():
    return FileResponse(
        CONSOLIDATED_INSIGHTS_FILE,
        filename="consolidated_dq_insights.xlsx",
    )


@app.get("/api/download/failed-records")
def download_failed_records():
    return FileResponse(
        FAILED_RECORDS_FILE,
        filename="dq_failed_records.csv",
    )