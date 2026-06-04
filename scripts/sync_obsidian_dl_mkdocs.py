#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


INDEX_NOTE_NAME = "🧠 深度学习课程总索引.md"
IMAGE_EMBED_RE = re.compile(r"!\[\[([^|\]]+)(?:\|([^\]]+))?\]\]")
WIKI_LINK_RE = re.compile(r"(?<!!)\[\[([^|\]]+)(?:\|([^\]]+))?\]\]")
CALLOUT_RE = re.compile(r"^>\s*\[!([A-Za-z-]+)\]\s*(.*)$")

CALLOUT_TYPES = {
    "abstract": "abstract",
    "bug": "bug",
    "check": "success",
    "danger": "danger",
    "error": "failure",
    "example": "example",
    "fail": "failure",
    "failure": "failure",
    "info": "info",
    "important": "note",
    "note": "note",
    "proof": "note",
    "question": "question",
    "quote": "quote",
    "summary": "abstract",
    "success": "success",
    "tip": "tip",
    "tips": "tip",
    "warning": "warning",
}


@dataclass(frozen=True)
class SyncResult:
    markdown_files: int
    asset_files: int


def output_path_for_markdown(source_md: Path) -> Path:
    if source_md.name == INDEX_NOTE_NAME:
        return Path("index.md")

    match = re.fullmatch(r"第(\d+)章\.md", source_md.name)
    if match:
        return Path(f"chapter-{int(match.group(1)):02d}.md")

    return source_md.with_suffix(".md").name


def build_note_map(source: Path) -> dict[str, str]:
    note_map: dict[str, str] = {}
    for source_md in source.glob("*.md"):
        if should_skip_file(source_md):
            continue

        output = output_path_for_markdown(source_md).as_posix()
        stem = source_md.stem
        note_map[stem] = output
        if source_md.name == INDEX_NOTE_NAME:
            note_map["深度学习课程总索引"] = output
            note_map["课程地图"] = output
            note_map["深度学习目录"] = output
    return note_map


def sync_obsidian_dl_mkdocs(source: Path, dest: Path) -> SyncResult:
    source = source.expanduser().resolve()
    dest = dest.resolve()
    if not source.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source}")

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    note_map = build_note_map(source)
    markdown_count = 0
    referenced_assets: set[Path] = set()

    for source_md in sorted(source.glob("*.md"), key=sort_key):
        if should_skip_file(source_md):
            continue

        raw = source_md.read_text(encoding="utf-8")
        normalized = normalize_markdown(raw, note_map)
        output = dest / output_path_for_markdown(source_md)
        output.write_text(normalized, encoding="utf-8")
        markdown_count += 1
        referenced_assets.update(extract_assets(raw))

    asset_count = 0
    for asset in sorted(referenced_assets):
        source_asset = (source / asset).resolve()
        if not source_asset.is_file() or source not in source_asset.parents:
            continue
        if should_skip_file(source_asset):
            continue

        output_asset = dest / asset
        output_asset.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_asset, output_asset)
        asset_count += 1

    return SyncResult(markdown_files=markdown_count, asset_files=asset_count)


def normalize_markdown(markdown: str, note_map: dict[str, str]) -> str:
    markdown = strip_time_frontmatter(markdown)
    markdown = normalize_callouts(markdown)
    markdown = IMAGE_EMBED_RE.sub(replace_image_embed, markdown)
    markdown = WIKI_LINK_RE.sub(lambda match: replace_wiki_link(match, note_map), markdown)
    return markdown.rstrip() + "\n"


def strip_time_frontmatter(markdown: str) -> str:
    if not markdown.startswith("---"):
        return markdown

    parts = markdown.split("---", 2)
    if len(parts) < 3:
        return markdown

    frontmatter = []
    for line in parts[1].splitlines():
        if line.strip().startswith(("created:", "modified:")):
            continue
        frontmatter.append(line)
    return "---" + "\n".join(frontmatter).rstrip() + "\n---" + parts[2]


def normalize_callouts(markdown: str) -> str:
    output: list[str] = []
    in_callout = False

    for line in markdown.splitlines():
        match = CALLOUT_RE.match(line)
        if match:
            kind = CALLOUT_TYPES.get(match.group(1).strip().lower(), "note")
            title = match.group(2).strip()
            output.append(f'!!! {kind} "{title}"' if title else f"!!! {kind}")
            in_callout = True
            continue

        if in_callout and line.startswith(">"):
            content = line[1:]
            if content.startswith(" "):
                content = content[1:]
            output.append(f"    {content}")
            continue

        in_callout = False
        output.append(line)

    return "\n".join(output)


def replace_image_embed(match: re.Match[str]) -> str:
    raw_path = normalize_asset_path(Path(match.group(1).strip()))
    alt = raw_path.stem
    return f"![{alt}]({raw_path.as_posix()})"


def replace_wiki_link(match: re.Match[str], note_map: dict[str, str]) -> str:
    target = match.group(1).strip()
    label = (match.group(2) or target).strip()
    note_name, _, heading = target.partition("#")
    href = note_map.get(note_name)

    if not href:
        return label

    return f"[{label}]({href})"


def extract_assets(markdown: str) -> set[Path]:
    assets: set[Path] = set()
    for match in IMAGE_EMBED_RE.finditer(markdown):
        path = normalize_asset_path(Path(match.group(1).strip()))
        if path.parts and not path.is_absolute() and is_asset(path):
            assets.add(path)
    return assets


def normalize_asset_path(path: Path) -> Path:
    if len(path.parts) >= 2 and path.parts[0] == "DL" and path.parts[1] == "images":
        return Path(*path.parts[1:])
    return path


def sort_key(path: Path) -> tuple[int, str]:
    if path.name == INDEX_NOTE_NAME:
        return (0, path.name)
    match = re.fullmatch(r"第(\d+)章\.md", path.name)
    if match:
        return (int(match.group(1)), path.name)
    return (999, path.name)


def should_skip_file(path: Path) -> bool:
    name = path.name
    if name == ".DS_Store" or name.startswith("._"):
        return True
    if ".bak" in name or "bak-before" in name:
        return True
    return False


def is_asset(path: Path) -> bool:
    return path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync raw Obsidian DL notes into MkDocs content.")
    parser.add_argument("--source", type=Path, default=Path("/Users/gaia/Obsidian/zichen/DL"))
    parser.add_argument("--dest", type=Path, default=Path("docs/deep-learning"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = sync_obsidian_dl_mkdocs(args.source, args.dest)
    print(f"Synced {result.markdown_files} markdown files and {result.asset_files} referenced assets.")


if __name__ == "__main__":
    main()
