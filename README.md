# code-migration

Studying the ability of public LLMs to migrate code between two equivalent libraries.

## Quick Start

### 1. Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### 2. Setup

**For GPT models:** Set your OpenAI API key:
```bash
export OPENAI_API_KEY=sk-...
# Or create a .env file
```

**For Ollama models:** Ensure Ollama is running:
```bash
ollama serve  # In one terminal
ollama pull codeqwen:latest  # Pull your model
```

### 3. Run Pipeline

```bash
# Full pipeline (recommended)
code-migration pipeline \
  --tasks input/python/treated_python_commits.csv \
  --config configs/ollama_codeqwen.json \
  --out artifacts/run_001
```

## Documentation

For detailed usage instructions, command reference, and examples, see **[USAGE.md](USAGE.md)**.

## Pipeline Overview

The refactored pipeline consists of four stages:

1. **Batch Migration** (`batch`) - Run LLM migrations for multiple tasks
2. **Parsing** (`parse`) - Extract code blocks from model outputs
3. **Scoring** (`score`) - Compute CodeBLEU metrics against ground truth
4. **Full Pipeline** (`pipeline`) - Run all stages sequentially

Each run creates a self-contained directory under `artifacts/<run_id>/` with:
- Configuration snapshot (`config.json`)
- Task manifest (`tasks.csv`)
- Raw and cleaned model outputs (`migrations/`)
- Parsed code snippets (`parsed/`)
- Metrics and reports (`metrics/`)

## Legacy Scripts

The following scripts are still available as thin wrappers around the new CLI:

- `main.py` → `code-migration run`
- `run_migrations.py` → `code-migration batch`
- `parser.py` → `code-migration parse`
- `get_codebleu_metric.py` → `code-migration score`

See [USAGE.md](USAGE.md) for migration guide and examples.