class SQLNormalizer:
    def normalize(self, text: str) -> str:
        sql = text.strip()
        if sql.endswith(";"):
            return sql
        return f"{sql};"
