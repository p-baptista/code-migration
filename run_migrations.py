#!/usr/bin/env python3
"""
Legacy wrapper for run_migrations.py - converts old batch interface to new code-migration CLI.

DEPRECATED: Use 'code-migration batch' or 'code-migration pipeline' instead.
See USAGE.md for migration guide.
"""

import argparse
import csv
import json
import sys
import tempfile
from pathlib import Path

try:
    from code_migration.pipeline.batch import run_batch
    from code_migration.manifest import MigrationTask, write_tasks_csv
    NEW_CLI_AVAILABLE = True
except ImportError:
    NEW_CLI_AVAILABLE = False


def _convert_legacy_csv_to_new_format(csv_path: str, output_csv: Path) -> None:
    """
    Convert legacy CSV format to new format.
    Legacy: legacy_lib, target_lib, repo_name, code_before, id, etc.
    New: task_id, language, source_lib, target_lib, repo_name, code_before, etc.
    """
    with open(csv_path, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        tasks = []
        for row in reader:
            # Map old column names to new ones
            task_id = row.get('id', f"task_{len(tasks) + 1}")
            source_lib = row.get('legacy_lib', row.get('rmv_lib', ''))
            target_lib = row.get('target_lib', row.get('add_lib', ''))
            repo_name = row.get('repo_name', row.get('repo', ''))
            code_before = row.get('code_before', row.get('before', ''))
            code_after = row.get('code_after', row.get('after', ''))
            migration_type = row.get('migration_type', row.get('type', ''))
            
            tasks.append(MigrationTask(
                task_id=str(task_id),
                language="python",  # Default for legacy
                source_lib=source_lib,
                target_lib=target_lib,
                repo_name=repo_name,
                code_before=code_before,
                code_after=code_after if code_after else None,
                migration_type=migration_type if migration_type else None,
            ))
    
    write_tasks_csv(output_csv, tasks)


def run_all_migrations(csv_path, llm_name, model, prompt_template):
    """
    Legacy function signature maintained for backward compatibility.
    
    Note: The 'model' parameter is ignored - use llm_name for the model version.
    """
    if not NEW_CLI_AVAILABLE:
        print("ERROR: New CLI not available. Please install the package: pip install -e .")
        return
    
    print(f"⚠️  DEPRECATED: This script is a compatibility wrapper.")
    print(f"   Consider using: code-migration batch --tasks {csv_path} --config <config.json> --out artifacts/<run_id>")
    print()
    
    # Create temporary config
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_json = tmp_path / "config.json"
        converted_csv = tmp_path / "tasks.csv"
        out_dir = Path("artifacts") / f"legacy_run_{prompt_template}"
        
        # Convert CSV format
        _convert_legacy_csv_to_new_format(csv_path, converted_csv)
        
        # Create config
        config_json.write_text(json.dumps({
            "client_family": "ollama",  # Legacy script hardcodes ollama
            "model_version": llm_name,
            "prompt_template": prompt_template,
            "language": "python",
        }, indent=2), encoding="utf-8")
        
        # Run new batch CLI
        run_batch(
            tasks_path=str(converted_csv),
            config_path=str(config_json),
            out_dir=str(out_dir),
        )
        
        print(f"\n✅ Batch migration complete. Results in: {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run multiple code migrations defined in a CSV file (LEGACY)"
    )

    parser.add_argument(
        "--csv_file", 
        help="Path to the CSV file containing migration parameters."
    )

    parser.add_argument(
        "--llm_name", 
        help="Name of the LLM to be run."
    )

    default_templates = ['zero_shot', 'one_shot', 'chain_of_thoughts']

    parser.add_argument(
        "--prompt_template", 
        nargs="+",
        default=default_templates,
        help="Prompt template to be used."
    )

    parser.add_argument(
        "--model", 
        help="Model to be used (ignored, use --llm_name instead)."
    )
    
    args = parser.parse_args()
    
    if not args.csv_file or not args.llm_name:
        parser.print_help()
        sys.exit(1)

    for template in args.prompt_template:
        print(f"\n{'='*60}")
        print(f"Running migrations with template: {template}")
        print(f"{'='*60}\n")
        run_all_migrations(args.csv_file, args.llm_name, args.model, template)
