"""Compare two text columns in a CSV row-wise and add a JSON result column.

Algorithm:
 - Split each text into lines
 - Use a Needleman-Wunsch style DP where the match score for two lines is
   the fuzzy similarity (difflib.SequenceMatcher.ratio)
 - Gap penalty is configurable
 - Output: a JSON object per row with overall_score and aligned pairs

Usage (CLI):
 python compare_dataset.py --input data.csv --col_a col1 --col_b col2 --out out.csv

The new column will be called `comparison_result` by default and contains
JSON with keys: overall_score (float), pairs (list of [a_line|null, b_line|null, similarity]).
"""

from __future__ import annotations

import argparse
import csv
import json
from difflib import SequenceMatcher
from typing import Callable, List, Optional, Tuple

try:
    import pandas as pd
except Exception:
    pd = None

Pair = Tuple[Optional[str], Optional[str], float]


def line_similarity(a: str, b: str) -> float:
    if a is None or b is None:
        return 0.0
    return float(SequenceMatcher(None, a, b).ratio())


def needleman_wunsch_lines(
    a_lines: List[str],
    b_lines: List[str],
    match_score_fn: Callable[[str, str], float],
    gap_penalty: float = 0.3,
) -> List[Pair]:
    # Scores matrix
    n, m = len(a_lines), len(b_lines)
    # initialize dp
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]

    # gap penalty is negative when applied
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] - gap_penalty
        back[i][0] = "up"
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] - gap_penalty
        back[0][j] = "left"

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sim = match_score_fn(a_lines[i - 1], b_lines[j - 1])
            diag = dp[i - 1][j - 1] + sim
            up = dp[i - 1][j] - gap_penalty
            left = dp[i][j - 1] - gap_penalty
            best = max(diag, up, left)
            dp[i][j] = best
            if best == diag:
                back[i][j] = "diag"
            elif best == up:
                back[i][j] = "up"
            else:
                back[i][j] = "left"

    # backtrack
    i, j = n, m
    pairs: List[Pair] = []
    while i > 0 or j > 0:
        direction = back[i][j]
        if direction == "diag":
            a_line = a_lines[i - 1]
            b_line = b_lines[j - 1]
            sim = match_score_fn(a_line, b_line)
            pairs.append((a_line, b_line, sim))
            i -= 1
            j -= 1
        elif direction == "up":
            a_line = a_lines[i - 1]
            pairs.append((a_line, None, 0.0))
            i -= 1
        elif direction == "left":
            b_line = b_lines[j - 1]
            pairs.append((None, b_line, 0.0))
            j -= 1
        else:
            # at edges (should not normally happen because we set back on edges)
            if i > 0:
                pairs.append((a_lines[i - 1], None, 0.0))
                i -= 1
            elif j > 0:
                pairs.append((None, b_lines[j - 1], 0.0))
                j -= 1

    pairs.reverse()
    return pairs


def compare_texts(a: str, b: str, gap_penalty: float = 0.3) -> dict:
    a_lines = a.splitlines() if isinstance(a, str) else []
    b_lines = b.splitlines() if isinstance(b, str) else []
    pairs = needleman_wunsch_lines(a_lines, b_lines, line_similarity, gap_penalty)
    # overall score: average similarity over aligned pairs where both sides present
    sims = [s for (x, y, s) in pairs if x is not None and y is not None]
    total_pairs = len(pairs)
    overall = float(sum(sims) / total_pairs) if total_pairs > 0 else 0.0
    return {"overall_score": overall, "pairs": pairs}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two text columns in a CSV and add comparison results.")
    parser.add_argument("--input", required=True, help="Input CSV file path")
    parser.add_argument("--col_a", required=True, help="Name of first text column")
    parser.add_argument("--col_b", required=True, help="Name of second text column")
    parser.add_argument("--out", required=True, help="Output CSV file path")
    parser.add_argument("--newcol", default="comparison_result", help="Name for the new JSON result column")
    parser.add_argument("--gap_penalty", type=float, default=0.3, help="Gap penalty used in alignment (default 0.3)")

    args = parser.parse_args()

    # Read CSV (pandas optional). We use a neutral rows list to support both modes.
    if pd is not None:
        df = pd.read_csv(args.input)
        if args.col_a not in df.columns or args.col_b not in df.columns:
            raise KeyError(f"Columns not found in CSV: {args.col_a}, {args.col_b}")
        rows = df.to_dict(orient="records")
        columns = list(df.columns)
    else:
        with open(args.input, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            columns = reader.fieldnames or []
            rows = [r for r in reader]

    results = []
    for row in rows:
        a = row.get(args.col_a, "")
        b = row.get(args.col_b, "")
        res = compare_texts(str(a), str(b), gap_penalty=args.gap_penalty)
        res_serializable = {"overall_score": res["overall_score"], "pairs": [[x, y, s] for (x, y, s) in res["pairs"]]}
        results.append(json.dumps(res_serializable, ensure_ascii=False))

    # Attach and write out
    if pd is not None:
        df[args.newcol] = results
        df.to_csv(args.out, index=False)
    else:
        out_columns = list(columns)
        if args.newcol not in out_columns:
            out_columns.append(args.newcol)
        with open(args.out, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=out_columns)
            writer.writeheader()
            for r, res_json in zip(rows, results):
                out_row = dict(r)
                out_row[args.newcol] = res_json
                writer.writerow(out_row)


if __name__ == "__main__":
    main()
