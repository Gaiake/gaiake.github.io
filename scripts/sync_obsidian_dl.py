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


@dataclass(frozen=True)
class SyncResult:
    markdown_files: int
    asset_files: int


def is_publishable_file(path: Path) -> bool:
    name = path.name
    if name == ".DS_Store" or name.startswith("._"):
        return False
    if ".bak" in name or "bak-before" in name:
        return False
    return path.suffix.lower() in {".md", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def output_path_for_markdown(relative_path: Path) -> Path:
    if relative_path.name == INDEX_NOTE_NAME:
        return relative_path.with_name("index.md")
    return relative_path


def convert_obsidian_markdown(markdown: str) -> str:
    markdown = _convert_callouts(markdown)
    markdown = IMAGE_EMBED_RE.sub(_replace_image_embed, markdown)
    markdown = WIKI_LINK_RE.sub(_replace_wiki_link, markdown)
    return markdown


def sync_obsidian_dl(source: Path, dest: Path) -> SyncResult:
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
        relative = source_md.relative_to(source)
        if not is_publishable_file(relative):
            continue

        raw = source_md.read_text(encoding="utf-8")
        converted = convert_obsidian_markdown(raw)
        output = dest / output_path_for_markdown(relative)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(converted, encoding="utf-8")
        markdown_count += 1
        referenced_assets.update(_extract_embedded_assets(raw))

    asset_count = 0
    for asset in sorted(referenced_assets):
        source_asset = (source / asset).resolve()
        if not source_asset.is_file() or source not in source_asset.parents:
            continue
        if not is_publishable_file(asset):
            continue

        output_asset = dest / asset
        output_asset.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_asset, output_asset)
        asset_count += 1

    return SyncResult(markdown_files=markdown_count, asset_files=asset_count)


def _convert_callouts(markdown: str) -> str:
    lines = markdown.splitlines()
    converted: list[str] = []
    in_callout = False

    for line in lines:
        match = re.match(r"^>\s*\[!([A-Za-z-]+)\]\s*(.*)$", line)
        if match:
            callout_type = _callout_type(match.group(1))
            title = match.group(2).strip()
            if title:
                converted.append(f'!!! {callout_type} "{title}"')
            else:
                converted.append(f"!!! {callout_type}")
            in_callout = True
            continue

        if in_callout and line.startswith(">"):
            content = line[1:]
            if content.startswith(" "):
                content = content[1:]
            converted.append(f"    {content}" if content else "")
            continue

        in_callout = False
        converted.append(line)

    trailing_newline = "\n" if markdown.endswith("\n") else ""
    return "\n".join(converted) + trailing_newline


def _replace_image_embed(match: re.Match[str]) -> str:
    target = _normalize_asset_path(Path(match.group(1).strip())).as_posix()
    alt = (match.group(2) or "").strip()
    return f"![{alt}]({target})"


def _replace_wiki_link(match: re.Match[str]) -> str:
    target = match.group(1).strip()
    label = (match.group(2) or target).strip()
    return f"[{label}]({_wiki_target_to_markdown_href(target)})"


def _wiki_target_to_markdown_href(target: str) -> str:
    if target.startswith("#"):
        return target

    page, separator, anchor = target.partition("#")
    href = page
    if href and not Path(href).suffix:
        href = f"{href}.md"
    if separator:
        href = f"{href}#{anchor}"
    return href


def _extract_embedded_assets(markdown: str) -> set[Path]:
    assets: set[Path] = set()
    for match in IMAGE_EMBED_RE.finditer(markdown):
        target = match.group(1).strip()
        path = _normalize_asset_path(Path(target))
        if not path.is_absolute() and path.parts:
            assets.add(path)
    return assets


def _normalize_asset_path(path: Path) -> Path:
    if len(path.parts) >= 2 and path.parts[0] == "DL" and path.parts[1] == "images":
        return Path(*path.parts[1:])
    return path


def _callout_type(callout_type: str) -> str:
    normalized = callout_type.lower()
    aliases = {
        "abstract": "abstract",
        "summary": "abstract",
        "tldr": "abstract",
        "hint": "tip",
        "important": "tip",
        "attention": "warning",
        "caution": "warning",
        "error": "danger",
        "failure": "failure",
        "fail": "failure",
        "missing": "failure",
        "faq": "question",
        "help": "question",
        "todo": "note",
    }
    return aliases.get(normalized, normalized)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Obsidian DL notes into MkDocs docs/DL.")
    parser.add_argument("--source", type=Path, default=Path("/Users/gaia/Obsidian/zichen/DL"))
    parser.add_argument("--dest", type=Path, default=Path("docs/DL"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = sync_obsidian_dl(args.source, args.dest)
    print(f"Synced {result.markdown_files} markdown files and {result.asset_files} referenced assets.")


if __name__ == "__main__":
    main()
