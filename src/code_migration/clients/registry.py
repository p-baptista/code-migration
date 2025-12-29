from __future__ import annotations

from code_migration.clients.base import BaseClient
from code_migration.clients.gpt import GPTClient
from code_migration.clients.ollama import OllamaClient


def get_client_by_family(family: str) -> BaseClient:
    if family == "gpt":
        return GPTClient()
    if family == "ollama":
        return OllamaClient()
    raise ValueError(f"Unsupported client family: {family}")


