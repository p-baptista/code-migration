from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd
from codebleu import calc_codebleu

from code_migration.manifest import load_tasks


def run_score(*, tasks_path: str, pred_dir: str, out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("code_migration.score")
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    fh = logging.FileHandler(out / "analysis.log", mode="w", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(sh)

    tasks = load_tasks(tasks_path)
    results: list[dict] = []

    pred_root = Path(pred_dir)
    for task in tasks:
        if not task.code_after:
            raise ValueError(f"Task {task.task_id} missing code_after; required for scoring.")

        pred_path = pred_root / f"{task.task_id}.txt"
        if not pred_path.exists():
            logger.warning(f"[task_id={task.task_id}] prediction not found: {pred_path}")
            results.append(
                {
                    "task_id": task.task_id,
                    "migration_type": task.migration_type,
                    "score": None,
                }
            )
            continue

        prediction = pred_path.read_text(encoding="utf-8")
        result = calc_codebleu(predictions=[prediction], references=[[task.code_after]], lang=task.language)
        score = result["codebleu"]
        logger.info(f"[task_id={task.task_id}] CodeBLEU: {score:.4f}")
        results.append(
            {
                "task_id": task.task_id,
                "migration_type": task.migration_type,
                "score": score,
            }
        )

    df = pd.DataFrame(results)
    df.to_csv(out / "codebleu.csv", index=False)

    summary = (
        df.groupby("migration_type", dropna=False)["score"]
        .agg(["mean", "count", "size"])
        .reset_index()
        .rename(
            columns={
                "mean": "avg_codebleu",
                "count": "samples_found",
                "size": "total_samples",
            }
        )
    )
    (out / "summary.json").write_text(summary.to_json(orient="records", indent=2), encoding="utf-8")

    report_lines = ["=" * 25 + " ANALYSIS SUMMARY " + "=" * 25]
    for _, row in summary.iterrows():
        report_lines.append(f"\nResults for: {row['migration_type']}")
        report_lines.append(f"  - Average CodeBLEU: {row['avg_codebleu'] if pd.notna(row['avg_codebleu']) else 'NA'}")
        report_lines.append(f"  - Snippets Compared: {int(row['samples_found'])}/{int(row['total_samples'])}")
    (out / "summary.txt").write_text("\n".join(report_lines), encoding="utf-8")


