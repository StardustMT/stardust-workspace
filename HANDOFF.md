# Stardust — work in progress handoff

**Last updated:** 2026-07-06 (rig-lite re-sequencing after post-#118 review)
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
- **Board**: 122 issues. v0.1.0–v0.5.0 back-filled and ✅ Done; v0.6.0 in progress (#10 ✅, #11 ✅, #9 ✅, #1 ✅, #2 ✅, #3 ✅); v0.7.0–v1.0.0 milestoned with acceptance criteria.
- **v0.6.0 progress**: 6/11 shipped.
  - **#1 + #2 + #3 ✅ shipped 2026-07-03 as one batch** — stardust-pit#118 (squash `4346c76`) + stardust-core#14 (`9885c33`, midir port ids). First use of the new batching convention (CLAUDE.md): three issues sharing the MIDI/audio ingress core, one PR, three closure comments.
    - **#1 rebind** — Plan travels between cpal streams via a Drop-carrier; `engine_rebind_routing` swaps devices with no plugin reloads, held voices intact; failures restore the original device. Engine panel takes the rebind path on device-only changes.
    - **#3 Panic** — new per-instrument voice tracker (16ch×128 bitset, fan-out-maintained); `engine_panic` flushes within one block (sustain-off, per-voice note-offs + poly-AT clear, CC123, PB center, CC1, chan-pressure, all channels). PanicButton in engine panel + global Shift+Esc.
    - **#2 per-source binding** — `hardwareBinding` in source-node config (no schema bump, logged in `docs/schemas/CHANGELOG.md`); up to 8 devices, pre-routed SPSC ingress, fan-out on overlap, kind event classes. Inspector + Storybook story + canvas device label. **Spec drift**: device identity is midir port id + name fallback, NOT `(vendor, product)` — midir exposes none; amended in decisions.md.
    - **Second latent engine bug fixed**: hw-target outbox never cleared → injected MIDI re-distributed every block. Regression-tested.
    - Live-device integration tests (`tests/rebind_live_device.rs`, `#[ignore]`d in CI) pass locally on macOS.
  - **#10 ✅ shipped 2026-06-01** — GitHub Actions PR CI live on both repos (stardust-pit#114, stardust-core#11). All 5 status checks green. Spawned StardustMT/stardust-core#12 (cpal `DeviceTrait::name` migration) — `#[allow(deprecated)]` suppressions in stardust-audio need to come out when the device picker UI work picks them up.
  - **#11 ✅ shipped 2026-06-01** — Deleted `src/src/components/sound/` (8 files, 815 lines) + trimmed dead `SoundBlock`-typed orphans from `_demo-data.ts` (388 lines). Squash-merged as `5821a6d` (PR stardust-pit#115). Also closes the v0.5.0 tech-debt "sound/ orphaned" entry.
  - **#9 ✅ shipped 2026-07-03** — `instrument.sine` → `instrument.testtone`, merged via stardust-pit#116 (`36ca235`) + stardust-core#13 (`c2360c3`). `stardust.patch` + `stardust.show` bumped to schema v2 with raw-JSON v1→v2 migration (pre-deserialize). New Tauri command `engine_self_test` renders 2 s offline through a synthetic keyboard→testtone→sink graph and asserts peak 100 ms RMS > −24 dBFS (signal is a C6 note ≈ 1046.5 Hz — spec drift vs the 1 kHz sine, tech-debt logged on the roadmap). Canonical fixture `stardust-pit/src-tauri/tests/fixtures/v0.5.0-sine-show.json` covers the migration+audio end-to-end. New `SettingsScreen` + Storybook story; **live shell wiring spawned as stardust-pit#117 (v0.6.0)**. **Latent engine bug fixed in the process**: `topo_sort` was Kahn-only over audio wires, so `source.keyboard` (no audio I/O) could land *after* the instrument it MIDI-feeds, dropping every event by one block. Topo now stable-partitions sources first. First entry of `docs/schemas/CHANGELOG.md` (ADR-0003 obligation). Story screenshots live on the new `screenshots` orphan branch (`<sha>/<story>.png` — the #113 convention).
- **Re-sequenced 2026-07-06 (user decision)**: **#122 rig-lite** pulled forward from v0.10.0 into v0.6.0 — real Setup → Rig screen, component-level device binding, basic Learn, source nodes reference components (node-level `hardwareBinding` becomes fallback), engine derives MIDI inputs from the rig. Why: #5/#7 already assumed a rig surface; per-patch raw bindings accrue migration debt; real-hardware test loop for the rest of Program. Roadmap v0.6.0 + v0.10.0 entries and decisions.md updated (`stardustmt.github.io@e174d45`). Compounds/widget-editor/velocity-curves stay v0.10.0 — don't let #122 scope-creep.
- **Next chunk**: **#122 refinement session first** (it's `needs-refinement` — walk the draft AC with the user, lock UX against the approved `setup-rig` Storybook mock, set Estimate/Priority, re-scope #121's leftover), then implement. After #122: #5 → #7; #4/#6/#8 close the version.
- **Branch protection ✅ 2026-07-03** — required status checks now enforced on `main` for both repos (pit: 3× rust + frontend + storybook; core: 3× rust). Set via API; the former "outstanding manual step" is closed, and the v0.6.0 exit criterion "PR CI is required on main" is met.

## Decisions reversed during v0.6.0 refinement

Both updated in `stardustmt.github.io/src/content/docs/docs/pit/decisions.md` and the roadmap. Future-you: don't re-derive — these are locked again.

- **Plugin GUI placement (#6)** — flipped from "floating Windows per plugin" to "docks in patch editor bottom panel by default, per-plugin pop-out to floating Window." Reason: docked matches how patch editing actually flows; float stays as a per-plugin escape hatch.
- **Windows audio default (#8)** — flipped from "WASAPI Exclusive default" to "ASIO when vendor driver detected AND input + output are the same device; WASAPI Exclusive otherwise (including any split I/O); WASAPI Shared as fallback." Reason: ASIO has measurable latency advantages on interfaces that ship a vendor driver; auto-pick beats "user must know to switch."

## v0.6.0 implementation order (dependency-driven)

1. ~~**#10** — GitHub Actions PR CI~~ · L · P1 · **✅ 2026-06-01**
2. ~~**#11** — Delete orphaned `sound/`~~ · XS · P2 · **✅ 2026-06-01**
3. ~~**#9** — Sine → `instrument.testtone`~~ · S · P2 · **✅ 2026-07-03**
4. ~~**#1** — `engine_rebind_routing` (audio plumbing core)~~ · M · P1 · **✅ 2026-07-03 (batch, PR #118)**
5. ~~**#3** — Engine Panic command (needed by #5's Panic action)~~ · S · P1 · **✅ 2026-07-03 (batch, PR #118)**
6. ~~**#2** — Per-source-node hardware MIDI binding (foundational engine routing)~~ · M · P1 · **✅ 2026-07-03 (batch, PR #118)**
7. **#122** — Rig-lite: real Setup → Rig, component-level bindings (pulled from v0.10.0; `needs-refinement`) · est. M–L · P1 ← *next: refine, then build*
8. **#5** — Button/switch rig component (depends on #3 Panic + #122 rig surface) · L · P1
9. **#7** — Learn Master tool (depends on #5 + #122) · M · P2
10. **#4** — Plugin scan caching · M · P2
11. **#6** — Plugin GUI hosting (CLAP, dock-by-default UX) · L · P1
12. **#8** — Windows audio default (ASIO-when-detected) · M · P1

Also open, ride-along-sized: **#117** (SettingsScreen into shell), **#121** (retire EnginePanel — re-scope during #122 refinement; its MIDI-derivation half moved into #122), **#119 ✅** (viewport overflow, fixed 2026-07-06 PR #120).

## What's in flight right now

**Nothing.** The #1/#2/#3 batch shipped 2026-07-03; all bookkeeping closed same-session:

- **Issues #1, #2, #3** — auto-closed by PR #118; closure comments posted with merge refs, what-shipped summaries, and drift notes. Inspector Storybook screenshots attached to #2 via the `screenshots` orphan branch (`4346c76/…`).
- **Board** — all three ✅ Done.
- **Roadmap** — scope bullets flipped ✅; status 6/11; tech-debt table updated (two v0.5.0 items closed, four new v0.6.0 entries: port-id identity drift, rebind swap gap, no portable underrun counter, fixed panic shortcut).
- **decisions.md** — device-identity amendment + rebind decision tree + panic reset scope + kind event classes.
- **architecture/engine.md + reliability/voice-tracking.md + concepts/rig-components.md** — brought current.
- **`docs/schemas/CHANGELOG.md`** — `hardwareBinding` additive-config entry (no version bump).

**Post-ship review (2026-07-06):** user testing surfaced a viewport-overflow bug — `AppShellFrame` forced `h-screen` below the Tauri-only EnginePanel strip, scrolling the status footer off-screen. Fixed + merged same-session (**#119 → PR #120, `e4f773f`**; verified headlessly: 879px→830px scrollHeight). Review feedback also spawned **#121** (derive engine MIDI inputs from patch bindings, retire the EnginePanel strip entirely — depends on #4 + #117, board 📋 Planned, `needs-refinement`). A "Launchkey not found" report turned out to be environment: macOS saw **zero USB devices** on either bus (`system_profiler SPUSBHostDataType`) — cable/port issue, not app code.

**Loose ends for the user (not blocking):**

1. **Manual ear test for #1** — sustained pad, swap audio device, listen for the swap gap. The stream close→open leaves a few-ms silence; if audible/objectionable, file a follow-up (overlapping-stream crossfade). AC asked for the result recorded in the PR — pending user signoff, noted on #1.
2. **Inspector UX review** — the source-binding inspector was built to the mock locked in refinement, but the Storybook-first "demo → iterate" loop ran without you. Stories: `Patch Editor/Source Binding Inspector` (screenshots on #2).
3. **#117** (wire SettingsScreen into the shell) — still open v0.6.0 work, small, rides along with any pit UI session.

---

## Next chat — bootstrap prompt

Paste this into a fresh `/clear`-ed session:

> Resuming Stardust work — **v0.6.0, rig-lite refinement + implementation**. Start with a **refinement session for [#122](https://github.com/StardustMT/stardust-pit/issues/122)** (rig-lite: real Setup → Rig screen, component-level device bindings, basic Learn, `rigComponentId` on source nodes with node-level `hardwareBinding` as fallback, engine MIDI inputs derived from the rig). It's `needs-refinement`: walk the draft AC with me issue-by-issue, lock UX against the approved `setup-rig` Storybook mock (extract, don't rebuild), set Estimate/Priority on the board, and re-scope #121's leftover (Settings audio picker, real status footer, EnginePanel deletion) — #117 may batch in. Guardrail: compounds, widget editor, velocity curves, per-pad config stay v0.10.0. Then implement; after #122 the order is #5 → #7, then #4/#6/#8. Context: v0.6.0 re-sequenced 2026-07-06 (roadmap + decisions.md already updated — don't re-litigate); the #1/#2/#3 engine batch shipped as PR stardust-pit#118 and its engine plumbing (device matching, filters, rebind) carries over unchanged. Read `HANDOFF.md` + `CLAUDE.md` first. Batch issues that logically ship together into one PR/commit set, referencing each; docs ship in the same PR per the three-living-documents rule. Storybook-first for any new UI surface. `main` on both repos requires green CI. Loose ends waiting on the user: the #1 ear test verdict and the #2 inspector UX pass.

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
