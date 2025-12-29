from __future__ import annotations

import re
from abc import ABC, abstractmethod
from importlib import resources

from code_migration.config import RunConfig
from code_migration.manifest import MigrationTask


class BaseClient(ABC):
    def load_template(self, template_name: str) -> str:
        # templates are packaged as code_migration/templates/<name>.txt
        with resources.files("code_migration").joinpath("templates", f"{template_name}.txt").open(
            "r", encoding="utf-8"
        ) as f:
            return f.read()

    def find_pattern(self, formatted: str, flag: str) -> list[str]:
        pattern = rf"{{{flag}}}(.*?)[\r\n]*{{{flag}_END}}"
        return re.findall(pattern, formatted, re.DOTALL)

    def generate_request_dict(self, role: str, content: str) -> dict:
        return {"role": role, "content": content}

    @abstractmethod
    def migrate(self, *, task: MigrationTask, config: RunConfig) -> str:
        raise NotImplementedError


