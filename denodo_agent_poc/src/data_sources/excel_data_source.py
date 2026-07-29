from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .base_data_source import (
        BaseDataSource,
        DataAsset,
    )
except ImportError:
    from base_data_source import (
        BaseDataSource,
        DataAsset,
    )


PROJECT_DIR = Path(__file__).resolve().parents[2]

DEFAULT_SOURCE_DIR = (
    PROJECT_DIR
    / "data"
    / "source"
)

DEFAULT_METADATA_FILE = (
    PROJECT_DIR
    / "data"
    / "metadata"
    / "technical_metadata.xlsx"
)


class ExcelDataSource(BaseDataSource):
    """
    Excel implementation of the Data Quality data-source interface.

    This adapter reads the enterprise dummy source files currently
    used by the agent pipeline. It can later be replaced with a
    Denodo adapter without changing the rest of the system.
    """

    source_type = "excel"

    def __init__(
        self,
        source_directory: str | Path = DEFAULT_SOURCE_DIR,
        metadata_file: str | Path = DEFAULT_METADATA_FILE,
    ):
        self.source_directory = Path(source_directory).resolve()
        self.metadata_file = Path(metadata_file).resolve()

        self._metadata_cache: pd.DataFrame | None = None
        self._asset_cache: list[DataAsset] | None = None

    def _load_metadata(self) -> pd.DataFrame:
        if self._metadata_cache is not None:
            return self._metadata_cache.copy()

        if not self.metadata_file.exists():
            raise FileNotFoundError(
                "Technical metadata file was not found: "
                f"{self.metadata_file}"
            )

        metadata = pd.read_excel(self.metadata_file)

        required_columns = {
            "business_unit",
            "schema_name",
            "table_name",
            "column_name",
        }

        missing_columns = (
            required_columns
            - set(metadata.columns)
        )

        if missing_columns:
            raise ValueError(
                "Technical metadata is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )

        metadata = metadata.copy()

        metadata["business_unit"] = (
            metadata["business_unit"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        metadata["schema_name"] = (
            metadata["schema_name"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        metadata["table_name"] = (
            metadata["table_name"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        metadata["column_name"] = (
            metadata["column_name"]
            .astype(str)
            .str.strip()
        )

        self._metadata_cache = metadata

        return metadata.copy()

    def _source_file_for_business_unit(
        self,
        business_unit: str,
    ) -> Path:
        filename = (
            f"{business_unit.strip().lower()}_source.xlsx"
        )

        return (
            self.source_directory
            / filename
        ).resolve()

    def list_assets(self) -> list[DataAsset]:
        if self._asset_cache is not None:
            return list(self._asset_cache)

        metadata = self._load_metadata()

        asset_columns = [
            "business_unit",
            "schema_name",
            "table_name",
        ]

        unique_assets = (
            metadata[asset_columns]
            .drop_duplicates()
            .sort_values(asset_columns)
        )

        assets: list[DataAsset] = []

        for row in unique_assets.itertuples(index=False):
            source_file = (
                self._source_file_for_business_unit(
                    row.business_unit
                )
            )

            assets.append(
                DataAsset(
                    business_unit=row.business_unit,
                    schema_name=row.schema_name,
                    table_name=row.table_name,
                    source_identifier=str(source_file),
                )
            )

        self._asset_cache = assets

        return list(assets)

    def read_asset(
        self,
        asset: DataAsset,
        columns: list[str] | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        source_file = Path(asset.source_identifier)

        if not source_file.exists():
            raise FileNotFoundError(
                "Excel source file was not found: "
                f"{source_file}"
            )

        if limit is not None and limit < 0:
            raise ValueError(
                "The record limit cannot be negative."
            )

        try:
            dataframe = pd.read_excel(
                source_file,
                usecols=columns,
                nrows=limit,
            )
        except ValueError as error:
            raise ValueError(
                f"Unable to read columns from {source_file.name}: "
                f"{error}"
            ) from error

        return dataframe

    def get_technical_metadata(self) -> pd.DataFrame:
        return self._load_metadata()

    def health_check(self) -> dict[str, Any]:
        problems: list[str] = []
        assets: list[DataAsset] = []
        total_records = 0

        if not self.source_directory.exists():
            problems.append(
                "Source directory does not exist: "
                f"{self.source_directory}"
            )

        if not self.metadata_file.exists():
            problems.append(
                "Technical metadata file does not exist: "
                f"{self.metadata_file}"
            )

        if not problems:
            try:
                assets = self.list_assets()
            except (
                FileNotFoundError,
                ValueError,
                KeyError,
            ) as error:
                problems.append(str(error))

        asset_results = []

        for asset in assets:
            source_file = Path(asset.source_identifier)

            asset_status = {
                "business_unit": asset.business_unit,
                "schema_name": asset.schema_name,
                "table_name": asset.table_name,
                "file": source_file.name,
                "exists": source_file.exists(),
                "records": 0,
                "columns": 0,
                "error": None,
            }

            if not source_file.exists():
                error_message = (
                    "Source file does not exist: "
                    f"{source_file}"
                )

                asset_status["error"] = error_message
                problems.append(error_message)
                asset_results.append(asset_status)
                continue

            try:
                dataframe = pd.read_excel(source_file)

                asset_status["records"] = len(dataframe)
                asset_status["columns"] = len(
                    dataframe.columns
                )

                total_records += len(dataframe)

                expected_columns = set(
                    self._load_metadata()
                    .loc[
                        (
                            self._load_metadata()[
                                "business_unit"
                            ]
                            == asset.business_unit
                        )
                        & (
                            self._load_metadata()[
                                "schema_name"
                            ]
                            == asset.schema_name
                        )
                        & (
                            self._load_metadata()[
                                "table_name"
                            ]
                            == asset.table_name
                        ),
                        "column_name",
                    ]
                    .astype(str)
                )

                actual_columns = set(
                    dataframe.columns.astype(str)
                )

                missing_columns = (
                    expected_columns
                    - actual_columns
                )

                if missing_columns:
                    error_message = (
                        f"{source_file.name} is missing "
                        "documented columns: "
                        + ", ".join(
                            sorted(missing_columns)
                        )
                    )

                    asset_status["error"] = error_message
                    problems.append(error_message)

            except Exception as error:
                error_message = (
                    f"Unable to read {source_file.name}: "
                    f"{error}"
                )

                asset_status["error"] = error_message
                problems.append(error_message)

            asset_results.append(asset_status)

        return {
            "status": (
                "healthy"
                if not problems
                else "unhealthy"
            ),
            "source_type": self.source_type,
            "source_directory": str(
                self.source_directory
            ),
            "metadata_file": str(
                self.metadata_file
            ),
            "asset_count": len(assets),
            "total_records": total_records,
            "problems": problems,
            "assets": asset_results,
        }


def main():
    data_source = ExcelDataSource()

    print("Excel Data Source Validation")
    print("=" * 50)

    health = data_source.health_check()

    print(f"Status: {health['status']}")
    print(f"Assets: {health['asset_count']}")
    print(
        "Total records: "
        f"{health['total_records']:,}"
    )

    for asset in health["assets"]:
        print(
            f"{asset['business_unit']}: "
            f"{asset['records']:,} records, "
            f"{asset['columns']} columns"
        )

        if asset["error"]:
            print(
                f"  ERROR: {asset['error']}"
            )

    if health["problems"]:
        print("\nProblems:")

        for problem in health["problems"]:
            print(f"- {problem}")

        raise SystemExit(1)

    print("=" * 50)
    print("EXCEL DATA SOURCE IS HEALTHY")


if __name__ == "__main__":
    main()