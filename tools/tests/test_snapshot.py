import contextlib
import io
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tools import snapshot_web as sw

HTML = """<html><head><title>Intro</title></head><body><article>
<h1>Getting started</h1>
<p>This protocol connects applications to tools. It is open and well documented.
Clients and servers exchange simple messages. You can start with a small example today.</p>
<pre><code>x = 1</code></pre>
</article></body></html>"""
EMPTY = "<html><body><script>app()</script></body></html>"


class TestToMarkdown(unittest.TestCase):
    def test_markdown_has_header_and_code(self):
        out = sw.to_markdown(HTML, "https://example.com/a", date(2026, 10, 25))
        self.assertTrue(out.startswith(
            "<!-- source: https://example.com/a -->\n<!-- retrieved: 2026-10-25 -->\n\n"))
        self.assertIn("x = 1", out)

    def test_empty_page_raises(self):
        with self.assertRaises(ValueError):
            sw.to_markdown(EMPTY, "https://example.com/a", date(2026, 10, 25))


class TestWrite(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_write_creates_topic_dir(self):
        p = sw.write_snapshot(self.root, "mcp", "intro", "hello")
        self.assertEqual(p, self.root / "resources/web/mcp/intro.md")
        self.assertEqual(p.read_text(encoding="utf-8"), "hello")

    def test_existing_snapshot_not_overwritten(self):
        p = sw.write_snapshot(self.root, "mcp", "intro", "old")
        with self.assertRaises(FileExistsError):
            sw.write_snapshot(self.root, "mcp", "intro", "new")
        self.assertEqual(p.read_text(encoding="utf-8"), "old")

    def test_refresh_overwrites(self):
        p = sw.write_snapshot(self.root, "mcp", "intro", "old")
        sw.write_snapshot(self.root, "mcp", "intro", "new", refresh=True)
        self.assertEqual(p.read_text(encoding="utf-8"), "new")


class TestMain(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        old = os.environ.get("COLLEGE_ROOT")
        os.environ["COLLEGE_ROOT"] = str(self.root)
        self.addCleanup(lambda: os.environ.__setitem__("COLLEGE_ROOT", old)
                        if old is not None else os.environ.pop("COLLEGE_ROOT", None))

    def run_main(self, argv, fetch):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = sw.main(argv, fetch=fetch)
        return code, err.getvalue()

    def files(self):
        return [p for p in (self.root / "resources").rglob("*") if p.is_file()]

    def test_success(self):
        code, _ = self.run_main(["https://x.org/a", "mcp", "intro"], lambda u: HTML)
        self.assertEqual(code, 0)
        self.assertEqual(len(self.files()), 1)

    def test_empty_page_writes_nothing(self):
        code, err = self.run_main(["https://x.org/a", "mcp", "intro"], lambda u: EMPTY)
        self.assertEqual(code, 2)
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertEqual(self.files(), [])

    def test_fetch_failure(self):
        code, _ = self.run_main(["https://x.org/a", "mcp", "intro"], lambda u: None)
        self.assertEqual(code, 2)

        def boom(u):
            raise OSError("down")
        code, _ = self.run_main(["https://x.org/a", "mcp", "intro"], boom)
        self.assertEqual(code, 2)
        self.assertEqual(self.files(), [])

    def test_existing_file_returns_2_and_refresh_works(self):
        args = ["https://x.org/a", "mcp", "intro"]
        self.run_main(args, lambda u: HTML)
        target = next(iter(self.files()))
        target.write_text("kept", encoding="utf-8")
        code, _ = self.run_main(args, lambda u: HTML)
        self.assertEqual(code, 2)
        self.assertEqual(target.read_text(encoding="utf-8"), "kept")
        code, _ = self.run_main(args + ["--refresh"], lambda u: HTML)
        self.assertEqual(code, 0)

    def test_rejects_path_like_names(self):
        for topic, name in (("mcp", "../x"), ("../mcp", "x"), ("mcp", "A b"), ("", "x")):
            code, _ = self.run_main(["https://x.org/a", topic, name], lambda u: HTML)
            self.assertEqual(code, 2)
        self.assertEqual(self.files(), [])
        self.assertFalse((self.root / "x.md").exists())
        self.assertFalse((self.root / "resources" / "x.md").exists())

    def test_rejects_urls_that_break_the_header(self):
        for url in ("https://x.org/a b", "https://x.org/a-->b", "https://x.org/\na"):
            code, _ = self.run_main([url, "mcp", "intro"], lambda u: HTML)
            self.assertEqual(code, 2, url)
        self.assertEqual(self.files(), [])

    def test_fetch_error_is_one_line(self):
        def boom(u):
            raise OSError("down\nsecond line\n  third")
        code, err = self.run_main(["https://x.org/a", "mcp", "intro"], boom)
        self.assertEqual(code, 2)
        self.assertEqual(len(err.strip().splitlines()), 1)

    def test_write_snapshot_rejects_path_like_names(self):
        with self.assertRaises(ValueError):
            sw.write_snapshot(self.root, "mcp", "../x", "c")


if __name__ == "__main__":
    unittest.main()
