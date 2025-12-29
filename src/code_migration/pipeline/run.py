from __future__ import annotations

from pathlib import Path

from code_migration.config import RunConfig
from code_migration.pipeline.batch import run_batch
from code_migration.pipeline.parse import run_parse
from code_migration.pipeline.score import run_score


def run_pipeline(*, tasks_path: str, config_path: str, out_dir: str, parse_policy: str = "first") -> None:
    run_batch(tasks_path=tasks_path, config_path=config_path, out_dir=out_dir)
    run_dir = Path(out_dir)
    run_parse(input_dir=str(run_dir / "migrations" / "clean"), out_dir=str(run_dir / "parsed"), policy=parse_policy)
    run_score(tasks_path=str(run_dir / "tasks.csv"), pred_dir=str(run_dir / "parsed"), out_dir=str(run_dir / "metrics"))


