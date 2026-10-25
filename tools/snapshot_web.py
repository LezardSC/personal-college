"""Save a web page as a Markdown snapshot under resources/web/<topic>/<name>.md.

Usage: .venv/bin/python -I tools/snapshot_web.py <url> <topic> <name> [--refresh]
The root is $COLLEGE_ROOT, else the repository root. Exit code 2 (one line on
stderr) on fetch failure, empty extraction, invalid names or an existing file.
"""
import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

import trafilatura

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def _check_slug(label: str, value: str) -> None:
    if not SLUG.fullmatch(value):
        raise ValueError(f"invalid {label} {value!r}: use lowercase letters, digits and hyphens")


def to_markdown(html: str, url: str, retrieved_on: date) -> str:
    body = trafilatura.extract(
        html,
        output_format="markdown",
        include_formatting=True,
        include_links=True,
        include_tables=True,
    )
    if not body or not body.strip():
        raise ValueError("no readable content extracted from the page")
    return f"<!-- source: {url} -->\n<!-- retrieved: {retrieved_on.isoformat()} -->\n\n{body.strip()}\n"


def write_snapshot(root: Path, topic: str, name: str, content: str, refresh: bool = False) -> Path:
    _check_slug("topic", topic)
    _check_slug("name", name)
    path = Path(root) / "resources" / "web" / topic / f"{name}.md"
    if path.exists() and not refresh:
        raise FileExistsError(f"{path} already exists (use --refresh to overwrite)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _root() -> Path:
    env = os.environ.get("COLLEGE_ROOT")
    return Path(env) if env else Path(__file__).resolve().parents[1]


def main(argv=None, fetch=trafilatura.fetch_url) -> int:
    parser = argparse.ArgumentParser(description="Snapshot a web page as Markdown.")
    parser.add_argument("url")
    parser.add_argument("topic")
    parser.add_argument("name")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args(argv)
    try:
        _check_slug("topic", args.topic)
        _check_slug("name", args.name)
        try:
            html = fetch(args.url)
        except Exception as e:
            raise OSError(f"could not fetch {args.url}: {e}") from e
        if not html:
            raise OSError(f"could not fetch {args.url}")
        content = to_markdown(html, args.url, date.today())
        path = write_snapshot(_root(), args.topic, args.name, content, args.refresh)
    except (ValueError, OSError) as e:  # FileExistsError is an OSError
        print(f"snapshot_web: {e}", file=sys.stderr)
        return 2
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
