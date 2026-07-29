from pathlib import Path
import sys

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE_CODE_DIR = PROJECT_DIR / "src"

sys.path.insert(
    0,
    str(SOURCE_CODE_DIR),
)

from data_sources import (  # noqa: E402
    DataAsset,
    ExcelDataSource,
)


EXPECTED_BUSINESS_UNITS = {
    "ALU",
    "FIN",
    "GGM",
    "HR",
    "PDE",
    "PHO",
    "PRO",
}

EXPECTED_ASSET_COUNT = 7
EXPECTED_ROWS_PER_ASSET = 8_000
EXPECTED_TOTAL_RECORDS = 56_000
EXPECTED_COLUMNS_PER_ASSET = 9
EXPECTED_METADATA_ROWS = 63


def check(
    condition: bool,
    message: str,
):
    if not condition:
        raise AssertionError(message)

    print(f"PASSED: {message}")


def test_asset_discovery(
    data_source: ExcelDataSource,
):
    assets = data_source.list_assets()

    check(
        len(assets) == EXPECTED_ASSET_COUNT,
        "Seven source assets discovered",
    )

    check(
        all(
            isinstance(asset, DataAsset)
            for asset in assets
        ),
        "All discovered assets use DataAsset",
    )

    business_units = {
        asset.business_unit
        for asset in assets
    }

    check(
        business_units
        == EXPECTED_BUSINESS_UNITS,
        "All expected Business Units discovered",
    )

    check(
        len(
            {
                (
                    asset.business_unit,
                    asset.schema_name,
                    asset.table_name,
                )
                for asset in assets
            }
        )
        == EXPECTED_ASSET_COUNT,
        "No duplicate source assets",
    )


def test_metadata(
    data_source: ExcelDataSource,
):
    metadata = (
        data_source.get_technical_metadata()
    )

    check(
        isinstance(metadata, pd.DataFrame),
        "Technical metadata returned as a DataFrame",
    )

    check(
        len(metadata)
        == EXPECTED_METADATA_ROWS,
        "63 technical columns documented",
    )

    required_columns = {
        "business_unit",
        "schema_name",
        "table_name",
        "column_name",
    }

    check(
        required_columns.issubset(
            metadata.columns
        ),
        "Required metadata fields are available",
    )

    check(
        metadata["column_name"]
        .notna()
        .all(),
        "No technical metadata column name is missing",
    )


def test_asset_lookup(
    data_source: ExcelDataSource,
):
    for asset in data_source.list_assets():
        check(
            data_source.asset_exists(
                asset.business_unit,
                asset.table_name,
            ),
            (
                "Asset lookup works for "
                f"{asset.business_unit}"
            ),
        )

        selected_asset = (
            data_source.find_asset(
                asset.business_unit,
                asset.table_name,
            )
        )

        check(
            selected_asset == asset,
            (
                "Correct asset returned for "
                f"{asset.business_unit}"
            ),
        )

    check(
        not data_source.asset_exists(
            "UNKNOWN",
            "missing_table",
        ),
        "Unknown assets are rejected",
    )


def test_selective_reading(
    data_source: ExcelDataSource,
):
    asset = data_source.list_assets()[0]

    metadata = (
        data_source.get_technical_metadata()
    )

    expected_columns = (
        metadata.loc[
            (
                metadata["business_unit"]
                == asset.business_unit
            )
            & (
                metadata["schema_name"]
                == asset.schema_name
            )
            & (
                metadata["table_name"]
                == asset.table_name
            ),
            "column_name",
        ]
        .astype(str)
        .tolist()
    )

    selected_columns = expected_columns[:2]

    sample = data_source.read_asset(
        asset=asset,
        columns=selected_columns,
        limit=25,
    )

    check(
        len(sample) == 25,
        "Record limit is applied",
    )

    check(
        list(sample.columns)
        == selected_columns,
        "Only requested columns are loaded",
    )


def test_all_source_records(
    data_source: ExcelDataSource,
):
    total_records = 0

    for asset in data_source.list_assets():
        dataframe = data_source.read_asset(
            asset
        )

        check(
            len(dataframe)
            == EXPECTED_ROWS_PER_ASSET,
            (
                f"{asset.business_unit} contains "
                "8,000 records"
            ),
        )

        check(
            len(dataframe.columns)
            == EXPECTED_COLUMNS_PER_ASSET,
            (
                f"{asset.business_unit} contains "
                "9 columns"
            ),
        )

        total_records += len(dataframe)

    check(
        total_records
        == EXPECTED_TOTAL_RECORDS,
        "56,000 total source records loaded",
    )


def test_health_check(
    data_source: ExcelDataSource,
):
    health = data_source.health_check()

    check(
        health["status"] == "healthy",
        "Excel data source health is healthy",
    )

    check(
        health["asset_count"]
        == EXPECTED_ASSET_COUNT,
        "Health check reports seven assets",
    )

    check(
        health["total_records"]
        == EXPECTED_TOTAL_RECORDS,
        "Health check reports 56,000 records",
    )

    check(
        not health["problems"],
        "Health check reports no problems",
    )


def run_tests():
    print()
    print("Excel Data Source Adapter Tests")
    print("=" * 50)

    data_source = ExcelDataSource()

    test_asset_discovery(data_source)
    test_metadata(data_source)
    test_asset_lookup(data_source)
    test_selective_reading(data_source)
    test_all_source_records(data_source)
    test_health_check(data_source)

    print("=" * 50)
    print("ALL EXCEL DATA SOURCE TESTS PASSED")
    print()


if __name__ == "__main__":
    run_tests()