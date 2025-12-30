#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cleaner for RoboCamp blog markdown.

Key goals:
- Deterministic cleaning (no LLM).
- Preserve section structure (headings) and anchor ids.
- Remove noise (TOC, HTML wrappers, kramdown attrs, images as files).
- Convert local anchor links "(#section)" -> "(<canonical_url>#section)".
- Shift headings down by 1 (# -> ##, ## -> ###, ...) because title is stored in YAML frontmatter.
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import re
import sys
from datetime import datetime
from typing import List, Tuple, Optional
from urllib.parse import urlsplit


@dataclasses.dataclass
class Stats:
    removed_toc_lines: int = 0
    removed_html_tags: int = 0
    converted_html_headings: int = 0
    removed_kramdown_attrs: int = 0
    converted_images: int = 0
    converted_anchor_links: int = 0
    shifted_heading_lines: int = 0
    collapsed_blank_lines: int = 0


HTML_TAGS_STRIP = ("div", "span", "section", "aside")
HTML_HEADING_RE = re.compile(r"<\s*(h[1-6])\b[^>]*>(.*?)<\s*/\s*\1\s*>", re.IGNORECASE | re.DOTALL)

# Kramdown-style attribute lists, commonly used in your sources:
# - after images/links: `![...](...){: ...}`
# - standalone: `{: ...}`
KRAMDOWN_ATTR_AFTER_PAREN_RE = re.compile(r"\)\s*\{\:\s*[^}]*\}")
KRAMDOWN_ATTR_STANDALONE_RE = re.compile(r"^\s*\{\:\s*[^}]*\}\s*$")

TOC_LINE_RE = re.compile(r"^\s*\[(toc|TOC)\]\s*$")

# Markdown image: ![alt](url)
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

# Markdown local anchor links: ( #something )
LOCAL_ANCHOR_LINK_RE = re.compile(r"\]\(\s*#([^) \t]+)\s*\)")

# ATX headings line: one to six hashes at start
ATX_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")

# Strip simple HTML tags we don't want to keep (opening/closing only)
def _strip_simple_html_tags(line: str, stats: Stats) -> str:
    # Remove tags like <div ...>, </div>, <section>, </section> etc.
    before = line
    for tag in HTML_TAGS_STRIP:
        line = re.sub(rf"</?\s*{tag}\b[^>]*>", "", line, flags=re.IGNORECASE)
    if line != before:
        stats.removed_html_tags += 1
    return line


def _convert_html_headings(text: str, stats: Stats) -> str:
    # Convert <h3>Title</h3> -> ### Title (preserving inner text)
    def repl(m: re.Match) -> str:
        level = int(m.group(1)[1])
        inner = m.group(2)
        # Clean inner text from newlines / excessive spaces
        inner = re.sub(r"\s+", " ", inner).strip()
        hashes = "#" * level
        stats.converted_html_headings += 1
        return f"{hashes} {inner}"
    return re.sub(HTML_HEADING_RE, repl, text)


def _remove_toc_lines(lines: List[str], stats: Stats) -> List[str]:
    out = []
    for ln in lines:
        if TOC_LINE_RE.match(ln):
            stats.removed_toc_lines += 1
            continue
        out.append(ln)
    return out


def _remove_kramdown_attrs(lines: List[str], stats: Stats) -> List[str]:
    out = []
    for ln in lines:
        before = ln
        # remove standalone {: ...}
        if KRAMDOWN_ATTR_STANDALONE_RE.match(ln):
            stats.removed_kramdown_attrs += 1
            continue
        # remove `){: ...}` pattern
        ln2 = re.sub(KRAMDOWN_ATTR_AFTER_PAREN_RE, ")", ln)
        if ln2 != before:
            stats.removed_kramdown_attrs += 1
        out.append(ln2)
    return out


def _convert_images(lines: List[str], stats: Stats) -> List[str]:
    out = []
    for ln in lines:
        m = MD_IMAGE_RE.search(ln)
        if not m:
            out.append(ln)
            continue

        # Replace each image in line. Keep alt text as plain text.
        def repl(mm: re.Match) -> str:
            alt = (mm.group(1) or "").strip()
            if not alt:
                alt = "Image"
            stats.converted_images += 1
            # Keep this short and non-invasive:
            # - does not create headings, does not create links
            return f"({alt})"

        out.append(re.sub(MD_IMAGE_RE, repl, ln))
    return out


def _convert_local_anchor_links(lines: List[str], canonical_url: str, stats: Stats) -> List[str]:
    if not canonical_url:
        return lines

    canonical = canonical_url.strip()
    # ensure it ends with "/" or at least not break anchors; do not force slash if already has query etc.
    # For your blog canonical URLs, trailing "/" is standard. Keep if present.
    def repl(m: re.Match) -> str:
        anchor = m.group(1)
        stats.converted_anchor_links += 1
        return f"]({canonical}#{anchor})"

    out = []
    for ln in lines:
        out.append(re.sub(LOCAL_ANCHOR_LINK_RE, repl, ln))
    return out


def _absolutize_root_relative_links(lines: List[str], canonical_url: str) -> List[str]:
    """
    Convert Markdown inline links [text](/path...) to [text](<site_base>/path...),
    where site_base is derived from canonical_url (scheme + netloc).
    Does NOT touch:
      - anchors: (#...)
      - absolute URLs with scheme: https:, http:, mailto:, tel:, etc.
      - protocol-relative URLs: //...
      - non-root-relative paths: ./..., ../..., foo/bar
    """
    site_base = "https://www.robocamp.pl"
    if canonical_url:
        parts = urlsplit(canonical_url.strip())
        if parts.scheme and parts.netloc:
            site_base = f"{parts.scheme}://{parts.netloc}"

    # Inline markdown links: [label](url...)
    # We only rewrite if the first URL token starts with "/".
    pattern = re.compile(r"(\[[^\]]*\]\()([^)]+)(\))")

    def repl(m: re.Match) -> str:
        prefix, url_part, suffix = m.group(1), m.group(2), m.group(3)
        raw = url_part.strip()

        # split URL and optional title: (url "title")
        # keep spacing minimal: we preserve everything after the first token.
        if not raw:
            return m.group(0)

        first, *rest = raw.split(maxsplit=1)
        tail = (" " + rest[0]) if rest else ""

        u = first

        # do not touch anchors, scheme URLs, or protocol-relative
        if u.startswith("#"):
            return prefix + url_part + suffix
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", u):
            return prefix + url_part + suffix
        if u.startswith("//"):
            return prefix + url_part + suffix

        if u.startswith("/"):
            new_first = site_base.rstrip("/") + u
            return prefix + (new_first + tail) + suffix

        return prefix + url_part + suffix

    out = []
    for ln in lines:
        out.append(re.sub(pattern, repl, ln))
    return out


def _shift_atx_headings(lines: List[str], stats: Stats) -> List[str]:
    """
    Shift headings by +1 level:
      #  -> ##
      ## -> ###
      ...
      ##### -> ######
      ###### stays ###### (cap at 6)
    Do not modify inside fenced code blocks.
    """
    out = []
    in_code = False
    for ln in lines:
        if ln.strip().startswith("```"):
            in_code = not in_code
            out.append(ln)
            continue
        if in_code:
            out.append(ln)
            continue

        m = ATX_HEADING_RE.match(ln)
        if not m:
            out.append(ln)
            continue

        hashes, rest = m.group(1), m.group(2)
        level = len(hashes)
        new_level = min(6, level + 1)
        if new_level != level:
            stats.shifted_heading_lines += 1
        out.append("#" * new_level + " " + rest.rstrip() + "\n")
    return out


def _strip_html_wrappers(lines: List[str], stats: Stats) -> List[str]:
    out = []
    for ln in lines:
        out.append(_strip_simple_html_tags(ln, stats))
    return out


def _collapse_blank_lines(lines: List[str], stats: Stats) -> List[str]:
    out = []
    blank_run = 0
    for ln in lines:
        if ln.strip() == "":
            blank_run += 1
            if blank_run > 1:
                stats.collapsed_blank_lines += 1
                continue
            out.append("\n")
        else:
            blank_run = 0
            out.append(ln.rstrip() + "\n")
    return out


def _frontmatter(
    article_id: str,
    title: str,
    language: str,
    authors: List[str],
    canonical_url: str,
    web_slug: str,
    published: str,
    license_name: str,
    status: str,
) -> str:
    # Basic YAML with safe quoting.
    # Authors is a YAML list.
    def q(s: str) -> str:
        s = s.replace('"', '\\"')
        return f"\"{s}\""

    author_lines = "\n".join([f"  - {q(a)}" for a in authors])

    fm = (
        "---\n"
        f"article_id: {q(article_id)}\n"
        f"title: {q(title)}\n"
        f"language: {q(language)}\n"
        "author:\n"
        f"{author_lines}\n"
        f"canonical_url: {q(canonical_url)}\n"
        f"web_slug: {q(web_slug)}\n"
        f"published: {published}\n"
        f"license: {q(license_name)}\n"
        f"status: {status}\n"
        "---\n\n"
    )
    return fm


def clean_markdown(md_text: str, canonical_url: str, stats: Stats) -> str:
    # 1) Convert HTML headings first at text-level (because they can span multiple lines)
    md_text = _convert_html_headings(md_text, stats)

    # split into lines for deterministic line-based transforms
    lines = md_text.splitlines(keepends=True)

    # 2) Remove TOC lines
    lines = _remove_toc_lines(lines, stats)

    # 3) Strip simple HTML wrappers
    lines = _strip_html_wrappers(lines, stats)

    # 4) Remove kramdown attrs
    lines = _remove_kramdown_attrs(lines, stats)

    # 5) Convert images to alt-text markers
    lines = _convert_images(lines, stats)

    # 6) Convert local anchor links to canonical_url#anchor
    lines = _convert_local_anchor_links(lines, canonical_url, stats)

    # 6.5) Convert root-relative links to absolute site links
    lines = _absolutize_root_relative_links(lines, canonical_url)

    # 7) Shift headings
    lines = _shift_atx_headings(lines, stats)

    # 8) Collapse excessive blank lines
    lines = _collapse_blank_lines(lines, stats)

    return "".join(lines).strip() + "\n"


def parse_authors(raw: str) -> List[str]:
    parts = [p.strip() for p in (raw or "").split(",")]
    authors = [p for p in parts if p]
    return authors


def validate_date(date_str: str) -> str:
    # Expect YYYY-MM-DD
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError as e:
        raise ValueError(f"Invalid date format (expected YYYY-MM-DD): {date_str}") from e


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Path to source markdown file (robocamp-new-web content.md)")
    ap.add_argument("--out", required=True, help="Path to output markdown file (knowledge-base target full.md)")
    ap.add_argument("--article-id", required=True)
    ap.add_argument("--web-slug", required=True)
    ap.add_argument("--language", required=True, choices=["pl", "en"])
    ap.add_argument("--title", required=True)
    ap.add_argument("--authors", required=True, help="Comma-separated list of authors")
    ap.add_argument("--canonical-url", required=True)
    ap.add_argument("--published", required=True, help="YYYY-MM-DD")
    ap.add_argument("--license", default="CC BY-NC 4.0")
    ap.add_argument("--status", default="published")
    ap.add_argument("--debug", action="store_true")

    args = ap.parse_args()

    published = validate_date(args.published)
    authors = parse_authors(args.authors)
    if not authors:
        print("ERROR: authors list is empty after parsing.", file=sys.stderr)
        return 2

    src_path = args.src
    out_path = args.out

    if not os.path.isfile(src_path):
        print(f"ERROR: source file not found: {src_path}", file=sys.stderr)
        return 2

    with open(src_path, "r", encoding="utf-8") as f:
        src_text = f.read()

    stats = Stats()
    cleaned_body = clean_markdown(src_text, args.canonical_url, stats)

    fm = _frontmatter(
        article_id=args.article_id,
        title=args.title,
        language=args.language,
        authors=authors,
        canonical_url=args.canonical_url,
        web_slug=args.web_slug,
        published=published,
        license_name=args.license,
        status=args.status,
    )

    final_text = fm + cleaned_body

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(final_text)

    if args.debug:
        print("CLEANER DEBUG STATS")
        print(f"- removed_toc_lines: {stats.removed_toc_lines}")
        print(f"- removed_html_tags: {stats.removed_html_tags}")
        print(f"- converted_html_headings: {stats.converted_html_headings}")
        print(f"- removed_kramdown_attrs: {stats.removed_kramdown_attrs}")
        print(f"- converted_images: {stats.converted_images}")
        print(f"- converted_anchor_links: {stats.converted_anchor_links}")
        print(f"- shifted_heading_lines: {stats.shifted_heading_lines}")
        print(f"- collapsed_blank_lines: {stats.collapsed_blank_lines}")
        print(f"OUTPUT: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
