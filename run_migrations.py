import argparse
import csv
import subprocess
import sys
import tempfile
from pathlib import Path
import os

def run_all_migrations(csv_path, llm_name, prompt_template):
    """
    Reads a CSV file, creates a temporary file for the source code,
    and runs the main.py script for each row.
    """
    script_dir = Path(__file__).resolve().parent
    main_py_path = script_dir / "main.py"
    if not main_py_path.is_file():
        print(f"Error: 'main.py' could not be found at the expected location: {main_py_path}")
        return

    base_temp_dir = script_dir / "temp_output"
    base_temp_dir.mkdir(exist_ok=True)

    try:
        with open(csv_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            migration_tasks = list(reader)
            if not migration_tasks:
                print("CSV file is empty. No migrations to run.")
                return

            total_tasks = len(migration_tasks)
            print(f"Found {total_tasks} migration tasks in '{csv_path}'. Starting process...\n")

            for i, row in enumerate(migration_tasks, 1):
                with tempfile.TemporaryDirectory(dir=base_temp_dir) as temp_dir:
                    try:
                        temp_dir_path = Path(temp_dir)
                        language = "python"
                        old_lib = row['legacy_lib']
                        repo_name = row['repo_name']
                        filename = f"python_{row['legacy_lib']}_{row['target_lib']}" + row['id']
                        source_code = row['code_before']
                        
                        temp_source_file = temp_dir_path / 'input' / language / prompt_template / old_lib / repo_name / filename

                        parent_dir = temp_source_file.parent

                        parent_dir.mkdir(parents=True, exist_ok=True)
                                                
                        temp_source_file.write_text(source_code, encoding='utf-8')

                        print(f"--- [ {i}/{total_tasks} ] Running migration for: {repo_name}/{filename} ---")
                        
                        command = [
                            sys.executable,
                            str(main_py_path),
                            language,
                            old_lib,
                            row['target_lib'],
                            "ollama",
                            llm_name,
                            prompt_template,
                            str(temp_source_file)
                        ]

                        result = subprocess.run(
                            command, 
                            check=True, 
                            capture_output=True, 
                            text=True, 
                            encoding='utf-8'
                        )

                        print(result.stdout.strip())
                        if result.stderr:
                            print("STDERR:", result.stderr.strip())

                    except KeyError as e:
                        print(f"Error: CSV file is missing required column: {e}. Skipping this row.")
                    except subprocess.CalledProcessError as e:
                        print(f"An error occurred while executing main.py for row {i}.")
                        print(f"   Return Code: {e.returncode}")
                        print(f"   Output:\n{e.stdout.strip()}")
                        print(f"   Error Output:\n{e.stderr.strip()}")
                    
                    print(f"Migration complete. Temporary files cleaned up. 🧹")
                    print("-" * 60 + "\n")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run multiple code migrations defined in a CSV file."
    )
    parser.add_argument(
        "csv_file", 
        help="Path to the CSV file containing migration parameters."
    )
    parser.add_argument(
        "llm_name", 
        help="Name of the LLM to be run."
    )
    args = parser.parse_args()

    templates = ['zero_shot', 'one_shot', 'chain_of_thoughts']

    for template in templates:
        run_all_migrations(args.csv_file, args.llm_name, template)