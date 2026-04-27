import re


class SQLOutputParser:
    def parse(self, raw_text: str) -> str:
        text = raw_text.strip()

        # Remove markdown fences if model ignores constraints.
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", text)
            text = re.sub(r"\n```$", "", text)
            text = text.strip()

        # Keep only first non-empty line block if extra prose is present.
        if "\n\n" in text:
            text = text.split("\n\n", 1)[0].strip()

        return text
