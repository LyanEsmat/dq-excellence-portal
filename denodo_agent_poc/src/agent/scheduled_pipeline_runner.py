from datetime import (
    datetime,
    timedelta,
)
from pathlib import Path
from zoneinfo import ZoneInfo
import signal
import sys
import time


PROJECT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIRECTORY = PROJECT_DIR / "config"

if str(CONFIG_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(CONFIG_DIRECTORY),
    )


from deployment_settings import (  # noqa: E402
    get_settings,
)

from pipeline_orchestrator_v3 import (  # noqa: E402
    run_pipeline_v3,
)


shutdown_requested = False


def request_shutdown(
    signal_number,
    frame,
):
    global shutdown_requested

    shutdown_requested = True

    print()
    print(
        "Scheduler shutdown requested."
    )


def parse_schedule_time(
    schedule_time: str,
) -> tuple[int, int]:
    hour_text, minute_text = (
        schedule_time.split(":")
    )

    return (
        int(hour_text),
        int(minute_text),
    )


def calculate_next_run(
    schedule_time: str,
    timezone_name: str,
) -> datetime:
    timezone = ZoneInfo(
        timezone_name
    )

    current_time = datetime.now(
        timezone
    )

    hour, minute = parse_schedule_time(
        schedule_time
    )

    next_run = current_time.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )

    if next_run <= current_time:
        next_run += timedelta(
            days=1
        )

    return next_run


def wait_until(
    target_time: datetime,
):
    while not shutdown_requested:
        current_time = datetime.now(
            target_time.tzinfo
        )

        remaining_seconds = (
            target_time
            - current_time
        ).total_seconds()

        if remaining_seconds <= 0:
            return True

        time.sleep(
            min(
                remaining_seconds,
                60,
            )
        )

    return False


def execute_scheduled_pipeline():
    started_at = datetime.now(
        ZoneInfo("Asia/Riyadh")
    )

    print()
    print("=" * 60)
    print("SCHEDULED DATA QUALITY PIPELINE")
    print("=" * 60)
    print(
        f"Triggered: "
        f"{started_at.isoformat()}"
    )

    try:
        run_pipeline_v3(
            trigger="Scheduled"
        )

        print(
            "Scheduled pipeline "
            "completed successfully."
        )

        return True

    except SystemExit as error:
        print(
            "Scheduled pipeline failed "
            f"with exit code {error.code}."
        )

        return False

    except Exception as error:
        print(
            "Scheduled pipeline failed: "
            f"{error}"
        )

        return False


def run_scheduler():
    settings = get_settings()

    print()
    print("Data Quality Pipeline Scheduler")
    print("=" * 60)
    print(
        "Enabled: "
        f"{settings.schedule_enabled}"
    )
    print(
        "Schedule: "
        f"{settings.schedule_time}"
    )
    print(
        "Timezone: "
        f"{settings.timezone}"
    )
    print(
        "Data source: "
        f"{settings.data_source}"
    )

    if not settings.schedule_enabled:
        print("=" * 60)
        print(
            "Scheduler is disabled. Set "
            "DQ_SCHEDULE_ENABLED=true only "
            "in the approved deployment "
            "environment."
        )
        print()

        return

    signal.signal(
        signal.SIGTERM,
        request_shutdown,
    )

    signal.signal(
        signal.SIGINT,
        request_shutdown,
    )

    print("=" * 60)
    print(
        "Scheduler started successfully."
    )

    while not shutdown_requested:
        next_run = calculate_next_run(
            schedule_time=(
                settings.schedule_time
            ),
            timezone_name=(
                settings.timezone
            ),
        )

        print()
        print(
            "Next scheduled execution: "
            f"{next_run.isoformat()}"
        )

        should_execute = wait_until(
            next_run
        )

        if (
            should_execute
            and not shutdown_requested
        ):
            execute_scheduled_pipeline()

    print(
        "Scheduler stopped safely."
    )


if __name__ == "__main__":
    run_scheduler()