import json
from pathlib import Path


class RunTracker:
    def __init__(self, log_path: str, log_to_stdout: bool = True, log_to_file: bool = False) -> None:
        self.path = Path(log_path)
        self.log_to_stdout = log_to_stdout
        self.log_to_file = log_to_file
        if self.log_to_file:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: dict) -> None:
        encoded = json.dumps(event, ensure_ascii=True)
        if self.log_to_stdout:
            print(encoded, flush=True)
        if self.log_to_file:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(encoded + "\n")
