import json
from collections import Counter
from datetime import datetime

INPUT_FILE = "social/social_posts.json"
OUTPUT_FILE = "social/social_posts.txt"


def format_date(iso_ts: str | None) -> str | None:
    if not iso_ts:
        return None
    try:
        return iso_ts.split("T")[0]
    except Exception:
        return None


def detect_post_type(platform: str, post_format: str | None, url: str) -> str:
    if platform == "Facebook":
        if post_format:
            pf = post_format.lower()
            if pf == "reel":
                return "Facebook reel"
            if pf == "post":
                return "Facebook post"
        # fallback (starsze dane)
        if url and "/reel/" in url:
            return "Facebook reel"
        return "Facebook post"

    if platform == "Instagram":
        if post_format:
            pf = post_format.lower()
            if pf == "sidecar":
                return "Instagram sidecar"
            if pf == "clips":
                return "Instagram clip"
        return "Instagram post"

    return platform or "Unknown"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

items = data.get("items", [])

blocks = []
index = 1

# META collectors
platform_counter = Counter()
language_counter = Counter()
type_counter = Counter()
dates = []

for item in items:
    text = (item.get("text") or "").strip()
    if not text:
        continue

    platform = item.get("platform", "unknown")
    post_format = item.get("post_format")
    language = item.get("language", "unknown")
    url = item.get("canonical_url", "")

    post_type = detect_post_type(platform, post_format, url)
    date = format_date(item.get("published_at"))
    tags = ", ".join(item.get("audience_tags", []))

    # Collect META
    platform_counter[platform] += 1
    language_counter[language] += 1
    type_counter[post_type] += 1
    if date:
        dates.append(date)

    block = f"""POST #{index}
Date: {date or "unknown"}
Type: {post_type}
Language: {language}
Tags: {tags}
URL: {url}

Content:
{text}
"""
    blocks.append(block)
    index += 1


# === META section ===

total_posts = len(blocks)

date_range = "unknown"
if dates:
    sorted_dates = sorted(dates)
    date_range = f"{sorted_dates[0]} → {sorted_dates[-1]}"

platforms_meta = ", ".join(
    f"{platform} ({count})" for platform, count in platform_counter.items()
)

languages_meta = ", ".join(
    f"{lang} ({count})" for lang, count in language_counter.items()
)

types_meta_lines = "\n".join(
    f"- {ptype}: {count}" for ptype, count in type_counter.items()
)

meta_block = f"""
=== META ===
Total posts: {total_posts}
Platforms: {platforms_meta}
Languages: {languages_meta}
Date range: {date_range}
Post types:
{types_meta_lines}
""".strip()

final_text = "\n---\n".join(blocks) + "\n\n" + meta_block

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(final_text)

print(f"[build_social_posts_txt] Generated {total_posts} posts → {OUTPUT_FILE}")
