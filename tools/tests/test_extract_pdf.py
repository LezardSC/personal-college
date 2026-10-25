import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pypdf import PdfWriter

from tools import extract_pdf


def blank_pdf(path: Path, pages: int = 3) -> Path:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=200, height=200)
    with open(path, "wb") as f:
        writer.write(f)
    return path


class TestExtractPdf(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.pdf = blank_pdf(self.dir / "book.pdf")
        self.out = self.dir / "out"

    def tearDown(self):
        self._tmp.cleanup()

    def run_extract(self, slug="book"):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            extract_pdf.extract(self.pdf, self.out, slug)
        return err.getvalue()

    def test_writes_text_and_toc(self):
        self.run_extract()
        self.assertIn("=== page 1 ===", (self.out / "book.txt").read_text())
        self.assertTrue((self.out / "book.toc.md").exists())
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), ["book.toc.md", "book.txt"])

    def test_blank_pages_warn_about_scan(self):
        self.assertIn("scanned", self.run_extract())

    def test_text_pages_do_not_warn(self):
        with mock.patch("pypdf.PageObject.extract_text", return_value="some text"):
            self.assertEqual(self.run_extract(), "")

    def test_path_like_slug_rejected(self):
        for slug in ("../x", "a/b", "", "-x", "A"):
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                self.run_extract(slug)
        self.assertFalse(self.out.exists() and any(self.out.iterdir()))

    def test_crash_leaves_no_partial_file(self):
        with mock.patch("os.replace", side_effect=OSError("boom")), self.assertRaises(OSError):
            self.run_extract()
        self.assertEqual(list(self.out.iterdir()), [])
