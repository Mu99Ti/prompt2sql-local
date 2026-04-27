import json
from pathlib import Path


class FileSchemaCache:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def save(self, schema: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
