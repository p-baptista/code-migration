from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class MigrationTask:
    task_id: str
    language: str
    legacy_lib: str
    target_lib: str
    repo_name: str
    code_before: str
    code_after: str | None = None
    migration_type: str | None = None


def load_tasks(path: str | Path) -> list[MigrationTask]:
    p = Path(path)
    if p.suffix.lower() == ".jsonl":
        tasks: list[MigrationTask] = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            tasks.append(MigrationTask(**data))
        return tasks

    # Default: CSV
    with p.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        out: list[MigrationTask] = []
        for row in reader:
            out.append(
                MigrationTask(
                    task_id=row["task_id"],
                    language=row.get("language", "python"),
                    legacy_lib=row["legacy_lib"],
                    target_lib=row["target_lib"],
                    repo_name=row.get("repo_name", ""),
                    code_before=row["code_before"],
                    code_after=row.get("code_after") or None,
                    migration_type=row.get("migration_type") or row.get("type") or None,
                )
            )
        return out


def write_tasks_csv(path: str | Path, tasks: Iterable[MigrationTask]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "task_id",
        "language",
        "legacy_lib",
        "target_lib",
        "repo_name",
        "migration_type",
        "code_before",
        "code_after",
    ]
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in tasks:
            d = asdict(t)
            d["migration_type"] = d.pop("migration_type")
            writer.writerow({k: d.get(k) for k in fieldnames})


