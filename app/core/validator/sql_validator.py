from __future__ import annotations

import re

from sqlglot import exp, parse


class SQLValidator:
    def __init__(self, schema: dict, sql_dialect: str = "sqlite") -> None:
        self.schema = schema
        self.sql_dialect = sql_dialect
        self.qualified_tables, self.unqualified_tables = self._build_table_indexes(schema)
        self.columns_by_qualified_table, self.columns_by_unqualified_table, self.global_columns = (
            self._build_column_indexes(schema)
        )

    def validate(self, sql: str) -> tuple[bool, str]:
        if not sql.strip():
            return False, "Empty SQL"

        statements = [s for s in parse(sql, read=self.sql_dialect) if s is not None]
        if len(statements) != 1:
            return False, "SQL must contain exactly one statement"

        statement = statements[0]

        # Only SELECT or WITH ... SELECT.
        if not isinstance(statement, exp.Select) and not statement.find(exp.Select):
            return False, "Only SELECT queries are allowed"

        disallowed = (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Alter)
        if any(statement.find(kind) for kind in disallowed):
            return False, "DML/DDL statements are not allowed"

        cte_names = {name.lower() for name in self._collect_cte_names(statement)}
        cte_names.update(name.lower() for name in self._collect_cte_names_from_sql(sql))
        table_refs = [(t.name, t.db) for t in statement.find_all(exp.Table)]
        if not table_refs:
            return False, "Query must reference at least one table"

        for table_name_raw, schema_name_raw in table_refs:
            table_name = self._normalize_identifier(table_name_raw)
            schema_name = self._normalize_identifier(schema_name_raw)
            if table_name in cte_names:
                continue
            if schema_name:
                qualified = f"{schema_name}.{table_name}"
                if qualified not in self.qualified_tables:
                    return False, f"Unknown table: {schema_name_raw}.{table_name_raw}"
            else:
                if table_name not in self.unqualified_tables:
                    return False, f"Unknown table: {table_name_raw}"

        for col in statement.find_all(exp.Column):
            col_name = col.name
            table_qualifier = col.table
            if not col_name:
                continue
            if table_qualifier:
                qualifier = self._normalize_identifier(table_qualifier)
                column_name = col_name.lower()

                if qualifier in self.columns_by_qualified_table:
                    if column_name not in self.columns_by_qualified_table[qualifier]:
                        return False, f"Unknown column {table_qualifier}.{col_name}"
                    continue

                if qualifier in self.columns_by_unqualified_table:
                    if column_name not in self.columns_by_unqualified_table[qualifier]:
                        return False, f"Unknown column {table_qualifier}.{col_name}"
                    continue

                # Could be alias; keep MVP behavior permissive for alias resolution.
                continue
            else:
                if col_name.lower() not in self.global_columns:
                    return False, f"Unknown column: {col_name}"

        return True, "ok"

    @staticmethod
    def _collect_cte_names(statement: exp.Expression) -> set[str]:
        names: set[str] = set()
        for cte in statement.find_all(exp.CTE):
            alias = cte.alias_or_name
            if alias:
                names.add(alias)
        return names

    @staticmethod
    def _collect_cte_names_from_sql(sql: str) -> set[str]:
        """Fallback CTE detection for parser/runtime differences."""
        if "with" not in sql.lower():
            return set()
        pattern = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s+AS\s*\(", re.IGNORECASE)
        return {match.group(1) for match in pattern.finditer(sql)}

    @staticmethod
    def _normalize_identifier(value: str | None) -> str:
        if not value:
            return ""
        text = str(value).strip().strip("[]").strip('"').strip("`")
        return text.lower()

    def _build_table_indexes(self, schema: dict) -> tuple[set[str], set[str]]:
        qualified: set[str] = set()
        unqualified: set[str] = set()
        for schema_name, schema_payload in schema.get("schemas", {}).items():
            for table_name in schema_payload.get("tables", {}).keys():
                s = self._normalize_identifier(schema_name)
                t = self._normalize_identifier(table_name)
                qualified.add(f"{s}.{t}")
                unqualified.add(t)
        return qualified, unqualified

    def _build_column_indexes(self, schema: dict) -> tuple[dict[str, set[str]], dict[str, set[str]], set[str]]:
        by_qualified: dict[str, set[str]] = {}
        by_unqualified: dict[str, set[str]] = {}
        global_columns: set[str] = set()

        for schema_name, schema_payload in schema.get("schemas", {}).items():
            s = self._normalize_identifier(schema_name)
            for table_name, table_payload in schema_payload.get("tables", {}).items():
                t = self._normalize_identifier(table_name)
                columns = {self._normalize_identifier(col) for col in table_payload.get("columns", {}).keys()}
                by_qualified[f"{s}.{t}"] = set(columns)
                by_unqualified[t] = by_unqualified.get(t, set()).union(columns)
                global_columns = global_columns.union(columns)

        return by_qualified, by_unqualified, global_columns
