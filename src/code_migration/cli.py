import argparse

from code_migration.pipeline.run import run_pipeline
from code_migration.pipeline.batch import run_batch
from code_migration.pipeline.migrate import run_one
from code_migration.pipeline.parse import run_parse
from code_migration.pipeline.score import run_score


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="code-migration")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run a single migration task.")
    p_run.add_argument("--task", required=True, help="Path to task JSON or CSV row JSON.")
    p_run.add_argument("--config", required=True, help="Path to config JSON.")
    p_run.add_argument("--out", required=True, help="Output run directory: artifacts/<run_id>")

    p_batch = sub.add_parser("batch", help="Run many migration tasks from a manifest.")
    p_batch.add_argument("--tasks", required=True, help="Path to tasks CSV/JSONL.")
    p_batch.add_argument("--config", required=True, help="Path to config JSON.")
    p_batch.add_argument("--out", required=True, help="Output run directory: artifacts/<run_id>")

    p_parse = sub.add_parser("parse", help="Parse model outputs into code snippets.")
    p_parse.add_argument("--in", dest="input_dir", required=True, help="Input directory (clean outputs).")
    p_parse.add_argument("--out", required=True, help="Output directory for parsed snippets.")
    p_parse.add_argument(
        "--policy",
        choices=["first", "all_concat", "all_separate"],
        default="first",
        help="How to handle multiple code blocks.",
    )

    p_score = sub.add_parser("score", help="Compute CodeBLEU scores.")
    p_score.add_argument("--tasks", required=True, help="Path to tasks CSV/JSONL (must include ground truth).")
    p_score.add_argument("--pred", required=True, help="Directory containing parsed predictions (<task_id>.txt).")
    p_score.add_argument("--out", required=True, help="Output directory for metrics + reports.")

    p_pipe = sub.add_parser("pipeline", help="Run batch -> parse -> score end-to-end.")
    p_pipe.add_argument("--tasks", required=True, help="Path to tasks CSV/JSONL.")
    p_pipe.add_argument("--config", required=True, help="Path to config JSON.")
    p_pipe.add_argument("--out", required=True, help="Output run directory: artifacts/<run_id>")
    p_pipe.add_argument(
        "--parse-policy",
        choices=["first", "all_concat", "all_separate"],
        default="first",
        help="How to handle multiple code blocks during parse.",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "run":
        run_one(task_path=args.task, config_path=args.config, out_dir=args.out)
    elif args.cmd == "batch":
        run_batch(tasks_path=args.tasks, config_path=args.config, out_dir=args.out)
    elif args.cmd == "parse":
        run_parse(input_dir=args.input_dir, out_dir=args.out, policy=args.policy)
    elif args.cmd == "score":
        run_score(tasks_path=args.tasks, pred_dir=args.pred, out_dir=args.out)
    elif args.cmd == "pipeline":
        run_pipeline(
            tasks_path=args.tasks,
            config_path=args.config,
            out_dir=args.out,
            parse_policy=args.parse_policy,
        )
    else:
        raise SystemExit(f"Unknown command: {args.cmd}")


