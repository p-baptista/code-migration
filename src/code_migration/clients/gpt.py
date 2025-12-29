from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

from code_migration.clients.base import BaseClient
from code_migration.config import RunConfig
from code_migration.manifest import MigrationTask

load_dotenv()


class GPTClient(BaseClient):
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _generate_prompt(self, template: str, *, task: MigrationTask, config: RunConfig) -> list[dict]:
        formatted = template.format(
            PROMPT=config.prompt_template,
            LANGUAGE_NAME=task.language,
            OLD_LIB_NAME=task.source_lib,
            NEW_LIB_NAME=task.target_lib,
            CODE_BEFORE_MIGRATION=task.code_before,
        )
        system_match = self.find_pattern(formatted, "SYSTEM_CONFIG")
        user_match = self.find_pattern(formatted, "USER_CONFIG")

        system_config = self.generate_request_dict("system", system_match[0])
        user_config_1 = self.generate_request_dict("user", user_match[0])

        if config.prompt_template != "one_shot":
            return [system_config, user_config_1]

        assistant_match = self.find_pattern(formatted, "ASSISTANT_CONFIG")
        assistant_config = self.generate_request_dict("assistant", assistant_match[0])
        user_config_2 = self.generate_request_dict("user", user_match[1])
        return [system_config, user_config_1, assistant_config, user_config_2]

    def migrate(self, *, task: MigrationTask, config: RunConfig) -> str:
        template = self.load_template(config.prompt_template)
        prompt = self._generate_prompt(template, task=task, config=config)
        response = self.client.chat.completions.create(model=config.model_version, messages=prompt)
        return response.choices[0].message.content


