from pathlib import Path
import sys


SOURCE_CODE_DIRECTORY = (
    Path(__file__).resolve().parents[1]
)

if (
    str(SOURCE_CODE_DIRECTORY)
    not in sys.path
):
    sys.path.insert(
        0,
        str(SOURCE_CODE_DIRECTORY),
    )


from data_sources import (  # noqa: E402
    create_data_source,
)

from batch_dq_executor_v3 import (  # noqa: E402
    run_batch_dq_execution_v3,
)


def run_configured_dq_execution():
    """
    Run DQ execution using the data source selected
    by deployment configuration.

    Current:
        DQ_DATA_SOURCE=excel

    Future:
        DQ_DATA_SOURCE=denodo
    """
    data_source = create_data_source()

    print()
    print(
        "Deployment data-source "
        "configuration loaded."
    )
    print(
        "Selected data source: "
        f"{data_source.source_type}"
    )

    return run_batch_dq_execution_v3(
        data_source=data_source
    )


if __name__ == "__main__":
    run_configured_dq_execution()