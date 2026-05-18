#!/usr/bin/env python3
"""
One-shot migration from GitHub Wiki markdown to Starlight content collection.

Run once after Starlight scaffold is in place:
    python3 scripts/migrate-wiki.py

Operates on:
    src:  /home/chase/projects/stardust/_wiki-source/
    dst:  /home/chase/projects/stardust/stardust-site/src/content/docs/

Transformations applied:
    1. Filename mapping (Feature:-X.md -> features/x.md, etc.)
    2. Frontmatter injection (title pulled from first H1)
    3. Wiki link conversion: [[Page|Label]] -> [Label](/path/to/page/)
    4. Strip the original H1 (Starlight renders the frontmatter title)
    5. Skip _Sidebar.md / _Footer.md (sidebar is configured in astro.config.mjs)

This script is intentionally re-runnable. It overwrites destination files.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
WIKI_SRC = WORKSPACE / "_wiki-source"
DOCS_DST = WORKSPACE / "stardust-site" / "src" / "content" / "docs"

# Maps source wiki filename -> destination path relative to DOCS_DST.
# Pages that exist in the wiki but aren't migrated (e.g. _Sidebar) are omitted.
FILE_MAP: dict[str, str] = {
    # Top-level
    "Home.md": "index.mdx",
    "Comparison.md": "comparison.md",
    # Concepts
    "Shows,-Songs,-and-Patches.md": "concepts/shows-songs-patches.md",
    "Cascading-Settings.md": "concepts/cascading-settings.md",
    "Edit-Mode-vs-Live-Mode.md": "concepts/edit-vs-live.md",
    # Architecture
    "Architecture-Overview.md": "architecture/overview.md",
    "Architecture:-Tauri-Stack.md": "architecture/tauri-stack.md",
    # Features
    "Feature:-Plugin-Hosting.md": "features/plugin-hosting.md",
    "Feature:-Patch-Sequencing.md": "features/patch-sequencing.md",
    "Feature:-MIDI-Learn.md": "features/midi-learn.md",
    "Feature:-Device-Profiles.md": "features/device-profiles.md",
    "Feature:-Cue-System.md": "features/cue-system.md",
    "Feature:-Click-Track.md": "features/click-track.md",
    "Feature:-Show-Notes.md": "features/show-notes.md",
    "Feature:-Transpose.md": "features/transpose.md",
    "Feature:-Setlist-Mode.md": "features/setlist-mode.md",
    "Feature:-forScore-Integration.md": "features/forscore-integration.md",
    "Feature:-Hot-spare-Rig.md": "features/hot-spare-rig.md",
    "Feature:-Audio-I-O.md": "features/audio-io.md",
    "Feature:-Custom-Sampler.md": "features/custom-sampler.md",
    "Feature:-Community-Sharing.md": "features/community-sharing.md",
    "Feature:-Marketplace.md": "features/marketplace.md",
    "Feature:-AU-Hosting.md": "features/au-hosting.md",
    "Feature:-Mobile-Companion.md": "features/mobile-companion.md",
    "Feature:-Multi-keyboardist-Sync.md": "features/multi-keyboardist-sync.md",
    # Reliability
    "Reliability:-Latency-Budget.md": "reliability/latency-budget.md",
    "Reliability:-Plugin-Crash-Isolation.md": "reliability/plugin-crash-isolation.md",
    "Reliability:-Hot-Plug.md": "reliability/hot-plug.md",
    "Reliability:-Pre-Show-Validation.md": "reliability/pre-show-validation.md",
    "Reliability:-Performance-Lock.md": "reliability/performance-lock.md",
    "Reliability:-Voice-Tracking.md": "reliability/voice-tracking.md",
    # Roadmap
    "Roadmap.md": "roadmap/index.md",
    "v0.1-Foundations.md": "roadmap/v0-1-foundations.md",
    "v0.2-Core-Engine.md": "roadmap/v0-2-core-engine.md",
    "v0.3-Plugin-Sandboxing-+-CLAP.md": "roadmap/v0-3-plugin-sandboxing-clap.md",
    "v0.4-Data-Model-+-UI.md": "roadmap/v0-4-data-model-ui.md",
    "v0.5-MT-Features.md": "roadmap/v0-5-mt-features.md",
    "v1.0-Public-Release.md": "roadmap/v1-0-public-release.md",
    "v2.0-Post-1.0.md": "roadmap/v2-0-post-1-0.md",
}

# Maps a wiki page title (no path, no extension) to its Starlight URL path.
# Used to convert [[Wiki Link]] syntax. Anything not in this map becomes a
# bare label with a TODO comment so we can find dead links later.
WIKI_TITLE_TO_URL: dict[str, str] = {
    "Home": "/",
    "Comparison": "/comparison/",
    "Shows, Songs, and Patches": "/concepts/shows-songs-patches/",
    "Cascading Settings": "/concepts/cascading-settings/",
    "Edit Mode vs Live Mode": "/concepts/edit-vs-live/",
    "Architecture Overview": "/architecture/overview/",
    "Architecture: Tauri Stack": "/architecture/tauri-stack/",
    "Feature: Plugin Hosting": "/features/plugin-hosting/",
    "Feature: Patch Sequencing": "/features/patch-sequencing/",
    "Feature: MIDI Learn": "/features/midi-learn/",
    "Feature: Device Profiles": "/features/device-profiles/",
    "Feature: Cue System": "/features/cue-system/",
    "Feature: Click Track": "/features/click-track/",
    "Feature: Show Notes": "/features/show-notes/",
    "Feature: Transpose": "/features/transpose/",
    "Feature: Setlist Mode": "/features/setlist-mode/",
    "Feature: forScore Integration": "/features/forscore-integration/",
    "Feature: Hot-spare Rig": "/features/hot-spare-rig/",
    "Feature: Audio I/O": "/features/audio-io/",
    "Feature: Custom Sampler": "/features/custom-sampler/",
    "Feature: Community Sharing": "/features/community-sharing/",
    "Feature: Marketplace": "/features/marketplace/",
    "Feature: AU Hosting": "/features/au-hosting/",
    "Feature: Mobile Companion": "/features/mobile-companion/",
    "Feature: Multi-keyboardist Sync": "/features/multi-keyboardist-sync/",
    "Reliability: Latency Budget": "/reliability/latency-budget/",
    "Reliability: Plugin Crash Isolation": "/reliability/plugin-crash-isolation/",
    "Reliability: Hot-Plug": "/reliability/hot-plug/",
    "Reliability: Pre-Show Validation": "/reliability/pre-show-validation/",
    "Reliability: Performance Lock": "/reliability/performance-lock/",
    "Reliability: Voice Tracking": "/reliability/voice-tracking/",
    "Roadmap": "/roadmap/",
    "v0.1 Foundations": "/roadmap/v0-1-foundations/",
    "v0.2 Core Engine": "/roadmap/v0-2-core-engine/",
    "v0.3 Plugin Sandboxing + CLAP": "/roadmap/v0-3-plugin-sandboxing-clap/",
    "v0.4 Data Model + UI": "/roadmap/v0-4-data-model-ui/",
    "v0.5 MT Features": "/roadmap/v0-5-mt-features/",
    "v1.0 Public Release": "/roadmap/v1-0-public-release/",
    "v2.0 Post-1.0": "/roadmap/v2-0-post-1-0/",
}

# Wiki link patterns:
#   [[Target]]              -> [Target](url-of-target)
#   [[Target|Label]]        -> [Label](url-of-target)
#   [[Target\|Label]]       -> [Label](url-of-target)   (escaped form used inside markdown tables)
WIKI_LINK_RE = re.compile(r"\[\[([^\]|\\]+)(?:\\?\|([^\]]+))?\]\]")

H1_RE = re.compile(r"^# (.+)$", re.MULTILINE)


def convert_wiki_links(body: str) -> tuple[str, list[str]]:
    """Replace [[...]] with standard markdown links. Returns (converted, dead_links)."""
    dead: list[str] = []

    def repl(match: re.Match[str]) -> str:
        target = match.group(1).strip()
        label = (match.group(2) or target).strip()
        url = WIKI_TITLE_TO_URL.get(target)
        if url is None:
            dead.append(target)
            # Render as bold text + HTML comment so the broken ref is visible
            # in the rendered site and grep-able in source.
            return f"**{label}** <!-- TODO: dead wiki link to '{target}' -->"
        return f"[{label}]({url})"

    return WIKI_LINK_RE.sub(repl, body), dead


def extract_title_and_strip_h1(body: str) -> tuple[str, str]:
    """Pull the first H1 as the page title; strip it from the body."""
    m = H1_RE.search(body)
    if not m:
        return "Untitled", body
    title = m.group(1).strip()
    # Remove just that H1 line (and an optional following blank line)
    start, end = m.span()
    rest = body[end:]
    rest = rest.lstrip("\n")
    return title, body[:start] + rest


def description_for(title: str, body: str) -> str:
    """First non-empty, non-frontmatter, non-heading paragraph, capped at 160 chars."""
    for raw in body.split("\n\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#") or line.startswith(">"):
            continue
        # Strip markdown emphasis and inline code for the description
        line = re.sub(r"[*_`]", "", line)
        line = re.sub(r"<!--.*?-->", "", line, flags=re.DOTALL).strip()
        if not line:
            continue
        if len(line) > 160:
            line = line[:157].rstrip() + "..."
        return line
    return f"{title} — Stardust documentation."


def build_frontmatter(title: str, description: str, source: str) -> str:
    # Escape double quotes in YAML values
    def yq(s: str) -> str:
        return s.replace('"', '\\"')

    return (
        "---\n"
        f'title: "{yq(title)}"\n'
        f'description: "{yq(description)}"\n'
        "---\n\n"
    )


def migrate_file(src_filename: str, dst_relpath: str) -> list[str]:
    src_path = WIKI_SRC / src_filename
    dst_path = DOCS_DST / dst_relpath
    if not src_path.exists():
        print(f"  ! missing source: {src_filename}", file=sys.stderr)
        return []

    raw = src_path.read_text(encoding="utf-8")
    title, body = extract_title_and_strip_h1(raw)
    body, dead = convert_wiki_links(body)
    description = description_for(title, body)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(build_frontmatter(title, description, src_filename) + body, encoding="utf-8")
    return dead


def main() -> int:
    if not WIKI_SRC.exists():
        print(f"wiki source not found at {WIKI_SRC}", file=sys.stderr)
        return 1

    all_dead: dict[str, list[str]] = {}
    for src, dst in FILE_MAP.items():
        dead = migrate_file(src, dst)
        if dead:
            all_dead[src] = dead
        print(f"  → {src:50s}  ->  {dst}")

    # Report any wiki files not in the map (so we don't silently drop new pages).
    mapped = set(FILE_MAP)
    found = {p.name for p in WIKI_SRC.glob("*.md") if not p.name.startswith("_")}
    unmapped = found - mapped
    if unmapped:
        print("\n! Wiki files NOT migrated (add to FILE_MAP if intentional):")
        for name in sorted(unmapped):
            print(f"    {name}")

    if all_dead:
        print("\n! Dead [[wiki links]] (rendered as bold text + TODO comment):")
        for src, targets in all_dead.items():
            for t in sorted(set(targets)):
                print(f"    {src} -> [[{t}]]")

    print(f"\nMigrated {len(FILE_MAP)} files to {DOCS_DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
