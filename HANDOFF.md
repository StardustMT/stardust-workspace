# Stardust — work in progress handoff

**Last updated:** 2026-06-01 (post #11 orphan-cleanup ship)
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
- **Board**: 122 issues. v0.1.0–v0.5.0 back-filled and ✅ Done; v0.6.0 in progress (#10 ✅, #11 ✅); v0.7.0–v1.0.0 milestoned with acceptance criteria.
- **v0.6.0 progress**: 2/11 shipped.
  - **#10 ✅ shipped 2026-06-01** — GitHub Actions PR CI live on both repos (stardust-pit#114, stardust-core#11). All 5 status checks green. Spawned StardustMT/stardust-core#12 (cpal `DeviceTrait::name` migration) — `#[allow(deprecated)]` suppressions in stardust-audio need to come out when the device picker UI work picks them up.
  - **#11 ✅ shipped 2026-06-01** — Deleted `src/src/components/sound/` (8 files, 815 lines) + trimmed dead `SoundBlock`-typed orphans from `_demo-data.ts` (388 lines). Squash-merged as `5821a6d` (PR stardust-pit#115). Also closes the v0.5.0 tech-debt "sound/ orphaned" entry.
- **Next chunk**: #9 (sine → `instrument.testtone`) per dependency order. S / P2 — small schema migration; hide sine from the catalog, expose as diagnostic-only.

## Outstanding manual step

Branch protection rules on `main` for both repos. **Not configured yet.** Required status checks to set in the GitHub UI (Settings → Branches):

- **stardust-pit**: `rust (ubuntu-latest)`, `rust (macos-latest)`, `rust (windows-latest)`, `frontend (ubuntu)`, `storybook (ubuntu)`
- **stardust-core**: `rust (ubuntu-latest)`, `rust (macos-latest)`, `rust (windows-latest)`

The workflow files exist and run; protection is the one-time UI toggle that makes them required-to-merge.

## Decisions reversed during v0.6.0 refinement

Both updated in `stardustmt.github.io/src/content/docs/docs/pit/decisions.md` and the roadmap. Future-you: don't re-derive — these are locked again.

- **Plugin GUI placement (#6)** — flipped from "floating Windows per plugin" to "docks in patch editor bottom panel by default, per-plugin pop-out to floating Window." Reason: docked matches how patch editing actually flows; float stays as a per-plugin escape hatch.
- **Windows audio default (#8)** — flipped from "WASAPI Exclusive default" to "ASIO when vendor driver detected AND input + output are the same device; WASAPI Exclusive otherwise (including any split I/O); WASAPI Shared as fallback." Reason: ASIO has measurable latency advantages on interfaces that ship a vendor driver; auto-pick beats "user must know to switch."

## v0.6.0 implementation order (dependency-driven)

1. ~~**#10** — GitHub Actions PR CI~~ · L · P1 · **✅ 2026-06-01**
2. ~~**#11** — Delete orphaned `sound/`~~ · XS · P2 · **✅ 2026-06-01**
3. **#9** — Sine → `instrument.testtone` (small schema migration) · S · P2 ← *next*
4. **#1** — `engine_rebind_routing` (audio plumbing core) · M · P1
5. **#3** — Engine Panic command (needed by #5's Panic action) · S · P1
6. **#2** — Per-source-node hardware MIDI binding (foundational engine routing) · M · P1
7. **#4** — Plugin scan caching · M · P2
8. **#6** — Plugin GUI hosting (CLAP, dock-by-default UX) · L · P1
9. **#8** — Windows audio default (ASIO-when-detected) · M · P1
10. **#5** — Button/switch rig component (depends on #3 Panic) · L · P1
11. **#7** — Learn Master tool (depends on #5) · M · P2

## What's in flight right now

**Nothing.** #11 shipped 2026-06-01. Same-session bookkeeping closed:

- **Issue #11** — auto-closed by "Closes #11" in PR #115. Closure comment posted with merge ref, file list, and reaffirmation that v0.10.0 will rebuild from scratch.
- **Roadmap** — v0.6.0 scope entry flipped to ✅ shipped with the PR ref; v0.5.0 tech-debt "sound/ orphaned" entry moved to ✅ v0.6.0 with the same ref.
- **No docs page** — #11 is housekeeping (no user-facing surface). `git log --follow` on any deleted path lands on the squash commit for archaeology.

Next chat picks up #9 (sine → `instrument.testtone`).

---

## Next chat — bootstrap prompt

Paste this into a fresh `/clear`-ed session:

> Resuming Stardust work — **v0.6.0 implementation**, next up is **#9 (sine → `instrument.testtone`)** per dependency order. #10 (PR CI) and #11 (orphan deletion) both shipped 2026-06-01; CI is green on `main` in both repos. Read `HANDOFF.md` + `CLAUDE.md` first. Then read [#9 on the board](https://github.com/StardustMT/stardust-pit/issues/9) for its locked acceptance criteria — it's S / P2, a small schema migration that hides the sine synth from the catalog and re-files it as a diagnostic-only `instrument.testtone`. After #9, the next chunk is #1 (`engine_rebind_routing`), then #3 (engine Panic). Ship in small PRs that each reference the issue; update `docs/pit/` pages in the same PR as the feature ships per the three-living-documents rule. Storybook-first applies for any UI surface.

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
