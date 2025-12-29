#!/usr/bin/env python3
"""
Legacy wrapper for get_codebleu_metric.py - converts old interface to new code-migration CLI.

DEPRECATED: Use 'code-migration score' instead.
See USAGE.md for migration guide.

This script maintains backward compatibility by reading from the old hard-coded paths
at the top of the file and converting them to the new CLI format.
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from code_migration.pipeline.score import run_score
    from code_migration.manifest import load_tasks, write_tasks_csv
    NEW_CLI_AVAILABLE = True
except ImportError:
    NEW_CLI_AVAILABLE = False

# Legacy configuration (for backward compatibility)
# These can be overridden via command-line arguments
CSV_DIRECTORY = './input/python'
MODEL_NAME = "codeqwen:latest"
SNIPPETS_DIRECTORY = f'./parsed/python/ollama/{MODEL_NAME}'
CSV_FILES = ['Boto-Boto3.csv', 'Request-Urllib.csv']
GENERATION_FOLDERS = ['zero_shot/code-migration', 'one_shot/code-migration', 'chain_of_thoughts/code-migration']


def analyze_migrations():
    """
    Legacy function that reads from hard-coded paths and runs scoring.
    """
    if not NEW_CLI_AVAILABLE:
        print("ERROR: New CLI not available. Please install the package: pip install -e .")
        return
    
    print(f"⚠️  DEPRECATED: This script uses hard-coded paths.")
    print(f"   Consider using: code-migration score --tasks <tasks.csv> --pred <parsed_dir> --out <metrics_dir>")
    print()
    
    import tempfile
    from pathlib import Path as P
    
    # Collect all tasks from CSV files
    all_tasks = []
    for csv_file in CSV_FILES:
        csv_path = os.path.join(CSV_DIRECTORY, csv_file)
        if not os.path.exists(csv_path):
            print(f"Warning: CSV file not found: {csv_path}. Skipping.")
            continue
        
        tasks = load_tasks(csv_path)
        all_tasks.extend(tasks)
    
    if not all_tasks:
        print("No tasks found. Please check CSV_DIRECTORY and CSV_FILES configuration.")
        return
    
    # For each generation folder, run scoring
    for folder in GENERATION_FOLDERS:
        print(f"\n{'='*60}")
        print(f"Processing folder: {folder}")
        print(f"{'='*60}\n")
        
        pred_dir = os.path.join(SNIPPETS_DIRECTORY, folder)
        if not os.path.exists(pred_dir):
            print(f"Warning: Prediction directory not found: {pred_dir}. Skipping.")
            continue
        
        # Create temporary tasks CSV with ground truth
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = P(tmpdir)
            tasks_csv = tmp_path / "tasks.csv"
            
            # Write tasks with ground truth
            write_tasks_csv(tasks_csv, all_tasks)
            
            # Create output directory
            output_dir = P("artifacts") / "legacy_metrics" / folder.replace("/", "_")
            
            # Run new score CLI
            run_score(
                tasks_path=str(tasks_csv),
                pred_dir=pred_dir,
                out_dir=str(output_dir),
            )
            
            print(f"\n✅ Metrics saved to: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute CodeBLEU scores (LEGACY - use 'code-migration score' instead)"
    )
    parser.add_argument(
        "--csv-dir",
        default=CSV_DIRECTORY,
        help=f"Directory containing CSV files (default: {CSV_DIRECTORY})"
    )
    parser.add_argument(
        "--model-name",
        default=MODEL_NAME,
        help=f"Model name for snippets directory (default: {MODEL_NAME})"
    )
    parser.add_argument(
        "--snippets-dir",
        help=f"Directory containing parsed snippets (default: ./parsed/python/ollama/<model_name>)"
    )
    
    args = parser.parse_args()
    
    # Update globals if provided
    if args.csv_dir:
        CSV_DIRECTORY = args.csv_dir
    if args.model_name:
        MODEL_NAME = args.model_name
        if not args.snippets_dir:
            SNIPPETS_DIRECTORY = f'./parsed/python/ollama/{MODEL_NAME}'
    if args.snippets_dir:
        SNIPPETS_DIRECTORY = args.snippets_dir
    
    if not NEW_CLI_AVAILABLE:
        print("ERROR: New CLI not available. Please install the package: pip install -e .")
        sys.exit(1)
    
    analyze_migrations()
