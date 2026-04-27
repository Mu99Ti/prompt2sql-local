from __future__ import annotations

from pathlib import Path


class PromptBuilder:
    def __init__(self, prompt_version: str, sql_dialect: str) -> None:
        self.prompt_version = prompt_version
        self.sql_dialect = sql_dialect
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        prompt_file = Path("prompts/base/sql_system_prompt.txt")
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8").strip()
        return (
            "You are a SQL generator. Output exactly one SQLite SELECT query and nothing else. "
            "No markdown, no explanation, no comments."
        )

    def build(self, question: str, schema: dict) -> str:
        schema_text = self._format_schema(schema)
        return (
            f"{self.system_prompt}\n\n"
            "Rules:\n"
            "1) Output one SQL statement only.\n"
            "2) Allowed statements: SELECT (including WITH ... SELECT).\n"
            "3) Use only tables and columns from schema.\n"
            "4) Do not include markdown fences or prose.\n\n"
            f"SQL Dialect: {self.sql_dialect}\n"
            f"Prompt Version: {self.prompt_version}\n\n"
            f"Schema:\n{schema_text}\n\n"
            f"Question:\n{question}\n\n"
            "SQL:"
        )

    @staticmethod
    def _format_schema(schema: dict) -> str:
        lines: list[str] = []
        schemas = schema.get("schemas", {})
        for schema_name in sorted(schemas.keys(), key=lambda x: x.lower()):
            tables = schemas[schema_name].get("tables", {})
            for table_name in sorted(tables.keys(), key=lambda x: x.lower()):
                columns = tables[table_name].get("columns", {})
                cols = ", ".join(f"{c} ({t})" for c, t in columns.items())
                lines.append(f"- {schema_name}.{table_name}: {cols}")
        return "\n".join(lines)
