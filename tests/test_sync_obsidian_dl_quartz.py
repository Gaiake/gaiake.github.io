import tempfile
import unittest
from pathlib import Path

from scripts.sync_obsidian_dl_quartz import (
    extract_embedded_assets,
    normalize_markdown_for_quartz,
    output_path_for_markdown,
    sync_obsidian_dl_quartz,
)


class SyncObsidianDlQuartzTests(unittest.TestCase):
    def test_total_index_becomes_quartz_homepage(self):
        path = output_path_for_markdown(Path("🧠 深度学习课程总索引.md"))

        self.assertEqual(path, Path("index.md"))

    def test_wiki_links_are_preserved_for_quartz_with_safe_alias_separator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            dest = root / "dest"
            source.mkdir()
            (source / "第2章.md").write_text("[[第3章|下一章]]\n![[images/demo.png]]", encoding="utf-8")
            (source / "images").mkdir()
            (source / "images" / "demo.png").write_bytes(b"png")

            sync_obsidian_dl_quartz(source, dest)

            self.assertEqual(
                (dest / "第2章.md").read_text(encoding="utf-8"),
                "[[第3章\\|下一章]]\n![[images/demo.png]]",
            )

    def test_only_root_markdown_and_referenced_images_are_synced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            dest = root / "dest"
            (source / "images").mkdir(parents=True)
            (source / "mineru").mkdir()
            (source / "🧠 深度学习课程总索引.md").write_text("![[DL/images/used.png]]", encoding="utf-8")
            (source / "第2章.md").write_text("[[第3章]]", encoding="utf-8")
            (source / "第2章.md.bak-before-math-fix").write_text("old", encoding="utf-8")
            (source / "images" / "used.png").write_bytes(b"png")
            (source / "images" / "unused.png").write_bytes(b"png")
            (source / "mineru" / "courseware.pdf").write_bytes(b"pdf")

            result = sync_obsidian_dl_quartz(source, dest)

            self.assertEqual(result.markdown_files, 2)
            self.assertEqual(result.asset_files, 1)
            self.assertTrue((dest / "index.md").exists())
            self.assertTrue((dest / "第2章.md").exists())
            self.assertTrue((dest / "images" / "used.png").exists())
            self.assertFalse((dest / "images" / "unused.png").exists())
            self.assertFalse((dest / "mineru").exists())

    def test_extract_embedded_assets_normalizes_dl_image_prefix(self):
        assets = extract_embedded_assets("![[DL/images/a.png]]\n![[images/b.png]]")

        self.assertEqual(assets, {Path("images/a.png"), Path("images/b.png")})

    def test_wiki_alias_pipe_is_escaped_for_markdown_tables(self):
        markdown = "| 概念 | 章节 |\n|---|---|\n| 梯度下降 | [[第2章#七、深度学习泛化|§2.7]] |"

        normalized = normalize_markdown_for_quartz(markdown)

        self.assertIn("[[第2章#七、深度学习泛化\\|§2.7]]", normalized)


if __name__ == "__main__":
    unittest.main()
