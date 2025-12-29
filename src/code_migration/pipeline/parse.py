from __future__ import annotations

import os
import re
from pathlib import Path


def extract_code_blocks(text: str) -> list[str]:
    pattern = r"```(?:\w+)?\s*(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return [m.strip() for m in matches] if matches else [text.strip()]


def run_parse(*, input_dir: str, out_dir: str, policy: str = "first") -> None:
    in_dir = Path(input_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    for root, _, files in os.walk(in_dir):
        for filename in files:
            if not filename.endswith(".txt"):
                continue
            src = Path(root) / filename
            content = src.read_text(encoding="utf-8")
            blocks = extract_code_blocks(content)

            rel = Path(root).relative_to(in_dir)
            target_dir = out / rel
            target_dir.mkdir(parents=True, exist_ok=True)

            stem = Path(filename).stem
            if policy == "first":
                (target_dir / f"{stem}.txt").write_text(blocks[0], encoding="utf-8")
            elif policy == "all_concat":
                (target_dir / f"{stem}.txt").write_text("\n\n".join(blocks), encoding="utf-8")
            elif policy == "all_separate":
                for i, b in enumerate(blocks, 1):
                    (target_dir / f"{stem}__block{i}.txt").write_text(b, encoding="utf-8")
            else:
                raise ValueError(f"Unknown policy: {policy}")


