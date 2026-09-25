#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

USER_AGENT = (
    "script:Funny-Memes:1.0 "
    "(by /u/Funny-Memes-Bot; repo:https://github.com/PopeValleyHicks-dev/Funny-Memes)"
)
DEFAULT_SUBREDDITS = [
    "memes",
    "dankmemes",
    "wholesomememes",
    "meirl",
    "funny",
]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch daily meme posts from public Reddit JSON feeds."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of meme posts to collect.",
    )
    parser.add_argument(
        "--limit-per-subreddit",
        type=int,
        default=100,
        help="Number of posts to inspect per subreddit feed.",
    )
    parser.add_argument(
        "--subreddit",
        action="append",
        dest="subreddits",
        help="Subreddit to include. Repeat to add multiple. Defaults to a built-in list.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("data/daily_memes.json"),
        help="Path for the generated JSON output.",
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=Path("data/daily_memes.md"),
        help="Path for the generated Markdown output.",
    )
    return parser.parse_args()


def fetch_feed(subreddit: str, limit: int) -> dict[str, Any]:
    url = f"https://www.reddit.com/r/{subreddit}/top.json?t=day&limit={limit}"
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def extract_image_url(post: dict[str, Any]) -> str | None:
    direct_url = post.get("url_overridden_by_dest") or post.get("url")
    if isinstance(direct_url, str) and has_image_extension(direct_url):
        return direct_url

    preview = post.get("preview") or {}
    images = preview.get("images") if isinstance(preview, dict) else None
    if images and isinstance(images, list):
        source = images[0].get("source") if isinstance(images[0], dict) else None
        if isinstance(source, dict):
            candidate = source.get("url")
            if isinstance(candidate, str):
                return candidate.replace("&amp;", "&")
    return None


def has_image_extension(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(extension) for extension in IMAGE_EXTENSIONS)


def post_to_item(post: dict[str, Any], subreddit: str) -> dict[str, Any] | None:
    if post.get("over_18") or post.get("stickied") or post.get("is_video"):
        return None

    image_url = extract_image_url(post)
    if not image_url:
        return None

    title = post.get("title")
    permalink = post.get("permalink")
    post_id = post.get("id")
    if not all(isinstance(value, str) and value for value in [title, permalink, post_id]):
        return None

    return {
        "id": post_id,
        "title": normalize_title(title),
        "subreddit": subreddit,
        "author": post.get("author"),
        "score": post.get("score"),
        "comments": post.get("num_comments"),
        "post_url": f"https://www.reddit.com{permalink}",
        "image_url": image_url,
    }


def normalize_title(title: str) -> str:
    return " ".join(title.split())


def collect_memes(subreddits: list[str], count: int, limit_per_subreddit: int) -> list[dict[str, Any]]:
    if count <= 0:
        return []

    seen_ids: set[str] = set()
    items: list[dict[str, Any]] = []

    for subreddit in subreddits:
        feed = fetch_feed(subreddit, limit_per_subreddit)
        children = feed.get("data", {}).get("children", [])
        for child in children:
            post = child.get("data") if isinstance(child, dict) else None
            if not isinstance(post, dict):
                continue

            item = post_to_item(post, subreddit)
            if not item or item["id"] in seen_ids:
                continue

            seen_ids.add(item["id"])
            items.append(item)
            if len(items) >= count:
                return items

    if len(items) < count:
        raise RuntimeError(
            f"Only collected {len(items)} memes from {len(subreddits)} subreddits; needed {count}."
        )

    return items


def render_markdown(items: list[dict[str, Any]], generated_at: str) -> str:
    lines = [
        "# Daily Funny Memes",
        "",
        f"Generated at: {generated_at}",
        "",
    ]

    for index, item in enumerate(items, start=1):
        lines.append(f"## {index}. {item['title']}")
        lines.append(f"- Source: r/{item['subreddit']}")
        lines.append(f"- Score: {item['score']}")
        lines.append(f"- Comments: {item['comments']}")
        lines.append(f"- Post: {item['post_url']}")
        lines.append(f"- Image: ![{item['title']}]({item['image_url']})")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_outputs(output_json: Path, output_markdown: Path, payload: dict[str, Any]) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    output_markdown.write_text(
        render_markdown(payload["items"], payload["generated_at"]),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    subreddits = args.subreddits or DEFAULT_SUBREDDITS

    try:
        items = collect_memes(subreddits, args.count, args.limit_per_subreddit)
    except (HTTPError, URLError, socket.timeout, TimeoutError, RuntimeError) as error:
        raise SystemExit(str(error)) from error

    payload = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "count": len(items),
        "sources": subreddits,
        "items": items,
    }
    write_outputs(args.output_json, args.output_markdown, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
