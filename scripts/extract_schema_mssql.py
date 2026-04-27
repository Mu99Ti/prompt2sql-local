import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.cache.file_schema_cache import FileSchemaCache
from app.db.introspection.mssql_schema_introspector import extract_mssql_schema


def build_connection_string(
    server: str,
    database: str,
    driver: str,
    username: str | None,
    password: str | None,
    trusted_connection: bool,
    encrypt: bool,
    trust_server_certificate: bool,
) -> str:
    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server}",
        f"DATABASE={database}",
        f"Encrypt={'yes' if encrypt else 'no'}",
        f"TrustServerCertificate={'yes' if trust_server_certificate else 'no'}",
    ]
    if trusted_connection:
        parts.append("Trusted_Connection=yes")
    else:
        if not username or not password:
            raise ValueError("username/password are required when trusted_connection is false")
        parts.append(f"UID={username}")
        parts.append(f"PWD={password}")
    return ";".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract SQL Server schema into JSON")
    parser.add_argument("--server", required=True, help="SQL Server host or host,port")
    parser.add_argument("--database", required=True, help="Database name")
    parser.add_argument("--out", required=True, help="Output schema JSON path")
    parser.add_argument("--driver", default="ODBC Driver 18 for SQL Server", help="ODBC driver name")
    parser.add_argument("--username", help="SQL login username")
    parser.add_argument("--password", help="SQL login password")
    parser.add_argument("--trusted-connection", action="store_true", help="Use integrated auth")
    parser.add_argument("--encrypt", action="store_true", help="Enable encrypted connection")
    parser.add_argument("--trust-server-certificate", action="store_true", help="Trust self-signed TLS cert")
    parser.add_argument(
        "--schemas",
        help="Comma-separated schema list to include (example: dbo,sales). Default includes all schemas.",
    )
    args = parser.parse_args()

    include_schemas = [s.strip() for s in args.schemas.split(",")] if args.schemas else None
    conn_str = build_connection_string(
        server=args.server,
        database=args.database,
        driver=args.driver,
        username=args.username,
        password=args.password,
        trusted_connection=args.trusted_connection,
        encrypt=args.encrypt,
        trust_server_certificate=args.trust_server_certificate,
    )

    schema = extract_mssql_schema(connection_string=conn_str, include_schemas=include_schemas)
    FileSchemaCache(args.out).save(schema)
    print(f"Schema written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
