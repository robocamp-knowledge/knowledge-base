#!/usr/bin/env python3
"""
Build Knowledge Index (Phase 2 – multilingual structure)
Scans blog/articles/<slug>/<lang>/ and generates metadata/knowledge_index.json
Author: RoboCamp Team
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

BLOG_DIR = Path("blog/articles")
OUTPUT_DIR = Path("metadata")
OUTPUT_FILE = OUTPUT_DIR / "knowledge_index.json"


def extract_meta(full_path: Path) -> dict:
    """
    Extract metadata fields from YAML-style header in full.md
    """
    if not full_path.exists():
        return {}

    content = full_path.read_text(encoding="utf-8")

    def match_field(field):
        pattern = rf'^{field}:\s*"?(.+?)"?$'
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1).strip() if match else ""

    return {
        "article_id": match_field("article_id"),
        "title": match_field("title"),
        "language": match_field("language") or full_path.parent.name,
        "canonical_url": match_field("canonical_url"),
    }


def collect_articles() -> list[dict]:
    """
    Traverse blog/articles/<slug>/<lang>/ and collect chapters + metadata
    """
    articles = []

    for article_dir in BLOG_DIR.iterdir():
        if not article_dir.is_dir():
            continue

        for lang_dir in article_dir.iterdir():
            if not lang_dir.is_dir():
                continue

            full_file = lang_dir / "full.md"
            chapters_files = sorted(lang_dir.glob("chapters_*.json"))

            if not full_file.exists() or not chapters_files:
                continue

            meta = extract_meta(full_file)
            chapters = []

            for ch_file in chapters_files:
                try:
                    data = json.loads(ch_file.read_text(encoding="utf-8"))
                    for ch in data.get("chapters", data):  # handle both wrapped/unwrapped formats
                        chapters.append({
                            "chapter_id": ch.get("chapter_id"),
                            "title": ch.get("heading"),
                            "summary": ch.get("summary"),
                            "canonical_url": ch.get("canonical_url"),
                        })
                except Exception as e:
                    print(f"⚠️ Error parsing {ch_file}: {e}")

            articles.append({
                "slug": article_dir.name,
                "article_id": meta.get("article_id") or article_dir.name,
                "language": meta.get("language") or lang_dir.name,
                "title": meta.get("title") or article_dir.name,
                "canonical_url": meta.get("canonical_url", ""),
                "chapters": chapters,
            })

    return articles


def build_knowledge_index():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    articles = collect_articles()

    result = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sources": {
            "articles": articles,
            "social": []  # placeholder for future
        }
    }

    OUTPUT_FILE.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"✅ Knowledge Index generated with {len(articles)} articles at: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_knowledge_index()
