from __future__ import annotations

import sqlite3


def extract_sqlite_schema(db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        table_rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        tables: dict[str, dict] = {}
        for row in table_rows:
            table = row["name"]
            col_rows = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
            fk_rows = conn.execute(f"PRAGMA foreign_key_list('{table}')").fetchall()

            columns: dict[str, str] = {}
            for col in col_rows:
                columns[col["name"]] = col["type"] or "TEXT"

            foreign_keys = [
                {
                    "from": fk["from"],
                    "to_table": fk["table"],
                    "to": fk["to"],
                }
                for fk in fk_rows
            ]

            tables[table] = {
                "columns": columns,
                "foreign_keys": foreign_keys,
            }

        return {
            "dialect": "sqlite",
            "schemas": {
                "main": {
                    "tables": tables,
                }
            },
            # flattened convenience map used by some layers
            "tables": {f"main.{table_name}": table_payload for table_name, table_payload in tables.items()},
        }
    finally:
        conn.close()
