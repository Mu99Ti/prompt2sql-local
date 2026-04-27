from app.config.settings import Settings
from app.main.runner.service_runner import ServiceRunner


def main() -> int:
    settings = Settings.from_env()
    runner = ServiceRunner(settings)
    result = runner.generate_sql("List the top 5 customers by number of orders")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
