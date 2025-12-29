from __future__ import annotations

import json
from pathlib import Path

from code_migration.clients.registry import get_client_by_family
from code_migration.config import RunConfig
from code_migration.manifest import MigrationTask
from code_migration.utils.paths import ensure_run_dir, raw_output_path, clean_output_path


def _strip_think_tag(text: str) -> str:
    if "<think>" in text and "</think>" in text:
        return text.split("</think>", 1)[-1].lstrip()
    return text


def run_one(*, task_path: str, config_path: str, out_dir: str) -> None:
    config = RunConfig.from_json(config_path)
    run_dir = ensure_run_dir(out_dir, config)

    task_data = json.loads(Path(task_path).read_text(encoding="utf-8"))
    task = MigrationTask(**task_data)

    client = get_client_by_family(config.client_family)
    raw = client.migrate(task=task, config=config)
    raw_path = raw_output_path(run_dir, task.task_id)
    raw_path.write_text(raw, encoding="utf-8")

    clean = _strip_think_tag(raw)
    clean_path = clean_output_path(run_dir, task.task_id)
    clean_path.write_text(clean, encoding="utf-8")


