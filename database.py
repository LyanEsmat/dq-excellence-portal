from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DUMMY_DATA_DIR = BASE_DIR / "dummy_data"

DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "dq_platform.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


class BusinessTerm(Base):
    __tablename__ = "business_terms"

    id = Column(Integer, primary_key=True)
    business_term_id = Column(String(50), unique=True, nullable=False)
    business_term = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    domain = Column(String(50), nullable=False)
    owner = Column(String(150), nullable=False)
    criticality = Column(String(20), nullable=False)
    dq_dimension = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    mapping_candidates = relationship(
        "MappingCandidate",
        back_populates="business_term",
    )


class TechnicalAsset(Base):
    __tablename__ = "technical_assets"

    id = Column(Integer, primary_key=True)
    technical_asset_id = Column(String(50), unique=True, nullable=False)
    source_system = Column(String(100), nullable=False)
    schema_name = Column(String(100), nullable=False)
    table_name = Column(String(150), nullable=False)
    column_name = Column(String(150), nullable=False)
    data_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    domain = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    mapping_candidates = relationship(
        "MappingCandidate",
        back_populates="technical_asset",
    )


class MappingCandidate(Base):
    __tablename__ = "mapping_candidates"

    id = Column(Integer, primary_key=True)

    business_term_id = Column(
        Integer,
        ForeignKey("business_terms.id"),
        nullable=False,
    )

    technical_asset_id = Column(
        Integer,
        ForeignKey("technical_assets.id"),
        nullable=False,
    )

    name_similarity = Column(Float, nullable=False)
    description_similarity = Column(Float, nullable=False)
    domain_score = Column(Float, nullable=False)
    data_type_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)

    explanation = Column(Text, nullable=False)

    status = Column(
        String(30),
        default="Pending",
        nullable=False,
    )

    approved = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    reviewed_by = Column(String(150), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    business_term = relationship(
        "BusinessTerm",
        back_populates="mapping_candidates",
    )

    technical_asset = relationship(
        "TechnicalAsset",
        back_populates="mapping_candidates",
    )


class DQRule(Base):
    __tablename__ = "dq_rules"

    id = Column(Integer, primary_key=True)
    rule_code = Column(String(50), unique=True, nullable=False)

    mapping_candidate_id = Column(
        Integer,
        ForeignKey("mapping_candidates.id"),
        nullable=False,
    )

    business_term_name = Column(String(200), nullable=False)
    domain = Column(String(50), nullable=False)
    table_name = Column(String(150), nullable=False)
    column_name = Column(String(150), nullable=False)
    dimension = Column(String(50), nullable=False)

    rule_type = Column(String(50), nullable=False)
    rule_description = Column(Text, nullable=False)
    rule_parameters = Column(Text, nullable=True)

    severity = Column(String(20), default="Medium")
    threshold = Column(Float, default=95.0)
    status = Column(String(30), default="Active")

    created_at = Column(DateTime, default=datetime.utcnow)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True)
    run_name = Column(String(150), nullable=False)
    status = Column(String(30), default="Running")

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    total_rules = Column(Integer, default=0)
    passed_rules = Column(Integer, default=0)
    failed_rules = Column(Integer, default=0)
    overall_score = Column(Float, default=0.0)

    error_message = Column(Text, nullable=True)

    results = relationship(
        "DQResult",
        back_populates="pipeline_run",
    )


class DQResult(Base):
    __tablename__ = "dq_results"

    id = Column(Integer, primary_key=True)

    pipeline_run_id = Column(
        Integer,
        ForeignKey("pipeline_runs.id"),
        nullable=False,
    )

    dq_rule_id = Column(
        Integer,
        ForeignKey("dq_rules.id"),
        nullable=False,
    )

    rule_code = Column(String(50), nullable=False)
    business_term_name = Column(String(200), nullable=False)
    domain = Column(String(50), nullable=False)
    dimension = Column(String(50), nullable=False)
    column_name = Column(String(150), nullable=False)

    total_records = Column(Integer, nullable=False)
    passed_records = Column(Integer, nullable=False)
    failed_records = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)

    threshold = Column(Float, nullable=False)
    result_status = Column(String(30), nullable=False)

    failure_examples = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)

    pipeline_run = relationship(
        "PipelineRun",
        back_populates="results",
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True)

    pipeline_run_id = Column(
        Integer,
        ForeignKey("pipeline_runs.id"),
        nullable=False,
    )

    domain = Column(String(50), nullable=False)
    business_term_name = Column(String(200), nullable=False)
    dimension = Column(String(50), nullable=False)

    severity = Column(String(20), nullable=False)
    title = Column(String(250), nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    database = SessionLocal()

    try:
        yield database
    finally:
        database.close()


def clean_value(value):
    if pd.isna(value):
        return None

    return str(value).strip()


def load_business_terms(database):
    file_path = DUMMY_DATA_DIR / "business_terms.xlsx"

    if not file_path.exists():
        raise FileNotFoundError(
            "business_terms.xlsx was not found inside dummy_data."
        )

    dataframe = pd.read_excel(file_path)

    for _, row in dataframe.iterrows():
        identifier = clean_value(row["business_term_id"])

        record = (
            database.query(BusinessTerm)
            .filter(BusinessTerm.business_term_id == identifier)
            .first()
        )

        if record is None:
            record = BusinessTerm(
                business_term_id=identifier,
            )
            database.add(record)

        record.business_term = clean_value(row["business_term"])
        record.description = clean_value(row["description"])
        record.domain = clean_value(row["domain"])
        record.owner = clean_value(row["owner"])
        record.criticality = clean_value(row["criticality"])
        record.dq_dimension = clean_value(row["dq_dimension"])

    database.commit()

    return len(dataframe)


def load_technical_assets(database):
    file_path = DUMMY_DATA_DIR / "technical_metadata.xlsx"

    if not file_path.exists():
        raise FileNotFoundError(
            "technical_metadata.xlsx was not found inside dummy_data."
        )

    dataframe = pd.read_excel(file_path)

    for _, row in dataframe.iterrows():
        identifier = clean_value(row["technical_asset_id"])

        record = (
            database.query(TechnicalAsset)
            .filter(TechnicalAsset.technical_asset_id == identifier)
            .first()
        )

        if record is None:
            record = TechnicalAsset(
                technical_asset_id=identifier,
            )
            database.add(record)

        record.source_system = clean_value(row["source_system"])
        record.schema_name = clean_value(row["schema_name"])
        record.table_name = clean_value(row["table_name"])
        record.column_name = clean_value(row["column_name"])
        record.data_type = clean_value(row["data_type"])
        record.description = clean_value(row["description"])
        record.domain = clean_value(row["domain"])

    database.commit()

    return len(dataframe)


def initialize_database():
    Base.metadata.create_all(bind=engine)

    database = SessionLocal()

    try:
        business_term_count = load_business_terms(database)
        technical_asset_count = load_technical_assets(database)

        stored_business_terms = database.query(BusinessTerm).count()
        stored_technical_assets = database.query(TechnicalAsset).count()

        print("Database initialized successfully.")
        print(f"Database location: {DATABASE_PATH}")
        print(f"Business terms loaded: {business_term_count}")
        print(f"Technical assets loaded: {technical_asset_count}")
        print(f"Stored business terms: {stored_business_terms}")
        print(f"Stored technical assets: {stored_technical_assets}")

    except Exception:
        database.rollback()
        raise

    finally:
        database.close()


if __name__ == "__main__":
    initialize_database()