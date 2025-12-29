#!/usr/bin/env python3
import argparse
import re
from pathlib import Path
from typing import Tuple

FM_RE = re.compile(r"(?s)\A---\n.*?\n---\n")

def split_frontmatter(md: str) -> Tuple[str, str]:
    m = FM_RE.match(md)
    if not m:
        return "", md
    fm = m.group(0)
    body = md[len(fm):]
    return fm, body

def clean_raw_markdown(md: str) -> str:
    # Remove [TOC]
    md = re.sub(r"(?im)^\[TOC\]\s*$", "", md)

    # Remove markdown images with optional kramdown attrs: ![alt](url){: ...}
    md = re.sub(r"!\[[^\]]*\]\([^\)]*\)\s*\{:[^}]*\}\s*", "", md)
    # Remove plain markdown images: ![alt](url)
    md = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", md)

    # Remove standalone kramdown attribute lines: {: ...}
    md = re.sub(r"(?im)^\{:[^}]*\}\s*$", "", md)

    # Remove kramdown attrs appended to links: [text](url){:...}
    md = re.sub(r"(\[[^\]]+\]\([^)]+\))\s*\{:[^}]*\}", r"\1", md)

    # Normalize simple HTML headings <h3>Title</h3> -> ### Title
    md = re.sub(r"(?is)<h3>\s*(.*?)\s*</h3>", r"### \1", md)

    # Replace <br> / <br/> with newline
    md = re.sub(r"(?i)<br\s*/?>", "\n", md)

    # Normalize excessive blank lines
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"
    return md

def update_full_md(full_path: Path, cleaned_body: str) -> None:
    if not full_path.exists():
        raise FileNotFoundError(
            f"Target full.md not found: {full_path}\n"
            f"Create it first (even with only frontmatter), then rerun the workflow."
        )

    existing = full_path.read_text(encoding="utf-8")
    fm, _old_body = split_frontmatter(existing)

    # Ensure exactly one blank line after frontmatter
    if fm and not fm.endswith("\n\n"):
        fm = fm.rstrip("\n") + "\n\n"

    full_path.write_text(fm + cleaned_body, encoding="utf-8")

def main() -> None:
    p = argparse.ArgumentParser(description="Sync & clean one article (one language) from robocamp-new-web to knowledge-base.")
    p.add_argument("--article-id", required=True, help="e.g. lego-science-review")
    p.add_argument("--lang", required=True, choices=["pl", "en"])
    p.add_argument("--src-repo-path", required=True,
                   help="Path inside robocamp-new-web, e.g. data/blogposts/en/lego-science-review/content.md")
    args = p.parse_args()

    # Source repo checkout path (as per workflow)
    src_root = Path("_sources/robocamp-new-web")
    src = src_root / args.src_repo_path

    # Target path in knowledge-base
    tgt = Path(f"blog/articles/{args.article_id}/{args.lang}/full.md")

    if not src.exists():
        raise FileNotFoundError(
            f"Source file not found in robocamp-new-web checkout:\n"
            f"  {src}\n\n"
            f"Check:\n"
            f"  - src_repo_path input\n"
            f"  - that robocamp-new-web was checked out correctly\n"
            f"  - the file exists on the default branch of robocamp-new-web\n"
        )

    # Read & clean
    raw = src.read_text(encoding="utf-8")
    cleaned = clean_raw_markdown(raw)

    # Write into existing full.md preserving frontmatter
    update_full_md(tgt, cleaned)

    print(f"OK: Updated target:\n  {tgt}\nfrom source:\n  {src}")

if __name__ == "__main__":
    main()
