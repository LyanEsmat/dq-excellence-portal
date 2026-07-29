from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class DataAsset:
    business_unit: str
    schema_name: str
    table_name: str
    source_identifier: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class BaseDataSource(ABC):
    """
    Standard interface used by the Data Quality agent pipeline.

    Excel and Denodo data sources must implement the same methods.
    This allows the pipeline to change data sources without changing
    the mapping, DQ execution, insights, API or dashboard code.
    """

    source_type = "base"

    @abstractmethod
    def list_assets(self) -> list[DataAsset]:
        """
        Return every physical data asset available for assessment.
        """
        raise NotImplementedError

    @abstractmethod
    def read_asset(
        self,
        asset: DataAsset,
        columns: list[str] | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """
        Read records from one physical data asset.

        Args:
            asset:
                The asset that should be loaded.
            columns:
                Optional list of columns to return.
            limit:
                Optional maximum number of records to return.
        """
        raise NotImplementedError

    @abstractmethod
    def get_technical_metadata(self) -> pd.DataFrame:
        """
        Return technical metadata for all available assets.
        """
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """
        Confirm that the data source is available and usable.
        """
        raise NotImplementedError

    def asset_exists(
        self,
        business_unit: str,
        table_name: str,
    ) -> bool:
        """
        Check whether a business unit and table combination exists.
        """
        normalized_business_unit = business_unit.strip().upper()
        normalized_table_name = table_name.strip().lower()

        return any(
            asset.business_unit.strip().upper()
            == normalized_business_unit
            and asset.table_name.strip().lower()
            == normalized_table_name
            for asset in self.list_assets()
        )

    def find_asset(
        self,
        business_unit: str,
        table_name: str,
    ) -> DataAsset:
        """
        Find one asset using its business unit and table name.
        """
        normalized_business_unit = business_unit.strip().upper()
        normalized_table_name = table_name.strip().lower()

        for asset in self.list_assets():
            if (
                asset.business_unit.strip().upper()
                == normalized_business_unit
                and asset.table_name.strip().lower()
                == normalized_table_name
            ):
                return asset

        raise KeyError(
            "Data asset was not found: "
            f"{normalized_business_unit}."
            f"{normalized_table_name}"
        )

    def describe(self) -> dict[str, Any]:
        """
        Return a summary of the configured data source.
        """
        assets = self.list_assets()

        return {
            "source_type": self.source_type,
            "asset_count": len(assets),
            "business_units": sorted(
                {
                    asset.business_unit
                    for asset in assets
                }
            ),
            "assets": [
                asset.to_dict()
                for asset in assets
            ],
        }