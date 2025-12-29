from __future__ import annotations

from pathlib import Path

from code_migration.clients.registry import get_client_by_family
from code_migration.config import RunConfig
from code_migration.manifest import load_tasks, write_tasks_csv, MigrationTask
from code_migration.utils.paths import ensure_run_dir, raw_output_path, clean_output_path
from code_migration.pipeline.migrate import _strip_think_tag


def run_batch(*, tasks_path: str, config_path: str, out_dir: str) -> None:
    config = RunConfig.from_json(config_path)
    run_dir = ensure_run_dir(out_dir, config)

    tasks = load_tasks(tasks_path)
    # Persist the normalized manifest used for this run
    write_tasks_csv(run_dir / "tasks.csv", tasks)

    client = get_client_by_family(config.client_family)
    for task in tasks:
        raw = client.migrate(task=task, config=config)
        raw_output_path(run_dir, task.task_id).write_text(raw, encoding="utf-8")
        clean_output_path(run_dir, task.task_id).write_text(_strip_think_tag(raw), encoding="utf-8")


