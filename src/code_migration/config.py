from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunConfig:
    client_family: str  # "gpt" | "ollama"
    model_version: str  # e.g. "gpt-4o-mini" or "codeqwen:latest"
    prompt_template: str  # "zero_shot" | "one_shot" | "chain_of_thoughts"
    language: str = "python"

    @staticmethod
    def from_json(path: str | Path) -> "RunConfig":
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))
        return RunConfig(
            client_family=data["client_family"],
            model_version=data["model_version"],
            prompt_template=data["prompt_template"],
            language=data.get("language", "python"),
        )


