import os
import re

# usage: python parser.py /path/to/your/folder --output codes
# where 'codes' is the output folder name

def extract_code_blocks(text: str) -> list[str]:
    pattern = r"```(?:\w+)?\s*(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return [m.strip() for m in matches]


def process_directory(input_dir: str, output_dir: str = "output"):
    block_counter = 0

    for root, _, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith(".txt"):
                input_path = os.path.join(root, filename)

                with open(input_path, "r", encoding="utf-8") as f:
                    content = f.read()

                code_blocks = extract_code_blocks(content)
                if not code_blocks:
                    continue

                relative_path = os.path.relpath(root, input_dir)
                target_dir = os.path.join(output_dir, relative_path)
                os.makedirs(target_dir, exist_ok=True)

                for i, block in enumerate(code_blocks, 1):
                    block_counter += 1
                    output_file = os.path.join(
                        target_dir,
                        f"{os.path.splitext(filename)[0]}.txt"
                    )
                    with open(output_file, "w", encoding="utf-8") as out:
                        out.write(block)

    print(f"Extraction complete! {block_counter} blocks saved in '{output_dir}/'")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract code blocks from .txt files, preserving folder structure")
    parser.add_argument("input_dir", help="Directory containing .txt files")
    parser.add_argument("--output", default="output", help="Output directory (default: output)")

    args = parser.parse_args()
    process_directory(args.input_dir, args.output)
