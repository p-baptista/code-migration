#!/usr/bin/env python3
"""
Legacy wrapper for main.py - converts old CLI interface to new code-migration CLI.

DEPRECATED: Use 'code-migration run' instead.
See USAGE.md for migration guide.
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

# Try to import new CLI, fallback to old implementation if not available
try:
    from code_migration.pipeline.migrate import run_one
    from code_migration.config import RunConfig
    from code_migration.manifest import MigrationTask
    NEW_CLI_AVAILABLE = True
except ImportError:
    NEW_CLI_AVAILABLE = False


def _extract_repo_name_from_path(input_path: str) -> str:
    """Extract repo name from old path structure: input/lang/lib/repo/file"""
    path_obj = Path(input_path)
    parts = path_obj.parts
    # Old structure: input/lang/lib/repo/file or input/lang/prompt/lib/repo/file
    if len(parts) >= 4:
        # Try to find repo name (usually 3rd or 4th part)
        for i, part in enumerate(parts):
            if part in ["input", "python", "boto", "requests", "urllib"]:
                continue
            if i > 2:  # Skip input/lang/lib
                return part
    return "unknown_repo"


def _create_task_from_args(args) -> MigrationTask:
    """Create MigrationTask from old-style arguments."""
    input_path = Path(args.INPUT_PATH)
    code_before = input_path.read_text(encoding="utf-8")
    
    # Extract task_id from filename (remove extension)
    task_id = input_path.stem
    
    # Extract repo_name from path
    repo_name = _extract_repo_name_from_path(args.INPUT_PATH)
    
    return MigrationTask(
        task_id=task_id,
        language=args.LANGUAGE_NAME,
        legacy_lib=args.OLD_LIB_NAME,
        target_lib=args.NEW_LIB_NAME,
        repo_name=repo_name,
        code_before=code_before,
        code_after=None,
        migration_type=None,
    )


def _create_config_from_args(args) -> RunConfig:
    """Create RunConfig from old-style arguments."""
    return RunConfig(
        client_family=args.MODEL,
        model_version=args.VERSION,
        prompt_template=args.PROMPT,
        language=args.LANGUAGE_NAME,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Run code migration (LEGACY - use 'code-migration run' instead)"
    )
    parser.add_argument("LANGUAGE_NAME", help="Programming language (e.g., python)")
    parser.add_argument("OLD_LIB_NAME", help="Original library name (e.g., boto)")
    parser.add_argument("NEW_LIB_NAME", help="New library name (e.g., boto3)")
    parser.add_argument("MODEL", help="Model family (e.g., gpt)")
    parser.add_argument("VERSION", help="Model version (e.g., gpt-4)")
    parser.add_argument("PROMPT", help="Prompt template (e.g., one_shot)")
    parser.add_argument("INPUT_PATH", help="Input file path (e.g., input/python/boto/ex.txt)")

    args = parser.parse_args()

    if not NEW_CLI_AVAILABLE:
        print("ERROR: New CLI not available. Please install the package: pip install -e .")
        sys.exit(1)

    try:
        # Convert old args to new format
        task = _create_task_from_args(args)
        config = _create_config_from_args(args)
        
        # Create temporary files for new CLI
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            task_json = tmp_path / "task.json"
            config_json = tmp_path / "config.json"
            out_dir = tmp_path / "output"
            
            # Write task and config
            task_json.write_text(json.dumps({
                "task_id": task.task_id,
                "language": task.language,
                "legacy_lib": task.legacy_lib,
                "target_lib": task.target_lib,
                "repo_name": task.repo_name,
                "code_before": task.code_before,
            }, indent=2), encoding="utf-8")
            
            config_json.write_text(json.dumps({
                "client_family": config.client_family,
                "model_version": config.model_version,
                "prompt_template": config.prompt_template,
                "language": config.language,
            }, indent=2), encoding="utf-8")
            
            # Run new CLI
            run_one(
                task_path=str(task_json),
                config_path=str(config_json),
                out_dir=str(out_dir),
            )
            
            # Read output and save to old location for compatibility
            clean_output = Path(out_dir) / "migrations" / "clean" / f"{task.task_id}.txt"
            if clean_output.exists():
                # Try to save to old output location
                output_dir = Path("output") / args.LANGUAGE_NAME / args.MODEL / args.VERSION / args.PROMPT / task.repo_name
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / f"{task.task_id}.txt"
                output_file.write_text(clean_output.read_text(encoding="utf-8"), encoding="utf-8")
                print("\nMigração concluída com sucesso!")
                print(f"Resultado salvo em: {output_file}")
            else:
                print(f"\nMigração concluída. Resultado em: {out_dir}")
                
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
