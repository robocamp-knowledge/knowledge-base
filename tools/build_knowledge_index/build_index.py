#!/usr/bin/env python3
"""
Build Knowledge Index (Phase 1)
Scans blog/articles and generates metadata/knowledge_index.json
Author: RoboCamp Team
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path

BLOG_DIR = Path("blog/articles")
OUTPUT_DIR = Path("metadata")
OUTPUT_FILE = OUTPUT_DIR / "knowledge_index.json"


def extract_meta(full_path: Path) -> dict:
    """Extract minimal metadata (title, language, canonical_url) from full.md"""
    if not full_path.exists():
        return {}
    content = full_path.read_text(encoding="utf-8")

    def match_field(field):
        pattern = rf"{field}:\s*(.+)"
        match = re.search(pattern, content)
        return match.group(1).strip() if match else ""

    return {
        "title": match_field("title"),
        "language": match_field("language") or "en",
        "canonical_url": match_field("canonical_url"),
    }


def collect_articles() -> list[dict]:
    """Walk through all article directories and collect chapter data."""
    articles = []

    for article_dir in BLOG_DIR.iterdir():
        if not article_dir.is_dir():
            continue

        # expected files
        full_file = article_dir / "full.md"
        chapters_files = [f for f in article_dir.glob("chapters_*.json")]

        if not chapters_files:
            continue

        meta = extract_meta(full_file)
        chapters = []

        for file in chapters_files:
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                for ch in data:
                    chapters.append({
                        "chapter_id": ch.get("chapter_id"),
                        "title": ch.get("heading"),
                        "summary": ch.get("summary"),
                        "canonical_url": ch.get("canonical_url"),
                    })
            except Exception as e:
                print(f"⚠️ Error parsing {file}: {e}")

        articles.append({
            "slug": article_dir.name,
            "title": meta.get("title") or article_dir.name,
            "language": meta.get("language", "en"),
            "canonical_url": meta.get("canonical_url", ""),
            "chapters": chapters,
        })

    return articles


def build_knowledge_index():
    """Main builder function"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sources": {
            "articles": collect_articles(),
            "social": []  # placeholder for future
        }
    }

    OUTPUT_FILE.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"✅ Knowledge Index generated at: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_knowledge_index()
