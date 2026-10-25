"""Extract a PDF book's text, page by page, and its table of contents.

Usage: .venv/bin/python -I tools/extract_pdf.py <pdf> resources/text <slug>
Writes <slug>.txt (a "=== page N ===" marker before each page) and <slug>.toc.md
(the PDF outline, indented by level). N is the page label shown by PDF viewers
("xiii", "42"...), not the index of the page in the file.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader


SLUG = re.compile(r"[a-z0-9][a-z0-9-]*")


def _write_atomic(path: Path, text: str) -> None:
    """Write to a temporary file next to `path`, then replace: never a partial file."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def _toc(reader: PdfReader, entries, level: int = 0) -> list[str]:
    lines = []
    for entry in entries:
        if isinstance(entry, list):
            lines += _toc(reader, entry, level + 1)
            continue
        try:
            page = reader.page_labels[reader.get_destination_page_number(entry)]
        except Exception:
            page = "?"
        lines.append(f"{'  ' * level}- {entry.title.strip()} — page {page}")
    return lines


def extract(pdf: Path, out_dir: Path, slug: str) -> None:
    if not SLUG.fullmatch(slug):
        raise ValueError(f"invalid slug {slug!r}: use lowercase letters, digits and hyphens")
    reader = PdfReader(str(pdf))
    out_dir.mkdir(parents=True, exist_ok=True)
    parts, empty = [], 0
    for label, page in zip(reader.page_labels, reader.pages):
        parts.append(f"\n=== page {label} ===\n")
        try:
            text = page.extract_text() or ""
        except Exception as e:
            text = f"[extraction failed: {e}]"
        empty += not text.strip()
        parts.append(text)
    _write_atomic(out_dir / f"{slug}.txt", "".join(parts))
    toc = _toc(reader, reader.outline) if reader.outline else []
    header = [
        f"# Table of contents — {pdf.name}",
        "",
        f"{len(reader.pages)} pages. Numbers = pages shown by the PDF viewer (markers `=== page N ===` in {slug}.txt).",
        "",
    ]
    body = toc or ["*No outline in this PDF: rebuild the TOC from the text's headings (see /enroll).*"]
    _write_atomic(out_dir / f"{slug}.toc.md", "\n".join(header + body) + "\n")
    if len(reader.pages) and empty / len(reader.pages) > 0.5:
        print(f"extract_pdf: warning: {empty}/{len(reader.pages)} pages have no text; "
              "likely a scanned PDF (no OCR): report it in /enroll.", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    try:
        extract(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
    except ValueError as e:
        sys.exit(f"extract_pdf: {e}")
