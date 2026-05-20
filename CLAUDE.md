# Stardust Workspace — Claude Instructions

> **New chat resuming Stardust work?** Read `HANDOFF.md` first — it
> tracks in-flight work that's mid-extraction, the active roadmap
> phase, and decisions worth not re-litigating. This file (CLAUDE.md)
> covers durable conventions; HANDOFF.md covers "what are we doing
> right now".

This directory is the **Stardust meta-workspace**. It contains:

- `stardust-pit/` — the live-performance VST host (app)
- `stardust-core/` — shared Rust libraries / SDK (formerly Overture)
- `stardustmt.github.io/` — marketing site + docs (Astro + Starlight)
- `docs/adr/` — architecture decision records for the ecosystem
- `scripts/` — bootstrap, update, and cross-repo orchestration
- `_wiki-source/` — **temporary** — old GitHub wiki being migrated to `stardustmt.github.io/`. Delete after migration is verified.

Each app/library is its own git repo. This workspace repo orchestrates them but does not own their code.

GitHub org: **StardustMT**.

---

## Architectural rules

These apply across every repo in the workspace.

- **UI never owns realtime.** React / webview / Tauri IPC must never own audio scheduling, MIDI timing, or protocol timing. The signal flow is: React UI → Tauri IPC → Rust orchestration → native realtime engine. Crossing that boundary in the wrong direction is a bug.
- **Core crates are UI-agnostic.** `stardust-core` and any future shared crate must not depend on Tauri, React, or any frontend lifecycle.
- **Out-of-process plugin hosting.** VST3/CLAP/AU plugins run in sandboxed child processes communicating via shared-memory IPC. A crashing plugin must not take down the host.
- **Protocol abstractions over raw protocols.** Apps consume Stardust abstractions for MIDI / OSC / DMX, not raw protocol implementations directly.
- **Local-first, cloud-optional.** Every workflow must function without a network connection. Galaxy (cloud sync, marketplace) is additive, never required.
- **Theatre vocabulary in user-facing surfaces.** Show / Song / Patch / Sound — not Project / Track / Channel / Voice. DAW analogues are familiar but wrong for the user.

---

## SDLC rules

- **Significant architecture changes require an ADR.** See `docs/adr/`. Status workflow: Proposed → Accepted → (Deprecated | Superseded).
- **Schemas are versioned.** Any persisted format (patch files, show files, library entries) requires a migration path before merge.
- **Cross-app protocols are versioned.** When stardust-core gains a feature consumed by multiple apps, the consumed surface is versioned.
- **Prefer incremental architectural evolution.** No big-bang rewrites.
- **No premature microservices.** Within stardust-core, prefer shared crates over IPC where possible.
- **PRs land small.** A reviewer should be able to read the whole diff in one sitting.

---

## Coding standards

- **Strong typing everywhere.** No `any` in TypeScript, no `dyn Any` in Rust without justification.
- **Explicit over clever.** Magic abstractions cost more than they save.
- **Realtime paths are allocation-safe.** Audio callback, MIDI dispatch, etc. must not allocate or lock.
- **Frontend / backend coupling is minimized.** State that belongs in Rust stays in Rust.
- **Semantic versioning is honored.** Once a crate publishes 1.0, breaking changes require a major bump.

---

## Product philosophy

- **Stardust apps work standalone.** Pit must be useful without Sheets, Sheets without Pit. Ecosystem integration is additive.
- **UX scales from solo performer to full production.** A cabaret musician and a regional MD use the same app.
- **Professional reliability over novelty.** A musician's career depends on the patch loading mid-show. That is the single most important property.
- **Theatre workflows over generic workflows.** Vamps, codas, transposition, cascading settings — these are first-class, not accommodations.
- **No enterprise bloat.** If a feature only makes sense for a 50-person production company, it does not ship.

---

## Current priorities

Pit v0.1 (Foundations) is the active focus. Sheets is post-Pit-v1. Everything else (Rehearse, Produce, Stage, Lighting, Galaxy) is speculative — do not scaffold those repos or write code targeting them.

When working on Pit:

1. Stability before features
2. Audio architecture
3. Plugin hosting (sandboxed)
4. Routing
5. Patch / setlist system
6. MT-specific workflows

When working on stardust-core:

- Build only what Pit actually needs in the current iteration
- Resist building "for the future ecosystem"

---

## Things to explicitly avoid

- Adopting Bazel, Nx, Pants, or other heavyweight build orchestration (Moonrepo is the deferred future option; revisit when CI hurts)
- Premature shared-UI extraction — `stardust-ui` is not a separate repo until Sheets exists and there is real duplication
- Mandatory cloud / DRM / subscription-only features
- Full OMR (optical music recognition) — Sheets uses PDFs + semantic overlays, not parsing
- AI features without a clear, theatre-specific value proposition
- Plugin ABI stabilization before there are real plugin authors
