#!/usr/bin/env python3
"""
Legacy wrapper for parser.py - converts old interface to new code-migration CLI.

DEPRECATED: Use 'code-migration parse' instead.
See USAGE.md for migration guide.
"""

import argparse
import sys

try:
    from code_migration.pipeline.parse import run_parse
    NEW_CLI_AVAILABLE = True
except ImportError:
    NEW_CLI_AVAILABLE = False


def process_directory(input_dir: str, output_dir: str = "output"):
    """
    Legacy function signature maintained for backward compatibility.
    """
    if not NEW_CLI_AVAILABLE:
        print("ERROR: New CLI not available. Please install the package: pip install -e .")
        return
    
    print(f"⚠️  DEPRECATED: This script is a compatibility wrapper.")
    print(f"   Consider using: code-migration parse --in {input_dir} --out {output_dir} --policy first")
    print()
    
    # Run new parse CLI with default policy
    run_parse(
        input_dir=input_dir,
        out_dir=output_dir,
        policy="first",  # Default policy for legacy compatibility
    )
    
    print(f"✅ Extraction complete! Files saved in '{output_dir}/'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract code blocks from .txt files (LEGACY - use 'code-migration parse' instead)"
    )
    parser.add_argument("input_dir", help="Directory containing .txt files")
    parser.add_argument("--output", default="output", help="Output directory (default: output)")

    args = parser.parse_args()
    
    if not NEW_CLI_AVAILABLE:
        print("ERROR: New CLI not available. Please install the package: pip install -e .")
        sys.exit(1)
    
    process_directory(args.input_dir, args.output)
