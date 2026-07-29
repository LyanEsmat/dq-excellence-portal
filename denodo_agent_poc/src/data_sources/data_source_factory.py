from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIRECTORY = PROJECT_DIR / "config"

if str(CONFIG_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(CONFIG_DIRECTORY),
    )


from deployment_settings import (  # noqa: E402
    DeploymentSettings,
    get_settings,
)

try:
    from .base_data_source import (
        BaseDataSource,
    )
    from .excel_data_source import (
        ExcelDataSource,
    )
except ImportError:
    from base_data_source import (
        BaseDataSource,
    )
    from excel_data_source import (
        ExcelDataSource,
    )


def create_data_source(
    settings: DeploymentSettings | None = None,
) -> BaseDataSource:
    """
    Create the configured pipeline data source.

    Excel is available now. Denodo will be activated after
    connection access and approved read-only credentials
    are provided.
    """
    if settings is None:
        settings = get_settings()

    if settings.data_source == "excel":
        return ExcelDataSource(
            source_directory=(
                settings.source_directory
            ),
            metadata_file=(
                settings.metadata_file
            ),
        )

    if settings.data_source == "denodo":
        raise NotImplementedError(
            "Denodo is selected, but the "
            "DenodoDataSource adapter has not "
            "been configured yet. Set "
            "DQ_DATA_SOURCE=excel until Denodo "
            "access is available."
        )

    raise ValueError(
        "Unsupported data source: "
        f"{settings.data_source}"
    )


def validate_configured_data_source():
    settings = get_settings()
    data_source = create_data_source(
        settings
    )

    health = data_source.health_check()

    if health["status"] != "healthy":
        raise RuntimeError(
            "Configured data source is unhealthy: "
            + "; ".join(
                health.get(
                    "problems",
                    [],
                )
            )
        )

    return {
        "settings": settings,
        "data_source": data_source,
        "health": health,
    }


def main():
    result = (
        validate_configured_data_source()
    )

    settings = result["settings"]
    data_source = result["data_source"]
    health = result["health"]

    print()
    print("Configured Data Source")
    print("=" * 50)
    print(
        f"Environment: "
        f"{settings.environment}"
    )
    print(
        f"Selected source: "
        f"{data_source.source_type}"
    )
    print(
        f"Status: {health['status']}"
    )
    print(
        f"Assets: {health['asset_count']}"
    )
    print(
        "Records: "
        f"{health['total_records']:,}"
    )
    print("=" * 50)
    print(
        "CONFIGURED DATA SOURCE IS READY"
    )
    print()


if __name__ == "__main__":
    main()