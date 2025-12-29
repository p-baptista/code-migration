from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from code_migration.config import RunConfig


def ensure_run_dir(out_dir: str | Path, config: RunConfig) -> Path:
    run_dir = Path(out_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "migrations" / "raw").mkdir(parents=True, exist_ok=True)
    (run_dir / "migrations" / "clean").mkdir(parents=True, exist_ok=True)
    (run_dir / "parsed").mkdir(parents=True, exist_ok=True)
    (run_dir / "metrics").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)

    (run_dir / "config.json").write_text(
        json.dumps(asdict(config), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return run_dir


def raw_output_path(run_dir: Path, task_id: str) -> Path:
    return run_dir / "migrations" / "raw" / f"{task_id}.txt"


def clean_output_path(run_dir: Path, task_id: str) -> Path:
    return run_dir / "migrations" / "clean" / f"{task_id}.txt"


def parsed_output_path(run_dir: Path, task_id: str) -> Path:
    return run_dir / "parsed" / f"{task_id}.txt"


