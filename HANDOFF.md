# Stardust — work in progress handoff

**Last updated:** 2026-05-27 (post doc-rewrite v2 + kanban deepening; v0.6.0 engine completeness is the next chunk)
**Purpose:** Read this first in any new chat that's resuming Stardust work, especially when switching machines. Bridges what `git log` can't show: where we are in the roadmap, what's in flight, what decisions are baked in.

> ## ⚠️ REQUIRED READING for any future chat resuming Stardust work
>
> **Read `PLANNING.md` (workspace root) end-to-end before doing any docs / kanban / spec work.**
>
> HANDOFF.md (this file) carries the decisions; PLANNING.md carries the reasoning, depth, and alternatives considered. Feature pages, ADRs, and per-version refinement sessions write *from* PLANNING.md. If a planning decision feels under-specified in HANDOFF, the answer is in PLANNING.

---

## TL;DR for a new chat

- Current shipping state: **v0.5.0** (multi-plugin chain hosting via engine_graph Plan)
- **Just shipped (this chat):** Deep rewrite of all feature pages with full PLANNING.md depth (patch-library data model, balance tool LUFS/velocity/attack engineering, click track data model + SMF roundtrip, backing tracks workflow, engine monitor field table, conductor cam analog-vs-software analysis, Pit Mixer hardware compat, extension API WASM rationale, new show wizard 6-step spec, button/switch spec, show control vision, latency budget Part 14 landscape, marketplace tiers + cost, infrastructure choices); converted 19 existing feature pages from .md → .mdx with proper `<Badge>` status components; renamed project board "Stardust roadmap" → "Stardust Pit"; **filed the full per-version backlog as kanban issues — 97 issues in stardust-pit + 1 in stardust-core, 98 total on the board**, each milestone-tagged with detailed acceptance criteria. Added "🔍 Under refinement" status column + `needs-refinement` label for features explicitly requiring a per-version spec session before dev pickup (widget catalog, click editor, balance tool, song transport state machine, vamp interplay, MIDI recording, extension API).
- **Next chunk of work:** v0.6.0 refinement session, then implementation. See the [Pit roadmap v0.6.0 entry](https://stardustmt.github.io/docs/pit/roadmap/#v060--engine-completeness) — exit criteria are explicit. Issues #1–#11 + #18 have detailed acceptance criteria; pick any.
- All decisions from the prior planning consolidation are captured below — do not re-litigate

---

## Versioning (semver — was vX.Y-letter)

| Tag | Old tag | What shipped |
|---|---|---|
| v0.1.0 | v0.1 + v0.2 | Tauri 2 + React 19 + Vite + Storybook + bun scaffold. Three read-only bridge commands. Diagnostic 3-card view. |
| v0.1.1 | v0.3 | Patch editor wired in app shell. Client-side state only. |
| v0.2.0 | v0.4 | First live engine. Dedicated thread, `!Send` CLAP host, `engine_start/stop/status`, EnginePanel. |
| v0.2.1 | v0.5 | Patch document load/save bridge + macOS launch fix (DiscoveryLock, cpal 0.17 bump). |
| v0.3.0 | v0.6 | Show document load/save end-to-end. Zustand store, controlled PatchEditor, ShowToolbar, `.stardustshow`. ADR-0005. |
| v0.4.0 | v0.7 | Engine driven by Patch + on-screen MIDI playback. `engine_start_from_patch`, real plugin metadata in node config. |
| v0.4.1 | v0.8a | Always-on engine reactive to current patch. Start/Stop buttons removed. |
| **v0.5.0** | v0.8b | Multi-plugin chain hosting via `engine_graph` Plan. Native 3-band EQ + transpose + mix nodes. ADR-0006 Accepted. **← current** |

All tags exist on both repos (`stardust-pit` and `stardust-core` where applicable) — push them to GitHub:
- stardust-pit: v0.1.0–v0.5.0 (8 tags)
- stardust-core: v0.2.0, v0.2.1, v0.3.0, v0.5.0 (4 tags — no aligned commits for v0.1.x or v0.4.x)

---

## Roadmap to v1.0 (canonical source: docs site)

The canonical roadmap is now at https://stardustmt.github.io/docs/pit/roadmap/ — written as a Starlight MDX page with per-version cards, exit criteria, tech-debt log, and v1.x / v2.0+ backlogs.

| Ver | Theme | Status | Size |
|---|---|---|---|
| v0.5.0 | Multi-plugin chain hosting | ✅ shipped | — |
| v0.6.0 | Engine completeness | 📋 next | ~2 wk |
| v0.7.0 | Plugin sandboxing (out-of-process) | 📋 | ~6 wk |
| v0.8.0 | Transport + MD essentials | 📋 | ~4 wk |
| v0.9.0 | Three-mode shell + splash + wizard + settings | 📋 | ~3 wk |
| v0.10.0 | Library + reuse + drawing + Pit Mixer | 📋 | ~5 wk |
| v0.11.0 | Perform mode + widgets + conductor cam | 📋 | ~4 wk |
| v0.12.0 | Click track editor + balance tool | 📋 | ~4 wk |
| v0.13.0 | Backing tracks + bundle file format | 📋 | ~5 wk |
| v0.14.0 | Native SFZ player + built-in piano | 📋 | ~2 wk |
| v0.15.0 | Polish + extension API + release CI | 📋 | ~4 wk |
| v1.0.0 | Public release | 📋 | ~2 wk beta |

**Total: ~46 weeks engineering / 11–15 months calendar.** No hard deadline.

For per-version scope + exit criteria, see the roadmap doc (link above). The roadmap doc is the source of truth; this table is the at-a-glance.

---

## Project board (org-level)

**StardustMT org project: "Stardust roadmap"** — https://github.com/orgs/StardustMT/projects/1

- **Columns**: 📋 Planned · 🔨 In Progress · 🧪 Testing · 👀 Review · ✅ Done · 🧊 Deferred
- **Milestones** in stardust-pit and stardust-core: v0.6.0 through v1.0.0
- **Labels** in both repos:
  - `screen:setup`, `screen:program`, `screen:perform`, `screen:splash`, `screen:floating`
  - `engine:audio`, `engine:midi`, `engine:plugin`, `engine:transport`, `engine:graph`
  - `docs`, `tech-debt`, `extension`, `infrastructure`
- **Seeded issues**: 11 v0.6.0-scoped issues + 5 tech-debt issues in stardust-pit, 1 cross-repo issue in stardust-core (scan-cache backing). 17 total on the board.
- **Issue seeding policy**: file v0.6.0+ issues *during each version's refinement session*. v0.7.0–v1.0.0 milestones exist; no issues filed yet for those versions.

---

## Architectural decisions baked in (don't re-litigate)

These are locked unless you explicitly reopen. Most have multi-conversation rationale behind them.

### Engine + audio
- **CLAP only for plugins** in v1.0; VST3 + AU as v1.x or v2.0
- **First-party Rust SDKs for VST3 + AU** are v2.0+ initiatives
- **Plugin sandboxing (out-of-process)** is a hard requirement — currently violated, scheduled v0.7.0 ([ADR-0002](docs/adr/0002-out-of-process-plugin-sandboxing.md))
- **Realtime paths allocation-free** (CLAUDE.md rule)
- **Engine consumes whole patch graph** — Plan::build → topo-sort → allocation-free Plan::process per block ([ADR-0006](docs/adr/0006-engine-graph-walker.md), Accepted)
- **Audio I/O on Windows**: WASAPI Exclusive default, ASIO surfaced when available, WASAPI Shared as fallback. macOS uses CoreAudio. Linux uses ALSA → JACK → PipeWire fallback. Support separate input/output devices (no ASIO single-device limit).

### Data model
- **All patches are references to library entries** (no inline-vs-ref dichotomy). Library entries have `scope: "show" | "global"`. Show file bundles snapshots of global entries on share.
- **Orphan handling**: deleted library entry → refs freeze the last graph as `orphan.snapshot`, banner + reattach/save-new/keep options
- **Patch reference overrides**: Basic (name, notes, tempo, transpose, trim, color, tags) + Advanced (MIDI channel offset, bus routing, plugin params, FX bypass, on-enter/exit triggers, custom CSS). Tempo override = Advanced.
- **Graph edits to shared patches** trigger merge UI with per-instance update/keep/three-way-merge dialog
- **Show metadata** structured as Production (this run) / Source (the work) / Distribution (sharing) — Source includes Productions list for revivals
- **Schema-versioned everything** per ADR-0003
- **All shipping data formats use semver** with explicit migration paths

### File format
- **`.stardustshow/` bundle** (folder with extension) — not single JSON. Contains `show.json`, `libraries/`, `assets/audio`, `assets/images`, `assets/samples`, `thumbnails/`. Opt-in zip export for sharing.
- Migration scheduled v0.13.0 (when backing tracks force the issue anyway)

### UI shell
- **Three modes: Setup / Program / Perform** (see [concept doc](https://stardustmt.github.io/docs/pit/concepts/setup-program-perform/))
- **Settings is a floating Window**, not a fourth mode
- **Plugin GUIs are floating Windows**, per-plugin
- **New Show wizard is a Modal**
- **Splash is pre-shell screen** (separate from the three modes)
- **Native menu bar** for File/Edit/View/Window/Help — mode switches are NOT in the menu bar
- **Song page renders in patch-canvas area** when a song is selected in outline (tabs: Settings / Click / Backing / Patches)
- **No hard-forced Live widgets** — user places everything; layout templates seed sensible starting layouts

### Sync + ecosystem (post-v1.0)
- **CRDT (Automerge) for sync + collaboration** — works offline, P2P-capable, server-optional
- **Local-first non-negotiable** — every cloud feature is additive, never gates the app
- **MoR for payments**: Lemon Squeezy or Polar.sh (do not build payment infra from scratch)
- **Self-hostable marketplace server** — open source aligns with AGPL ethos
- **No mandatory accounts ever** — anonymous downloads stay available
- **Cloud provider stack** (provisional): Cloudflare R2 + Fly.io + Neon Postgres + Clerk/Ory + Plausible + GlitchTip. Architecture is provider-agnostic; can swap to AWS/GCP if needed.

### Extension API
- **Hybrid TypeScript + WASM** for v0.15.0 — TS for UI/importers/commands, WASM for compute-heavy
- **Realtime WASM extensions** are v2.0+
- **Sandboxed by default** — no native module plugins
- **Stream Deck support** ships as bundled example extension

### Tooling
- **Bun, not npm** for stardust-pit (uses `@tauri-apps/cli` JS, not `cargo-tauri`)
- **GitHub Projects v2** for kanban tracking — https://github.com/orgs/StardustMT/projects/1
- **GitHub Actions** for CI (basic PR CI in v0.6.0, soak tests in v0.7.0, visual regression in v0.10.0, release pipeline in v0.15.0)
- **No `Co-Authored-By: Claude`** footer in commits. Ever.
- **Storybook stays as design-iteration surface** — real screens in `src/src/screens/*.tsx`, `.stories.tsx` wraps with fixture data
- **Placeholder icons** in stardust-pit/src-tauri/icons/ — don't touch until real branding

### Crate organization
- **Stay flat workspace** (not nested workspaces) for now — group by naming convention (`stardust-audio-*` etc.). Revisit if past ~15 crates.

### What's NOT in v1.0
- AU plugin hosting (tentatively v1.0 if scope allows; defer otherwise)
- Multi-channel audio input via Dante/AVB (USB multitrack only)
- Cloud sync, marketplace, collaboration (all v2.0+)
- Sheets app (post-Pit-v1)
- Piano roll editor (v1.x or v2.0)
- VST3 host (v1.x with C++ shim)
- Realtime WASM extensions (v2.0+)
- IP/RTSP/NDI conductor cam (v2.0+)
- DMX / lighting (revisit if Show Control unlocks demand)
- Velocity-curve balance (v0.12.0 does velocity-normalized; curve in v1.x)

---

## What's in flight right now

**Nothing**. Doc rewrite + kanban setup is done. The next chunk is the v0.6.0 refinement session, then implementation.

For loose ends carried from v0.5.0, see [the roadmap's Tech Debt table](https://stardustmt.github.io/docs/pit/roadmap/#tech-debt) — every item has an explicit cleanup-target version.

---

## Next chat — bootstrap prompt

Paste this into a fresh `/clear`-ed session:

> Resuming Stardust work — v0.6.0 engine completeness. **Read `HANDOFF.md` and `PLANNING.md` (workspace root) first** — PLANNING.md is required reading for any docs / kanban / spec work; it carries the reasoning behind every locked-in decision. Then walk through the v0.6.0 refinement session per CLAUDE.md (pre-feature refinement). v0.6.0 scope is on the [Pit roadmap](https://stardustmt.github.io/docs/pit/roadmap/#v060--engine-completeness) and as seeded issues on https://github.com/orgs/StardustMT/projects/1. Surface ambiguities before writing code.

---

## Resuming on a different machine

```bash
# 1. Pull every repo
cd ~/projects/stardust && git pull
cd stardust-pit && git pull --tags
cd ../stardust-core && git pull --tags
cd ../stardustmt.github.io && git pull

# 2. JS deps (once per machine / after package.json changes)
cd ../stardust-pit && bun install
cd ../stardustmt.github.io && bun install

# 3. Verify
bun ui:build-storybook
cd ../stardust-core && cargo check --workspace

# 4. Run
cd ../stardust-pit && bun dev
```

Then open a fresh Claude Code chat in the meta-workspace and use the bootstrap prompt above.

---

## Working efficiently with Claude on this project

- **Start a fresh chat per chunk of work** — long threads dominate cost
- **End a chat by asking me to update HANDOFF** before `/clear`
- **CLAUDE.md's terseness directives** keep prose minimal — don't remove them
- **Be specific** — "Add X to the engine" is cheaper than "what should we do next?"
- **Refinement sessions are explicit** per CLAUDE.md — at the start of each version, walk through the spec and lock in details before code

---

## Recent commits worth knowing

- `stardust-workspace` (this chat) — ADR-0006 → Accepted, ADR-0002 v0.7.0 note, HANDOFF rewrite
- `stardustmt.github.io` (this chat) — full doc rewrite: roadmap MDX, setup-program-perform concept, 11 new feature pages, 3 ecosystem docs, screens inventory, custom Header, 19-page status sweep
- `stardust-pit` `20bfeaa` — v0.5.0: multi-plugin chain hosting via `engine_graph` Plan
- `stardust-core` `8eeff2f` — v0.5.0: 3-band stereo EQ + StereoChannel re-export
- `stardust-pit` `d88b8d9` — v0.4.1: always-on engine
- `stardust-pit` `4e42c7d` — v0.4.0: engine consumes Patch + on-screen MIDI
- `stardust-pit` `a933d33` — v0.3.0: Open/Save Show end-to-end
- `stardust-core` `be1eecb` — v0.3.0: stardust-show crate
- `stardust-core` `1870592` — v0.2.1: expose stardust-patch + cpal 0.16→0.17
- `stardust-pit` `c53d30e` — v0.2.1: load_patch/save_patch + DiscoveryLock macOS fix
- `stardust-core` `a671e51` — stardust-patch crate (no tag — intermediate)
- `stardust-pit` `9cc09ed` — v0.2.0: engine thread + plugin-host commands
- `stardust-pit` `530ac1b` — v0.1.1: patch editor in app
- `stardust-pit` `7818cf8` — v0.1.0: Tauri bridge with 3 read-only commands
- `stardust-core` `54b7ad4` — v0.2.0: Phase 1.7 CLAP host bin
