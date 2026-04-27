from __future__ import annotations

from collections import defaultdict

import pyodbc


def extract_mssql_schema(connection_string: str, include_schemas: list[str] | None = None) -> dict:
    include_filter = {s.lower() for s in (include_schemas or [])}
    conn = pyodbc.connect(connection_string)
    conn.timeout = 60

    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
              s.name AS schema_name,
              t.name AS table_name
            FROM sys.tables t
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            ORDER BY s.name, t.name
            """
        )
        table_rows = cur.fetchall()

        schema_tables: dict[str, dict[str, dict]] = defaultdict(dict)
        for row in table_rows:
            schema_name = str(row.schema_name)
            if include_filter and schema_name.lower() not in include_filter:
                continue
            table_name = str(row.table_name)
            schema_tables[schema_name][table_name] = {"columns": {}, "foreign_keys": []}

        cur.execute(
            """
            SELECT
              s.name AS schema_name,
              t.name AS table_name,
              c.name AS column_name,
              ty.name AS data_type
            FROM sys.columns c
            INNER JOIN sys.tables t ON c.object_id = t.object_id
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            INNER JOIN sys.types ty ON c.user_type_id = ty.user_type_id
            ORDER BY s.name, t.name, c.column_id
            """
        )
        column_rows = cur.fetchall()
        for row in column_rows:
            schema_name = str(row.schema_name)
            table_name = str(row.table_name)
            if schema_name not in schema_tables or table_name not in schema_tables[schema_name]:
                continue
            schema_tables[schema_name][table_name]["columns"][str(row.column_name)] = str(row.data_type)

        cur.execute(
            """
            SELECT
              sch_from.name AS from_schema,
              t_from.name AS from_table,
              c_from.name AS from_column,
              sch_to.name AS to_schema,
              t_to.name AS to_table,
              c_to.name AS to_column
            FROM sys.foreign_key_columns fkc
            INNER JOIN sys.tables t_from ON fkc.parent_object_id = t_from.object_id
            INNER JOIN sys.schemas sch_from ON t_from.schema_id = sch_from.schema_id
            INNER JOIN sys.columns c_from
              ON fkc.parent_object_id = c_from.object_id AND fkc.parent_column_id = c_from.column_id
            INNER JOIN sys.tables t_to ON fkc.referenced_object_id = t_to.object_id
            INNER JOIN sys.schemas sch_to ON t_to.schema_id = sch_to.schema_id
            INNER JOIN sys.columns c_to
              ON fkc.referenced_object_id = c_to.object_id AND fkc.referenced_column_id = c_to.column_id
            ORDER BY sch_from.name, t_from.name
            """
        )
        fk_rows = cur.fetchall()
        for row in fk_rows:
            from_schema = str(row.from_schema)
            from_table = str(row.from_table)
            if from_schema not in schema_tables or from_table not in schema_tables[from_schema]:
                continue
            schema_tables[from_schema][from_table]["foreign_keys"].append(
                {
                    "from": str(row.from_column),
                    "to_schema": str(row.to_schema),
                    "to_table": str(row.to_table),
                    "to": str(row.to_column),
                }
            )

        schemas_payload = {
            schema_name: {"tables": tables}
            for schema_name, tables in sorted(schema_tables.items(), key=lambda item: item[0].lower())
        }
        flat_tables = {
            f"{schema_name}.{table_name}": table_payload
            for schema_name, schema_data in schemas_payload.items()
            for table_name, table_payload in schema_data["tables"].items()
        }

        return {
            "dialect": "tsql",
            "schemas": schemas_payload,
            "tables": flat_tables,
        }
    finally:
        conn.close()
