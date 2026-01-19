#!/usr/bin/env python3
"""
Build Knowledge Index (RoboCamp Knowledge Base)
Scans blog/articles/<slug>/<lang>/ and generates metadata/knowledge_index.json
Author: RoboCamp Team
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

# --- Ścieżki źródłowe i docelowe ---
BLOG_DIR = Path("blog/articles")
OUTPUT_DIR = Path("metadata")
OUTPUT_FILE = OUTPUT_DIR / "knowledge_index.json"


# --- Funkcja pomocnicza: wyciąganie metadanych z full.md ---
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


# --- Główna funkcja: zbieranie artykułów i rozdziałów ---
def collect_articles() -> list[dict]:
    """
    Traverse blog/articles/<slug>/<lang>/ recursively and collect all articles.
    """
    articles = []
    total_chapters = 0

    for article_dir in BLOG_DIR.iterdir():
        if not article_dir.is_dir():
            continue

        for lang_dir in article_dir.iterdir():
            if not lang_dir.is_dir():
                continue

            full_file = lang_dir / "full.md"
            chapters_files = sorted(lang_dir.glob("chapters_*.json"))

            if not full_file.exists() or not chapters_files:
                print(f"⚠️ Pomijam {lang_dir} – brak full.md lub chapters_*.json")
                continue

            meta = extract_meta(full_file)
            chapters = []

            for ch_file in chapters_files:
                try:
                    data = json.loads(ch_file.read_text(encoding="utf-8"))
                    # obsługa zarówno tablicy, jak i obiektu {"chapters": [...]}
                    if isinstance(data, dict) and "chapters" in data:
                        data = data["chapters"]

                    for ch in data:
                        chapters.append({
                            "chapter_id": ch.get("chapter_id"),
                            "title": ch.get("heading"),
                            "summary": ch.get("summary"),
                            "canonical_url": ch.get("canonical_url"),
                        })
                except Exception as e:
                    print(f"⚠️ Błąd w {ch_file}: {e}")

            total_chapters += len(chapters)

            articles.append({
                "slug": article_dir.name,
                "article_id": meta.get("article_id") or article_dir.name,
                "language": meta.get("language") or lang_dir.name,
                "title": meta.get("title") or article_dir.name,
                "canonical_url": meta.get("canonical_url", ""),
                "chapters": chapters,
            })

    print(f"✅ Zebrano {len(articles)} artykułów ({total_chapters} rozdziałów).")
    langs = {a['language'] for a in articles}
    print(f"🌍 Wykryte języki: {', '.join(sorted(langs))}")
    return articles


# --- Główna funkcja budująca indeks ---
def build_knowledge_index():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    articles = collect_articles()

    result = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sources": {
            "articles": articles,
            "social": []  # placeholder – dodamy później
        }
    }

    OUTPUT_FILE.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"💾 Zapisano plik: {OUTPUT_FILE.resolve()}")


# --- Punkt wejścia ---
if __name__ == "__main__":
    build_knowledge_index()
