from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo
import os
import re


PROJECT_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_DIR = PROJECT_DIR.parent
ENV_FILE = REPOSITORY_DIR / ".env"


def load_environment_file(
    file_path: Path = ENV_FILE,
):
    """
    Load simple KEY=VALUE settings without requiring
    an additional Python package.

    Existing operating-system environment variables
    always take priority over values in .env.
    """
    if not file_path.exists():
        return

    for raw_line in file_path.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split(
            "=",
            maxsplit=1,
        )

        key = key.strip()
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        os.environ.setdefault(
            key,
            value,
        )


def environment_value(
    name: str,
    default: str = "",
) -> str:
    return os.getenv(
        name,
        default,
    ).strip()


def boolean_value(
    name: str,
    default: bool = False,
) -> bool:
    default_text = (
        "true"
        if default
        else "false"
    )

    value = environment_value(
        name,
        default_text,
    ).lower()

    true_values = {
        "true",
        "1",
        "yes",
        "on",
    }

    false_values = {
        "false",
        "0",
        "no",
        "off",
    }

    if value in true_values:
        return True

    if value in false_values:
        return False

    raise ValueError(
        f"{name} must be true or false, "
        f"not '{value}'."
    )


def integer_value(
    name: str,
    default: int,
) -> int:
    value = environment_value(
        name,
        str(default),
    )

    try:
        return int(value)
    except ValueError as error:
        raise ValueError(
            f"{name} must be an integer, "
            f"not '{value}'."
        ) from error


def resolve_project_path(
    value: str,
) -> Path:
    path = Path(value)

    if path.is_absolute():
        return path.resolve()

    return (
        REPOSITORY_DIR
        / path
    ).resolve()


@dataclass(frozen=True)
class DeploymentSettings:
    environment: str
    host: str
    port: int
    log_level: str

    data_source: str
    runtime_directory: Path
    source_directory: Path
    results_directory: Path
    metadata_file: Path

    schedule_enabled: bool
    schedule_time: str
    timezone: str

    denodo_host: str
    denodo_port: int
    denodo_database: str
    denodo_username: str
    denodo_password: str
    denodo_ssl_enabled: bool

    api_auth_enabled: bool
    api_key: str

    def validate(self):
        allowed_environments = {
            "development",
            "test",
            "production",
        }

        if (
            self.environment
            not in allowed_environments
        ):
            raise ValueError(
                "DQ_ENVIRONMENT must be one of: "
                "development, test, production."
            )

        if self.data_source not in {
            "excel",
            "denodo",
        }:
            raise ValueError(
                "DQ_DATA_SOURCE must be "
                "'excel' or 'denodo'."
            )

        if not 1 <= self.port <= 65535:
            raise ValueError(
                "DQ_PORT must be between "
                "1 and 65535."
            )

        if not 1 <= self.denodo_port <= 65535:
            raise ValueError(
                "DENODO_PORT must be between "
                "1 and 65535."
            )

        if not re.fullmatch(
            r"(?:[01]\d|2[0-3]):[0-5]\d",
            self.schedule_time,
        ):
            raise ValueError(
                "DQ_SCHEDULE_TIME must use "
                "24-hour HH:MM format."
            )

        try:
            ZoneInfo(self.timezone)
        except Exception as error:
            raise ValueError(
                "DQ_TIMEZONE is invalid: "
                f"{self.timezone}"
            ) from error

        if self.data_source == "excel":
            if not self.source_directory.exists():
                raise ValueError(
                    "Excel source directory "
                    "does not exist: "
                    f"{self.source_directory}"
                )

            if not self.metadata_file.exists():
                raise ValueError(
                    "Technical metadata file "
                    "does not exist: "
                    f"{self.metadata_file}"
                )

        if self.data_source == "denodo":
            required_denodo_values = {
                "DENODO_HOST": self.denodo_host,
                "DENODO_DATABASE": (
                    self.denodo_database
                ),
                "DENODO_USERNAME": (
                    self.denodo_username
                ),
                "DENODO_PASSWORD": (
                    self.denodo_password
                ),
            }

            missing_values = [
                name
                for name, value
                in required_denodo_values.items()
                if (
                    not value
                    or value.startswith(
                        "replace-with"
                    )
                )
            ]

            if missing_values:
                raise ValueError(
                    "Denodo configuration is "
                    "incomplete: "
                    + ", ".join(missing_values)
                )

        if (
            self.api_auth_enabled
            and not self.api_key
        ):
            raise ValueError(
                "DQ_API_KEY is required when "
                "DQ_API_AUTH_ENABLED=true."
            )

        return self

    def safe_summary(self) -> dict:
        """
        Return configuration information without
        exposing passwords or API keys.
        """
        return {
            "environment": self.environment,
            "host": self.host,
            "port": self.port,
            "log_level": self.log_level,
            "data_source": self.data_source,
            "runtime_directory": str(
                self.runtime_directory
            ),
            "source_directory": str(
                self.source_directory
            ),
            "results_directory": str(
                self.results_directory
            ),
            "metadata_file": str(
                self.metadata_file
            ),
            "schedule_enabled": (
                self.schedule_enabled
            ),
            "schedule_time": (
                self.schedule_time
            ),
            "timezone": self.timezone,
            "denodo_configured": all(
                [
                    self.denodo_host,
                    self.denodo_database,
                    self.denodo_username,
                    self.denodo_password,
                ]
            )
            and not self.denodo_host.startswith(
                "replace-with"
            ),
            "denodo_ssl_enabled": (
                self.denodo_ssl_enabled
            ),
            "api_auth_enabled": (
                self.api_auth_enabled
            ),
        }


def get_settings() -> DeploymentSettings:
    load_environment_file()

    settings = DeploymentSettings(
        environment=environment_value(
            "DQ_ENVIRONMENT",
            "development",
        ).lower(),
        host=environment_value(
            "DQ_HOST",
            "0.0.0.0",
        ),
        port=integer_value(
            "DQ_PORT",
            8000,
        ),
        log_level=environment_value(
            "DQ_LOG_LEVEL",
            "INFO",
        ).upper(),
        data_source=environment_value(
            "DQ_DATA_SOURCE",
            "excel",
        ).lower(),
        runtime_directory=resolve_project_path(
            environment_value(
                "DQ_RUNTIME_DIRECTORY",
                "denodo_agent_poc/runtime_data",
            )
        ),
        source_directory=resolve_project_path(
            environment_value(
                "DQ_SOURCE_DIRECTORY",
                "denodo_agent_poc/data/source",
            )
        ),
        results_directory=resolve_project_path(
            environment_value(
                "DQ_RESULTS_DIRECTORY",
                "denodo_agent_poc/data/results",
            )
        ),
        metadata_file=resolve_project_path(
            environment_value(
                "DQ_METADATA_FILE",
                (
                    "denodo_agent_poc/data/"
                    "metadata/"
                    "technical_metadata.xlsx"
                ),
            )
        ),
        schedule_enabled=boolean_value(
            "DQ_SCHEDULE_ENABLED",
            False,
        ),
        schedule_time=environment_value(
            "DQ_SCHEDULE_TIME",
            "06:00",
        ),
        timezone=environment_value(
            "DQ_TIMEZONE",
            "Asia/Riyadh",
        ),
        denodo_host=environment_value(
            "DENODO_HOST"
        ),
        denodo_port=integer_value(
            "DENODO_PORT",
            9999,
        ),
        denodo_database=environment_value(
            "DENODO_DATABASE"
        ),
        denodo_username=environment_value(
            "DENODO_USERNAME"
        ),
        denodo_password=environment_value(
            "DENODO_PASSWORD"
        ),
        denodo_ssl_enabled=boolean_value(
            "DENODO_SSL_ENABLED",
            True,
        ),
        api_auth_enabled=boolean_value(
            "DQ_API_AUTH_ENABLED",
            False,
        ),
        api_key=environment_value(
            "DQ_API_KEY"
        ),
    )

    settings.runtime_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return settings.validate()


def main():
    settings = get_settings()

    print()
    print("Deployment Configuration")
    print("=" * 50)

    for key, value in (
        settings.safe_summary().items()
    ):
        print(f"{key}: {value}")

    print("=" * 50)
    print(
        "DEPLOYMENT CONFIGURATION IS VALID"
    )
    print()


if __name__ == "__main__":
    main()