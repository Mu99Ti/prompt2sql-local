import argparse
import json
import sys

from app.config.settings import Settings
from app.main.runner.service_runner import ServiceRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Text-to-SQL generator (SQL only)")
    parser.add_argument("--question", type=str, help="Natural language question")
    parser.add_argument(
        "--output",
        choices=["sql", "json"],
        default="sql",
        help="Output format. 'sql' prints SQL only, 'json' prints full metadata.",
    )
    parser.add_argument(
        "--single-line",
        action="store_true",
        help="When used with --output sql, collapse SQL whitespace into one line.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    question = args.question
    if not question:
        question = input("Question: ").strip()

    if not question:
        print("Question is required.", file=sys.stderr)
        return 1

    settings = Settings.from_env()
    runner = ServiceRunner(settings)
    result = runner.generate_sql(question)

    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        if result.get("ok"):
            sql = result.get("sql", "")
            if args.single_line:
                sql = " ".join(sql.split())
            print(sql)
        else:
            print(result.get("error", "Failed to generate SQL"), file=sys.stderr)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
