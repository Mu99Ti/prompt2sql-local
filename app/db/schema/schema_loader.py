import json
from pathlib import Path

from app.db.schema.schema_contract import normalize_schema


class SchemaLoader:
    def __init__(self, schema_path: str, sql_dialect: str = "sqlite") -> None:
        self.schema_path = Path(schema_path)
        self.sql_dialect = sql_dialect

    def load(self) -> dict:
        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found: {self.schema_path}. Run scripts/extract_schema.py first."
            )
        raw = json.loads(self.schema_path.read_text(encoding="utf-8"))
        default_schema = "dbo" if self.sql_dialect == "tsql" else "main"
        return normalize_schema(raw, default_dialect=self.sql_dialect, default_schema=default_schema)
