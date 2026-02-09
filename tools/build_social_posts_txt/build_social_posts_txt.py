import json

INPUT_FILE = "social/social_posts.json"
OUTPUT_FILE = "social/social_posts.txt"


def format_date(iso_ts: str | None) -> str:
    if not iso_ts:
        return "unknown"
    try:
        return iso_ts.split("T")[0]
    except Exception:
        return "unknown"


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

items = data.get("items", [])

blocks = []
index = 1

for item in items:
    text = (item.get("text") or "").strip()
    if not text:
        continue

    date = format_date(item.get("published_at"))
    platform = item.get("platform", "unknown")
    language = item.get("language", "unknown")
    url = item.get("canonical_url", "")
    tags = ", ".join(item.get("audience_tags", []))

    block = f"""POST #{index}
Date: {date}
Platform: {platform}
Language: {language}
Tags: {tags}
URL: {url}

Content:
{text}
"""
    blocks.append(block)
    index += 1

final_text = "\n---\n".join(blocks)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(final_text)

print(f"[build_social_posts_txt] Generated {len(blocks)} posts → {OUTPUT_FILE}")
