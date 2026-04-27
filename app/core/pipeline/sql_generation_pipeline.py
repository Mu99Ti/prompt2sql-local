from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


class SQLGenerationPipeline:
    def __init__(
        self,
        schema: dict,
        llm_client,
        prompt_builder,
        output_parser,
        normalizer,
        validator,
        retry_policy,
        tracker,
        app_env: str,
        service_name: str,
    ) -> None:
        self.schema = schema
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder
        self.output_parser = output_parser
        self.normalizer = normalizer
        self.validator = validator
        self.retry_policy = retry_policy
        self.tracker = tracker
        self.app_env = app_env
        self.service_name = service_name

    def run(self, question: str) -> dict:
        run_id = str(uuid4())
        last_error = None

        for attempt in self.retry_policy.attempts():
            prompt = self.prompt_builder.build(question=question, schema=self.schema)
            if attempt > 1 and last_error:
                prompt = (
                    f"{prompt}\n\n"
                    f"Previous output failed validation: {last_error}\n"
                    "Regenerate a corrected SQL query.\n"
                )

            raw = self.llm_client.generate(prompt)
            parsed = self.output_parser.parse(raw)
            sql = self.normalizer.normalize(parsed)
            valid, reason = self.validator.validate(sql)

            event = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "service": self.service_name,
                "env": self.app_env,
                "run_id": run_id,
                "attempt": attempt,
                "question": question,
                "raw_output": raw,
                "parsed_output": parsed,
                "normalized_sql": sql,
                "valid": valid,
                "reason": reason,
            }
            self.tracker.log(event)

            if valid:
                return {"ok": True, "sql": sql, "attempts": attempt, "run_id": run_id}

            last_error = reason

        return {
            "ok": False,
            "error": last_error or "Failed to generate valid SQL",
            "attempts": self.retry_policy.max_attempts,
            "run_id": run_id,
        }
