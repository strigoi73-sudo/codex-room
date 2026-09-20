from __future__ import annotations


def effective_timeout_seconds(config: dict[str, int]) -> int:
    return config["connect_timeout_seconds"] + config["read_timeout_seconds"]


def maximum_attempts(config: dict[str, int]) -> int:
    return config["max_retries"] + 1
