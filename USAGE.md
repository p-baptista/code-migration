# Code Migration Pipeline - Usage Guide

## Quick Start

Run the full pipeline end-to-end:

```bash
code-migration pipeline \
  --tasks input/python/treated_python_commits.csv \
  --config configs/ollama_codeqwen.json \
  --out artifacts/run_20250101_001
```

## Configuration Files

### Example Config: `configs/ollama_codeqwen.json`

```json
{
  "client_family": "ollama",
  "model_version": "codeqwen:latest",
  "prompt_template": "zero_shot",
  "language": "python"
}
```

### Example Config: `configs/gpt_4o_mini.json`

```json
{
  "client_family": "gpt",
  "model_version": "gpt-4o-mini",
  "prompt_template": "one_shot",
  "language": "python"
}
```

### Available Prompt Templates

- `zero_shot` - Direct migration request
- `one_shot` - Includes an example migration
- `chain_of_thoughts` - Step-by-step reasoning approach

## Task Manifest Format

### CSV Format (Recommended)

The tasks CSV should have the following columns:

```csv
task_id,language,legacy_lib,target_lib,repo_name,migration_type,code_before,code_after
task_001,python,boto,boto3,my-repo,library_migration,"import boto
conn = boto.connect_s3()","import boto3
s3 = boto3.client('s3')"
task_002,python,requests,urllib,another-repo,library_migration,"import requests
r = requests.get('https://api.example.com')","from urllib import request
r = request.urlopen('https://api.example.com')"
```

**Required columns:**
- `task_id` - Unique identifier for the task
- `legacy_lib` - Legacy library name
- `target_lib` - Target library name
- `code_before` - Source code to migrate

**Optional columns:**
- `language` - Programming language (default: "python")
- `repo_name` - Repository name (for organization)
- `migration_type` - Type of migration (for grouping in reports)
- `code_after` - Ground truth (required only for scoring)

### JSONL Format (Alternative)

```jsonl
{"task_id": "task_001", "language": "python", "legacy_lib": "boto", "target_lib": "boto3", "repo_name": "my-repo", "code_before": "import boto\nconn = boto.connect_s3()"}
{"task_id": "task_002", "language": "python", "legacy_lib": "requests", "target_lib": "urllib", "repo_name": "another-repo", "code_before": "import requests\nr = requests.get('https://api.example.com')"}
```

## Command Reference

### 1. Run Single Task

Migrate a single code snippet:

```bash
code-migration run \
  --task task.json \
  --config configs/ollama_codeqwen.json \
  --out artifacts/single_task_run
```

**Task JSON format** (`task.json`):
```json
{
  "task_id": "task_001",
  "language": "python",
  "legacy_lib": "boto",
  "target_lib": "boto3",
  "repo_name": "my-repo",
  "code_before": "import boto\nconn = boto.connect_s3()"
}
```

### 2. Batch Migration

Run migrations for multiple tasks:

```bash
code-migration batch \
  --tasks input/python/treated_python_commits.csv \
  --config configs/ollama_codeqwen.json \
  --out artifacts/batch_run_001
```

**Output structure:**
```
artifacts/batch_run_001/
├── config.json                    # Configuration snapshot
├── tasks.csv                      # Normalized task manifest
└── migrations/
    ├── raw/
    │   ├── task_001.txt          # Raw LLM output
    │   └── task_002.txt
    └── clean/
        ├── task_001.txt          # Think tags removed
        └── task_002.txt
```

### 3. Parse Code Blocks

Extract code snippets from model outputs:

```bash
code-migration parse \
  --in artifacts/batch_run_001/migrations/clean \
  --out artifacts/batch_run_001/parsed \
  --policy first
```

**Parse policies:**
- `first` - Use first code block only (default)
- `all_concat` - Concatenate all blocks with `\n\n`
- `all_separate` - Save each block as separate files (`<task_id>__block1.txt`, etc.)

**Example:**
```bash
# Extract only first code block
code-migration parse \
  --in artifacts/batch_run_001/migrations/clean \
  --out artifacts/batch_run_001/parsed \
  --policy first

# Extract all blocks, concatenated
code-migration parse \
  --in artifacts/batch_run_001/migrations/clean \
  --out artifacts/batch_run_001/parsed \
  --policy all_concat
```

### 4. Score Predictions

Compute CodeBLEU metrics (requires ground truth in tasks CSV):

```bash
code-migration score \
  --tasks artifacts/batch_run_001/tasks.csv \
  --pred artifacts/batch_run_001/parsed \
  --out artifacts/batch_run_001/metrics
```

**Output files:**
```
artifacts/batch_run_001/metrics/
├── codebleu.csv          # Per-task scores
├── summary.json          # Aggregated statistics (JSON)
├── summary.txt           # Human-readable report
└── analysis.log          # Detailed execution log
```

**Example `codebleu.csv`:**
```csv
task_id,migration_type,score
task_001,library_migration,0.8234
task_002,library_migration,0.7567
```

**Example `summary.txt`:**
```
========================= ANALYSIS SUMMARY =========================

Results for: library_migration
  - Average CodeBLEU: 0.7901
  - Snippets Compared: 2/2
```

### 5. Full Pipeline

Run all stages sequentially (batch → parse → score):

```bash
code-migration pipeline \
  --tasks input/python/treated_python_commits.csv \
  --config configs/ollama_codeqwen.json \
  --out artifacts/full_pipeline_run \
  --parse-policy first
```

This is equivalent to:
```bash
code-migration batch --tasks ... --config ... --out artifacts/full_pipeline_run
code-migration parse --in artifacts/full_pipeline_run/migrations/clean --out artifacts/full_pipeline_run/parsed --policy first
code-migration score --tasks artifacts/full_pipeline_run/tasks.csv --pred artifacts/full_pipeline_run/parsed --out artifacts/full_pipeline_run/metrics
```

## Complete Workflow Examples

### Example 1: Compare Multiple Prompt Templates

```bash
# Run with zero_shot
code-migration pipeline \
  --tasks input/python/treated_python_commits.csv \
  --config configs/ollama_zero_shot.json \
  --out artifacts/comparison/zero_shot

# Run with one_shot
code-migration pipeline \
  --tasks input/python/treated_python_commits.csv \
  --config configs/ollama_one_shot.json \
  --out artifacts/comparison/one_shot

# Run with chain_of_thoughts
code-migration pipeline \
  --tasks input/python/treated_python_commits.csv \
  --config configs/ollama_cot.json \
  --out artifacts/comparison/chain_of_thoughts
```

### Example 2: Compare Different Models

```bash
# GPT-4o-mini
code-migration pipeline \
  --tasks input/python/treated_python_commits.csv \
  --config configs/gpt_4o_mini.json \
  --out artifacts/models/gpt_4o_mini

# Ollama CodeQwen
code-migration pipeline \
  --tasks input/python/treated_python_commits.csv \
  --config configs/ollama_codeqwen.json \
  --out artifacts/models/codeqwen
```

### Example 3: Incremental Workflow

Run stages separately for debugging or resuming:

```bash
# Step 1: Run migrations (takes time)
code-migration batch \
  --tasks input/python/treated_python_commits.csv \
  --config configs/ollama_codeqwen.json \
  --out artifacts/incremental_run

# Step 2: Parse outputs (quick)
code-migration parse \
  --in artifacts/incremental_run/migrations/clean \
  --out artifacts/incremental_run/parsed \
  --policy first

# Step 3: Score (requires ground truth)
code-migration score \
  --tasks artifacts/incremental_run/tasks.csv \
  --pred artifacts/incremental_run/parsed \
  --out artifacts/incremental_run/metrics
```

## Converting Legacy CSV Format

If your CSV uses different column names, you can convert it:

**Legacy format:**
```csv
repo,commit,rmv_lib,add_lib,before,after,type
my-repo,abc123,boto,boto3,"import boto","import boto3",library_migration
```

**Convert to new format:**
```python
import pandas as pd

df = pd.read_csv('legacy.csv')
df_new = pd.DataFrame({
    'task_id': df['repo'] + '_' + df['commit'],
    'language': 'python',
    'legacy_lib': df['rmv_lib'],
    'target_lib': df['add_lib'],
    'repo_name': df['repo'],
    'migration_type': df['type'],
    'code_before': df['before'],
    'code_after': df['after']
})
df_new.to_csv('tasks.csv', index=False)
```

## Artifacts Directory Structure

Each run creates a self-contained directory:

```
artifacts/<run_id>/
├── config.json                    # Run configuration
├── tasks.csv                      # Task manifest
├── migrations/
│   ├── raw/                       # Raw LLM outputs
│   │   └── <task_id>.txt
│   └── clean/                     # Cleaned outputs (think tags removed)
│       └── <task_id>.txt
├── parsed/                        # Extracted code snippets
│   └── <task_id>.txt
├── metrics/                       # CodeBLEU scores
│   ├── codebleu.csv
│   ├── summary.json
│   ├── summary.txt
│   └── analysis.log
└── reports/                       # (Reserved for future use)
```

## Troubleshooting

### Missing Ground Truth

If scoring fails with "missing code_after", ensure your tasks CSV includes the `code_after` column:

```csv
task_id,legacy_lib,target_lib,code_before,code_after
task_001,boto,boto3,"import boto","import boto3"
```

### Model Not Found (Ollama)

Ensure Ollama is running and the model is pulled:

```bash
ollama serve  # In one terminal
ollama pull codeqwen:latest  # In another terminal
```

### API Key Missing (GPT)

Set your OpenAI API key:

```bash
export OPENAI_API_KEY=sk-...
# Or create a .env file with: OPENAI_API_KEY=sk-...
```

### Parse Policy Issues

If code blocks aren't extracted correctly, try different policies:

```bash
# Try extracting all blocks separately to inspect
code-migration parse \
  --in artifacts/run/migrations/clean \
  --out artifacts/run/parsed \
  --policy all_separate
```

## Environment Variables

- `OPENAI_API_KEY` - Required for GPT client
- `OLLAMA_HOST` - Optional, defaults to `http://localhost:11434`

