# Stardust — work in progress handoff

**Last updated:** 2026-07-03 (post #9 testtone ship + bookkeeping)
**Purpose:** Lightweight pointer for whoever (or whichever chat) picks up Stardust work next. Current state + next task + how to bootstrap. Everything else lives in the canonical sources below.

> ## Source of truth (read in this order)
>
> 1. **GitHub Project board** — https://github.com/orgs/StardustMT/projects/1 — every feature, tech-debt item, and shipped work item as a milestone-tagged issue. Source of truth for *progress + scope*.
> 2. **Docs site** — https://stardustmt.github.io/docs/pit/ — what each feature is and why. Roadmap, per-feature pages, concept docs, widget catalog, screens, architecture, reliability, ecosystem, and the [locked-decisions reference](https://stardustmt.github.io/docs/pit/decisions/).
> 3. **ADRs** — `docs/adr/` — fully-argued decision records with revisit triggers.
> 4. **CLAUDE.md** — durable conventions + SDLC rules (three living docs, issue hygiene, refinement + review sessions, Storybook-first, accessibility, etc.).
> 5. **This file (HANDOFF.md)** — what's in flight + how to start the next chat. Nothing more.

---

## Current state

- **Shipping**: v0.5.0 (multi-plugin chain hosting via `engine_graph` Plan)
- **Board**: 122 issues. v0.1.0–v0.5.0 back-filled and ✅ Done; v0.6.0 in progress (#10 ✅, #11 ✅, #9 ✅); v0.7.0–v1.0.0 milestoned with acceptance criteria.
- **v0.6.0 progress**: 3/11 shipped.
  - **#10 ✅ shipped 2026-06-01** — GitHub Actions PR CI live on both repos (stardust-pit#114, stardust-core#11). All 5 status checks green. Spawned StardustMT/stardust-core#12 (cpal `DeviceTrait::name` migration) — `#[allow(deprecated)]` suppressions in stardust-audio need to come out when the device picker UI work picks them up.
  - **#11 ✅ shipped 2026-06-01** — Deleted `src/src/components/sound/` (8 files, 815 lines) + trimmed dead `SoundBlock`-typed orphans from `_demo-data.ts` (388 lines). Squash-merged as `5821a6d` (PR stardust-pit#115). Also closes the v0.5.0 tech-debt "sound/ orphaned" entry.
  - **#9 ✅ shipped 2026-07-03** — `instrument.sine` → `instrument.testtone`, merged via stardust-pit#116 (`36ca235`) + stardust-core#13 (`c2360c3`). `stardust.patch` + `stardust.show` bumped to schema v2 with raw-JSON v1→v2 migration (pre-deserialize). New Tauri command `engine_self_test` renders 2 s offline through a synthetic keyboard→testtone→sink graph and asserts peak 100 ms RMS > −24 dBFS (signal is a C6 note ≈ 1046.5 Hz — spec drift vs the 1 kHz sine, tech-debt logged on the roadmap). Canonical fixture `stardust-pit/src-tauri/tests/fixtures/v0.5.0-sine-show.json` covers the migration+audio end-to-end. New `SettingsScreen` + Storybook story; **live shell wiring spawned as stardust-pit#117 (v0.6.0)**. **Latent engine bug fixed in the process**: `topo_sort` was Kahn-only over audio wires, so `source.keyboard` (no audio I/O) could land *after* the instrument it MIDI-feeds, dropping every event by one block. Topo now stable-partitions sources first. First entry of `docs/schemas/CHANGELOG.md` (ADR-0003 obligation). Story screenshots live on the new `screenshots` orphan branch (`<sha>/<story>.png` — the #113 convention).
- **Next chunk**: #1 (`engine_rebind_routing`) per dependency order. M / P1 — swap MIDI/audio device without tearing down the Plan.
- **Branch protection ✅ 2026-07-03** — required status checks now enforced on `main` for both repos (pit: 3× rust + frontend + storybook; core: 3× rust). Set via API; the former "outstanding manual step" is closed, and the v0.6.0 exit criterion "PR CI is required on main" is met.

## Decisions reversed during v0.6.0 refinement

Both updated in `stardustmt.github.io/src/content/docs/docs/pit/decisions.md` and the roadmap. Future-you: don't re-derive — these are locked again.

- **Plugin GUI placement (#6)** — flipped from "floating Windows per plugin" to "docks in patch editor bottom panel by default, per-plugin pop-out to floating Window." Reason: docked matches how patch editing actually flows; float stays as a per-plugin escape hatch.
- **Windows audio default (#8)** — flipped from "WASAPI Exclusive default" to "ASIO when vendor driver detected AND input + output are the same device; WASAPI Exclusive otherwise (including any split I/O); WASAPI Shared as fallback." Reason: ASIO has measurable latency advantages on interfaces that ship a vendor driver; auto-pick beats "user must know to switch."

## v0.6.0 implementation order (dependency-driven)

1. ~~**#10** — GitHub Actions PR CI~~ · L · P1 · **✅ 2026-06-01**
2. ~~**#11** — Delete orphaned `sound/`~~ · XS · P2 · **✅ 2026-06-01**
3. ~~**#9** — Sine → `instrument.testtone`~~ · S · P2 · **✅ 2026-07-03**
4. **#1** — `engine_rebind_routing` (audio plumbing core) · M · P1 ← *next*
5. **#3** — Engine Panic command (needed by #5's Panic action) · S · P1
6. **#2** — Per-source-node hardware MIDI binding (foundational engine routing) · M · P1
7. **#4** — Plugin scan caching · M · P2
8. **#6** — Plugin GUI hosting (CLAP, dock-by-default UX) · L · P1
9. **#8** — Windows audio default (ASIO-when-detected) · M · P1
10. **#5** — Button/switch rig component (depends on #3 Panic) · L · P1
11. **#7** — Learn Master tool (depends on #5) · M · P2

## What's in flight right now

**Nothing.** #9 shipped 2026-07-03 (the diff had sat uncommitted locally for a month — re-validated green before shipping). Same-session bookkeeping closed:

- **Issue #9** — auto-closed by "Closes #9" in PR #116; closure comment posted with merge refs, what-shipped summary, and the C6-note spec-drift note. Storybook screenshots (idle / passing / failing) attached via the `screenshots` orphan branch.
- **#117 filed** — wire `SettingsScreen` into the live app shell (milestoned v0.6.0, `screen:settings` label created, board 📋 Planned, cross-linked to #9). Bump to v0.10.0 during refinement if v0.6.0 is judged wrong.
- **Roadmap** — #9 entry flipped ✅ with PR ref; v0.6.0 status line updated (3/11); self-test signal drift added to the tech-debt log.
- **decisions.md + architecture/engine.md** — brought current (`stardustmt.github.io@b384bc3`, `@f6d057c`).
- **Branch protection** — set on both repos (see Current state).

Next chat picks up #1 (`engine_rebind_routing`). Note #117 is also open v0.6.0 work — small, could ride along with any pit UI session.

---

## Next chat — bootstrap prompt

Paste this into a fresh `/clear`-ed session:

> Resuming Stardust work — **v0.6.0 implementation**, next up is **#1 (`engine_rebind_routing`)** per dependency order. #10 (PR CI), #11 (orphan deletion), and #9 (testtone migration) all shipped; v0.6.0 is 3/11 done, plus small spawned issue #117 (wire SettingsScreen into the shell) open. Read `HANDOFF.md` + `CLAUDE.md` first. Then read [#1 on the board](https://github.com/StardustMT/stardust-pit/issues/1) for its locked acceptance criteria — M / P1, audio plumbing core: swap MIDI/audio device without tearing down the Plan. After #1, #3 (engine Panic) → #2 (per-source hardware MIDI binding). Ship in small PRs that each reference the issue; update `docs/pit/` pages in the same PR as the feature ships per the three-living-documents rule. Storybook-first applies for any UI surface. Note: `main` on both repos now requires green CI checks to merge.

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
- **End a chat by asking me to update HANDOFF** before `/clear` — keep HANDOFF lightweight, push everything else into issues + docs
- **CLAUDE.md's terseness directives** keep prose minimal — don't remove them
- **Be specific** — "Refine v0.6.0 issue #5" is cheaper than "what should we do next?"
- **Refinement sessions are explicit** per CLAUDE.md — at the start of each version, walk through the issues + roadmap and lock in details before code
