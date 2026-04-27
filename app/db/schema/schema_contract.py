from __future__ import annotations


def normalize_schema(raw_schema: dict, default_dialect: str = "sqlite", default_schema: str = "main") -> dict:
    """
    Normalize legacy and new schema JSON formats into a canonical structure.

    Canonical format:
    {
      "dialect": "sqlite" | "tsql" | ...,
      "schemas": {
        "<schema_name>": {
          "tables": {
            "<table_name>": {
              "columns": {...},
              "foreign_keys": [...]
            }
          }
        }
      },
      "tables": { ... }  # flattened convenience map, key = "schema.table"
    }
    """
    if not isinstance(raw_schema, dict):
        raise ValueError("Schema JSON must be an object")

    dialect = str(raw_schema.get("dialect") or default_dialect).lower()
    schemas: dict = {}

    if isinstance(raw_schema.get("schemas"), dict) and raw_schema["schemas"]:
        for schema_name, schema_payload in raw_schema["schemas"].items():
            tables = {}
            if isinstance(schema_payload, dict):
                tables = schema_payload.get("tables") or {}
            schemas[str(schema_name)] = {"tables": _normalize_tables_map(tables)}
    else:
        # Backward compatibility: old format with top-level "tables".
        legacy_tables = raw_schema.get("tables") or {}
        schemas[default_schema] = {"tables": _normalize_tables_map(legacy_tables)}

    flattened_tables = {}
    for schema_name, schema_payload in schemas.items():
        for table_name, table_payload in schema_payload.get("tables", {}).items():
            flattened_tables[f"{schema_name}.{table_name}"] = table_payload

    return {
        "dialect": dialect,
        "schemas": schemas,
        "tables": flattened_tables,
    }


def _normalize_tables_map(tables: dict) -> dict:
    normalized = {}
    for table_name, payload in (tables or {}).items():
        payload = payload or {}
        columns = payload.get("columns") or {}
        foreign_keys = payload.get("foreign_keys") or []
        normalized[str(table_name)] = {
            "columns": dict(columns),
            "foreign_keys": list(foreign_keys),
        }
    return normalized
