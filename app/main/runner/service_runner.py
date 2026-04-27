from app.config.settings import Settings
from app.core.pipeline.sql_generation_pipeline import SQLGenerationPipeline
from app.db.schema.schema_loader import SchemaLoader
from app.llm.client.ollama_client import OllamaClient
from app.llm.output_parser.sql_output_parser import SQLOutputParser
from app.llm.prompts.prompt_builder import PromptBuilder
from app.core.normalizer.sql_normalizer import SQLNormalizer
from app.core.validator.sql_validator import SQLValidator
from app.core.retry.retry_policy import RetryPolicy
from app.logging.trackers.run_tracker import RunTracker


class ServiceRunner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        schema_loader = SchemaLoader(settings.schema_path, sql_dialect=settings.sql_dialect)
        schema = schema_loader.load()

        client = OllamaClient(
            base_url=settings.ollama_url,
            model=settings.model,
            temperature=settings.temperature,
            request_timeout_sec=settings.request_timeout_sec,
        )
        prompt_builder = PromptBuilder(prompt_version=settings.prompt_version, sql_dialect=settings.sql_dialect)
        parser = SQLOutputParser()
        normalizer = SQLNormalizer()
        validator = SQLValidator(schema=schema, sql_dialect=settings.sql_dialect)
        retry = RetryPolicy(max_attempts=settings.max_attempts)
        tracker = RunTracker(
            log_path=settings.log_path,
            log_to_stdout=settings.log_to_stdout,
            log_to_file=settings.log_to_file,
        )

        self.pipeline = SQLGenerationPipeline(
            schema=schema,
            llm_client=client,
            prompt_builder=prompt_builder,
            output_parser=parser,
            normalizer=normalizer,
            validator=validator,
            retry_policy=retry,
            tracker=tracker,
            app_env=settings.app_env,
            service_name=settings.service_name,
        )

    def generate_sql(self, question: str) -> dict:
        return self.pipeline.run(question)
