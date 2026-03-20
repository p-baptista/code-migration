import argparse
import csv
import difflib
from typing import List, Dict, Optional


def calculate_similarity(str1: str, str2: str) -> float:
    if not str1 and not str2:
        return 100.0
    return difflib.SequenceMatcher(None, str1, str2).ratio() * 100


def text_diff_analysis(old_text: str, new_text: str) -> List[Dict]:
    """Produce a line-aligned diff with similarity per pair and line indices.

    Each result item contains:
      - old_index (1-based) or None
      - new_index (1-based) or None
      - line_old: original line or None
      - line_new: new line or None
      - absolute_diff: one of 'equal','modified','removed','added'
      - similarity: percentage (0-100) for modified/equals, 0 for pure adds/removes
    """
    lines1 = old_text.splitlines() if old_text is not None else []
    lines2 = new_text.splitlines() if new_text is not None else []

    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    results: List[Dict] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for i, j in zip(range(i1, i2), range(j1, j2)):
                results.append({
                    "old_index": i + 1,
                    "new_index": j + 1,
                    "line_old": lines1[i],
                    "line_new": lines2[j],
                    "absolute_diff": "equal",
                    "similarity": 100.0,
                })
        elif tag == 'replace':
            # number of lines might differ between the replaced spans
            max_range = max(i2 - i1, j2 - j1)
            for offset in range(max_range):
                oi = i1 + offset
                nj = j1 + offset
                l1: Optional[str] = lines1[oi] if oi < i2 else None
                l2: Optional[str] = lines2[nj] if nj < j2 else None

                sim = calculate_similarity(l1 or "", l2 or "")
                results.append({
                    "old_index": (oi + 1) if l1 is not None else None,
                    "new_index": (nj + 1) if l2 is not None else None,
                    "line_old": l1,
                    "line_new": l2,
                    "absolute_diff": "modified",
                    "similarity": round(sim, 2),
                })
        elif tag == 'delete':
            for i in range(i1, i2):
                results.append({
                    "old_index": i + 1,
                    "new_index": None,
                    "line_old": lines1[i],
                    "line_new": None,
                    "absolute_diff": "removed",
                    "similarity": 0.0,
                })
        elif tag == 'insert':
            for j in range(j1, j2):
                results.append({
                    "old_index": None,
                    "new_index": j + 1,
                    "line_old": None,
                    "line_new": lines2[j],
                    "absolute_diff": "added",
                    "similarity": 0.0,
                })

    return results


def print_lines_mode(diff_results: List[Dict]):
    """Print only lines with any difference (added/removed/modified)."""
    for item in diff_results:
        if item['absolute_diff'] == 'equal':
            continue
        oi = item['old_index'] or '-'
        nj = item['new_index'] or '-'
        tag = item['absolute_diff']
        if tag == 'modified':
            print(f"[MOD] old:{oi} new:{nj} (sim={item['similarity']}%)")
            print(f"  - {repr(item['line_old'])}")
            print(f"  + {repr(item['line_new'])}")
        elif tag == 'removed':
            print(f"[REM] old:{oi}")
            print(f"  - {repr(item['line_old'])}")
        elif tag == 'added':
            print(f"[ADD] new:{nj}")
            print(f"  + {repr(item['line_new'])}")


def print_similarity_mode(old_text: str, new_text: str, diff_results: List[Dict], top_n: int = 10):
    overall = round(calculate_similarity(old_text or "", new_text or ""), 2)
    print(f"Overall similarity: {overall}%")

    # collect modified lines and sort by lowest similarity (most changed)
    modified = [r for r in diff_results if r['absolute_diff'] == 'modified']
    modified_sorted = sorted(modified, key=lambda r: r['similarity'])

    print(f"Top {min(top_n, len(modified_sorted))} modified line pairs (least similar first):")
    for item in modified_sorted[:top_n]:
        oi = item['old_index'] or '-'
        nj = item['new_index'] or '-'
        print(f"- old:{oi} new:{nj} sim={item['similarity']}%")
        print(f"    - {repr(item['line_old'])}")
        print(f"    + {repr(item['line_new'])}")


def _read_csv_row(csv_path: str, row_number: int = 1) -> Dict[str, str]:
    # row_number is 1-based (first data row is 1)
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            if idx == row_number:
                return row
    raise IndexError(f"CSV does not contain row {row_number}")


def main():
    parser = argparse.ArgumentParser(description="Line-level diff finder with modes: lines or similarity")
    parser.add_argument('--mode', choices=['lines', 'similarity'], default='lines', help='Output mode')
    parser.add_argument('--file1', help='Path to original file')
    parser.add_argument('--file2', help='Path to new file')
    parser.add_argument('--csv', default='input/python/treated_python_commits.csv', help='Path to CSV with before/after columns')
    parser.add_argument('--row', type=int, default=1, help='Row number in CSV to use (1-based)')
    parser.add_argument('--top', type=int, default=10, help='Top N modified lines to show in similarity mode')

    args = parser.parse_args()

    old_text = None
    new_text = None

    if args.file1 and args.file2:
        with open(args.file1, 'r', encoding='utf-8') as f:
            old_text = f.read()
        with open(args.file2, 'r', encoding='utf-8') as f:
            new_text = f.read()
    else:
        # try CSV path
        try:
            row = _read_csv_row(args.csv, args.row)
            old_text = row.get('before') or ''
            new_text = row.get('after') or ''
        except Exception as e:
            print(f"Failed to read inputs: {e}")
            return

    diff_results = text_diff_analysis(old_text, new_text)

    if args.mode == 'lines':
        print_lines_mode(diff_results)
    else:
        print_similarity_mode(old_text, new_text, diff_results, top_n=args.top)


if __name__ == '__main__':
    main()