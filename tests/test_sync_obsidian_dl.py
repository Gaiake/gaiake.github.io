import tempfile
import unittest
from pathlib import Path

from scripts.sync_obsidian_dl import (
    convert_obsidian_markdown,
    is_publishable_file,
    output_path_for_markdown,
    sync_obsidian_dl,
)


class SyncObsidianDlTests(unittest.TestCase):
    def test_convert_wiki_links_and_embedded_images(self):
        source = "1. [[第2章#一、什么是机器学习|什么是机器学习]]\n![[DL/images/demo 图.png]]"

        converted = convert_obsidian_markdown(source)

        self.assertIn("[什么是机器学习](第2章.md#一、什么是机器学习)", converted)
        self.assertIn("![](images/demo 图.png)", converted)

    def test_convert_plain_wiki_link(self):
        converted = convert_obsidian_markdown("[[第10章]]")

        self.assertEqual(converted, "[第10章](第10章.md)")

    def test_filters_backups_and_macos_metadata(self):
        self.assertFalse(is_publishable_file(Path("第2章.md.bak-before-math-fix")))
        self.assertFalse(is_publishable_file(Path(".DS_Store")))
        self.assertTrue(is_publishable_file(Path("images/figure.png")))
        self.assertTrue(is_publishable_file(Path("第2章.md")))

    def test_total_index_becomes_section_index(self):
        path = output_path_for_markdown(Path("🧠 深度学习课程总索引.md"))

        self.assertEqual(path, Path("index.md"))

    def test_sync_copies_assets_and_converts_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            dest = root / "dest"
            (source / "images").mkdir(parents=True)
            (source / "mineru").mkdir(parents=True)
            (source / "🧠 深度学习课程总索引.md").write_text("[[第2章]]", encoding="utf-8")
            (source / "第2章.md").write_text("![[images/demo.png]]", encoding="utf-8")
            (source / "第2章.md.bak-before-math-fix").write_text("old", encoding="utf-8")
            (source / ".DS_Store").write_text("metadata", encoding="utf-8")
            (source / "images" / "demo.png").write_bytes(b"png")
            (source / "images" / "unused.png").write_bytes(b"png")
            (source / "mineru" / "courseware.pdf").write_bytes(b"pdf")

            result = sync_obsidian_dl(source, dest)

            self.assertEqual(result.markdown_files, 2)
            self.assertEqual(result.asset_files, 1)
            self.assertEqual((dest / "index.md").read_text(encoding="utf-8"), "[第2章](第2章.md)")
            self.assertEqual((dest / "第2章.md").read_text(encoding="utf-8"), "![](images/demo.png)")
            self.assertTrue((dest / "images" / "demo.png").exists())
            self.assertFalse((dest / "images" / "unused.png").exists())
            self.assertFalse((dest / "mineru" / "courseware.pdf").exists())
            self.assertFalse((dest / "第2章.md.bak-before-math-fix").exists())


if __name__ == "__main__":
    unittest.main()
