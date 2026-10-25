"""Extract a PDF book's text, page by page, and its table of contents.

Usage: .venv/bin/python -I tools/extract_pdf.py <pdf> resources/text <slug>
Writes <slug>.txt (a "=== page N ===" marker before each page) and <slug>.toc.md
(the PDF outline, indented by level). N is the page label shown by PDF viewers
("xiii", "42"...), not the index of the page in the file.
"""
import sys
from pathlib import Path

from pypdf import PdfReader


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
    reader = PdfReader(str(pdf))
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"{slug}.txt", "w", encoding="utf-8") as f:
        for label, page in zip(reader.page_labels, reader.pages):
            f.write(f"\n=== page {label} ===\n")
            try:
                f.write(page.extract_text() or "")
            except Exception as e:
                f.write(f"[extraction failed: {e}]")
    toc = _toc(reader, reader.outline) if reader.outline else []
    header = [
        f"# Table of contents — {pdf.name}",
        "",
        f"{len(reader.pages)} pages. Numbers = pages shown by the PDF viewer (markers `=== page N ===` in {slug}.txt).",
        "",
    ]
    body = toc or ["*No outline in this PDF: rebuild the TOC from the text's headings (see /enroll).*"]
    (out_dir / f"{slug}.toc.md").write_text("\n".join(header + body) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    extract(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
