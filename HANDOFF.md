# Stardust — work in progress handoff

**Last updated:** 2026-06-01 (post #10 PR CI ship)
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
- **Board**: 122 issues. v0.1.0–v0.5.0 back-filled and ✅ Done; v0.6.0 in progress (#10 ✅); v0.7.0–v1.0.0 milestoned with acceptance criteria.
- **v0.6.0 progress**: 1/11 shipped. **#10 ✅ shipped 2026-06-01** — GitHub Actions PR CI live on both repos (stardust-pit#114, stardust-core#11). All 5 status checks green on first push to main. Spawned StardustMT/stardust-core#12 (cpal `DeviceTrait::name` migration) — `#[allow(deprecated)]` suppressions in stardust-audio need to come out when the device picker UI work picks them up.
- **Next chunk**: #11 (delete orphaned `sound/`) per dependency order. Trivial XS housekeeping; verified green by the CI we just landed.

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
2. **#11** — Delete orphaned `sound/` (housekeeping; verified green by #10) · XS · P2 ← *next*
3. **#9** — Sine → `instrument.testtone` (small schema migration) · S · P2
4. **#1** — `engine_rebind_routing` (audio plumbing core) · M · P1
5. **#3** — Engine Panic command (needed by #5's Panic action) · S · P1
6. **#2** — Per-source-node hardware MIDI binding (foundational engine routing) · M · P1
7. **#4** — Plugin scan caching · M · P2
8. **#6** — Plugin GUI hosting (CLAP, dock-by-default UX) · L · P1
9. **#8** — Windows audio default (ASIO-when-detected) · M · P1
10. **#5** — Button/switch rig component (depends on #3 Panic) · L · P1
11. **#7** — Learn Master tool (depends on #5) · M · P2

## What's in flight right now

**Nothing.** #10 shipped 2026-06-01. Same-session bookkeeping closed:

- **Issue #10** — auto-closed by "Closes #10" in the workflow commit. Closure comment posted with commit refs (pit + core), follow-up issue link, and the outstanding branch-protection step.
- **Roadmap** — v0.6.0 scope entry flipped to ✅ shipped with date + PR refs; tech-debt log updated (CI no-pipeline + `tsc --noEmit` items now ✅; cpal-deprecation item re-pointed at core#12).
- **No docs page** — #10 is infra (no user-facing surface to document). The build/test conventions are evident from the workflow file and CONTRIBUTING.md.
- **Follow-up filed** — StardustMT/stardust-core#12, cross-linked from PR #11.

Next chat picks up #11 (delete orphaned `sound/`).

---

## Next chat — bootstrap prompt

Paste this into a fresh `/clear`-ed session:

> Resuming Stardust work — **v0.6.0 implementation**, next up is **#11 (delete orphaned `sound/` components)** per dependency order. #10 (PR CI) shipped 2026-06-01; CI is now green on `main` in both repos. Read `HANDOFF.md` + `CLAUDE.md` first. Then read [#11 on the board](https://github.com/StardustMT/stardust-pit/issues/11) for its locked acceptance criteria — it's XS / P2 housekeeping, expected to be a single PR. After #11, the next chunk is #9 (sine → `instrument.testtone`), then #1 (`engine_rebind_routing`). Ship in small PRs that each reference the issue; update `docs/pit/` pages in the same PR as the feature ships per the three-living-documents rule. Storybook-first applies for any UI surface.

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
