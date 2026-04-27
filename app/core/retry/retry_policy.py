class RetryPolicy:
    def __init__(self, max_attempts: int = 2) -> None:
        self.max_attempts = max_attempts

    def attempts(self):
        for i in range(1, self.max_attempts + 1):
            yield i
