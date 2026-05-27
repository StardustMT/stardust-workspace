# ADR-0008: Crate organization — flat workspace

- **Status:** Accepted
- **Date:** 2026-05-27
- **Deciders:** @ChaseCondon
- **Affects:** stardust-core

## Context

`stardust-core` is a Cargo workspace of multiple crates (audio, midi, dsp, patch, show, plugin, rt). As the crate count grows, the question is whether to stay flat or introduce nested workspaces / crate sub-groups. This needs a decision so future crate additions follow a consistent pattern rather than being relitigated each time.

## Decision

**Stay a flat Cargo workspace.** Group crates by naming convention (`stardust-audio-*`, `stardust-midi-*`, etc.) if a family grows, rather than introducing nested workspaces. Current layout:

```
stardust-core/
├── Cargo.toml             # workspace root
└── crates/
    ├── stardust-audio/    # cpal output wrapper
    ├── stardust-midi/     # MIDI types + midir wrapper
    ├── stardust-dsp/      # native DSP nodes (EQ, synth, shared envelope)
    ├── stardust-patch/    # patch-graph data model
    ├── stardust-show/     # show document data model
    ├── stardust-plugin/   # CLAP host
    └── stardust-rt/       # realtime primitives (SPSC rings)
```

Most large Rust projects (tokio, axum, bevy) stay flat. A flat workspace keeps `cargo` commands simple, dependency edges visible, and avoids the cognitive overhead of nested-workspace tooling quirks.

## Consequences

- **Easier:** `cargo check --workspace`, `cargo test --workspace` cover everything; one lockfile; dependency graph is one level deep and easy to reason about.
- **Easier:** new crates drop into `crates/` with a naming-convention prefix; no decision about which sub-workspace they belong to.
- **Harder (eventually):** at a large crate count, a flat `crates/` directory becomes a long list. Naming conventions (`stardust-audio-*`) mitigate this but don't eliminate it.
- **Obligation:** keep crate names prefixed and descriptive so the flat list stays scannable.

## Alternatives considered

- **Nested workspaces** (e.g., `audio/` workspace, `data/` workspace) — rejected: adds tooling complexity, multiple lockfiles or virtual-manifest gymnastics, and the cross-workspace dependency story in Cargo is awkward. Not worth it below ~15 crates.
- **Monocrate with modules** — rejected: loses the ability to compile/test crates independently, slows incremental builds, and couples unrelated subsystems.

## Revisit trigger

Revisit if the workspace grows past **~15 crates** and the flat `crates/` list becomes hard to navigate, or if build times degrade in a way that crate-group isolation would fix.
