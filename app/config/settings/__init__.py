import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str
    service_name: str
    ollama_url: str
    model: str
    temperature: float
    sql_dialect: str
    schema_path: str
    prompt_version: str
    max_attempts: int
    request_timeout_sec: int
    log_format: str
    log_to_stdout: bool
    log_to_file: bool
    log_path: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_env=os.getenv("SQL_AGENT_ENV", "development"),
            service_name=os.getenv("SQL_AGENT_SERVICE_NAME", "sql-agent"),
            ollama_url=os.getenv("SQL_AGENT_OLLAMA_URL", "http://localhost:11434"),
            model=os.getenv("SQL_AGENT_MODEL", "gemma3:4b"),
            temperature=_get_float("SQL_AGENT_TEMPERATURE", 0.1),
            sql_dialect=os.getenv("SQL_AGENT_SQL_DIALECT", "sqlite").lower(),
            schema_path=os.getenv("SQL_AGENT_SCHEMA_PATH", "schemas/northwind_schema.json"),
            prompt_version=os.getenv("SQL_AGENT_PROMPT_VERSION", "v1"),
            max_attempts=_get_int("SQL_AGENT_MAX_ATTEMPTS", 2),
            request_timeout_sec=_get_int("SQL_AGENT_REQUEST_TIMEOUT_SEC", 120),
            log_format=os.getenv("SQL_AGENT_LOG_FORMAT", "json"),
            log_to_stdout=_get_bool("SQL_AGENT_LOG_TO_STDOUT", True),
            log_to_file=_get_bool("SQL_AGENT_LOG_TO_FILE", False),
            log_path=os.getenv("SQL_AGENT_LOG_PATH", "logs/runs.jsonl"),
        )


def _get_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_float(key: str, default: float) -> float:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default
