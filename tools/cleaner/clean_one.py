#!/usr/bin/env python3

import argparse
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description="Clean ONE blog article")
    parser.add_argument("--article-id", required=True)
    parser.add_argument("--lang", required=True)
    parser.add_argument("--src", required=True)
    parser.add_argument("--target", required=True)

    args = parser.parse_args()

    src = Path(args.src)
    target = Path(args.target)

    if not src.exists():
        print(f"[ERROR] Source file does not exist: {src}", file=sys.stderr)
        sys.exit(1)

    target.parent.mkdir(parents=True, exist_ok=True)

    raw = src.read_text(encoding="utf-8")

    # NA RAZIE: czyste kopiowanie (cleaner v0)
    # później tu dodasz:
    # - usuwanie obrazków
    # - TOC
    # - normalizację nagłówków
    cleaned = raw.strip() + "\n"

    target.write_text(cleaned, encoding="utf-8")

    print(f"[OK] Cleaned article written to {target}")


if __name__ == "__main__":
    main()
