#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


INDEX_NOTE_NAME = "🧠 深度学习课程总索引.md"
IMAGE_EMBED_RE = re.compile(r"!\[\[([^|\]]+)(?:\|([^\]]+))?\]\]")
WIKI_ALIAS_RE = re.compile(r"(?<!!)\[\[([^|\]]+)\|([^\]]+)\]\]")


@dataclass(frozen=True)
class SyncResult:
    markdown_files: int
    asset_files: int


def output_path_for_markdown(relative_path: Path) -> Path:
    if relative_path.name == INDEX_NOTE_NAME:
        return relative_path.with_name("index.md")
    return relative_path


def sync_obsidian_dl_quartz(source: Path, dest: Path) -> SyncResult:
    source = source.expanduser().resolve()
    dest = dest.resolve()
    if not source.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source}")

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    markdown_count = 0
    referenced_assets: set[Path] = set()

    for source_md in sorted(source.glob("*.md")):
        if _should_skip_file(source_md):
            continue

        raw = source_md.read_text(encoding="utf-8")
        normalized = normalize_markdown_for_quartz(raw)
        output = dest / output_path_for_markdown(source_md.relative_to(source))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(normalized, encoding="utf-8")
        markdown_count += 1
        referenced_assets.update(extract_embedded_assets(normalized))

    asset_count = 0
    for asset in sorted(referenced_assets):
        source_asset = (source / asset).resolve()
        if not source_asset.is_file() or source not in source_asset.parents:
            continue
        if _should_skip_file(source_asset):
            continue

        output_asset = dest / asset
        output_asset.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_asset, output_asset)
        asset_count += 1

    return SyncResult(markdown_files=markdown_count, asset_files=asset_count)


def normalize_markdown_for_quartz(markdown: str) -> str:
    def replace_embed(match: re.Match[str]) -> str:
        path = _normalize_asset_path(Path(match.group(1).strip())).as_posix()
        size_or_alt = match.group(2)
        if size_or_alt:
            return f"![[{path}|{size_or_alt}]]"
        return f"![[{path}]]"

    markdown = IMAGE_EMBED_RE.sub(replace_embed, markdown)
    return WIKI_ALIAS_RE.sub(lambda match: f"[[{match.group(1)}\\|{match.group(2)}]]", markdown)


def extract_embedded_assets(markdown: str) -> set[Path]:
    assets: set[Path] = set()
    for match in IMAGE_EMBED_RE.finditer(markdown):
        path = _normalize_asset_path(Path(match.group(1).strip()))
        if path.parts and not path.is_absolute() and _is_asset(path):
            assets.add(path)
    return assets


def _normalize_asset_path(path: Path) -> Path:
    if len(path.parts) >= 2 and path.parts[0] == "DL" and path.parts[1] == "images":
        return Path(*path.parts[1:])
    return path


def _should_skip_file(path: Path) -> bool:
    name = path.name
    if name == ".DS_Store" or name.startswith("._"):
        return True
    if ".bak" in name or "bak-before" in name:
        return True
    return False


def _is_asset(path: Path) -> bool:
    return path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync raw Obsidian DL notes into Quartz content.")
    parser.add_argument("--source", type=Path, default=Path("/Users/gaia/Obsidian/zichen/DL"))
    parser.add_argument("--dest", type=Path, default=Path("quartz-dl/content"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = sync_obsidian_dl_quartz(args.source, args.dest)
    print(f"Synced {result.markdown_files} markdown files and {result.asset_files} referenced assets.")


if __name__ == "__main__":
    main()
