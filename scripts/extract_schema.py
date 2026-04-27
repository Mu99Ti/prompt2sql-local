import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.cache.file_schema_cache import FileSchemaCache
from app.db.introspection.sqlite_schema_introspector import extract_sqlite_schema


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract SQLite schema into JSON")
    parser.add_argument("--db", required=True, help="Path to SQLite database file")
    parser.add_argument("--out", required=True, help="Output schema JSON path")
    args = parser.parse_args()

    schema = extract_sqlite_schema(args.db)
    FileSchemaCache(args.out).save(schema)
    print(f"Schema written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
