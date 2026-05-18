# ADR-0002: Out-of-process plugin sandboxing for Pit

- **Status:** Accepted
- **Date:** 2026-05-18
- **Deciders:** @ChaseCondon
- **Affects:** stardust-pit, stardust-core

## Context

A live performance host loads audio plugins (VST3, CLAP, AU on macOS) into its address space. The dominant industry pattern — used by every major DAW and by MainStage — is **in-process hosting**: the host process directly `dlopen`s the plugin binary, calls into its C++ ABI, and shares memory with it.

In-process hosting is fast (no IPC overhead, sample-accurate dispatch via direct function call) but has one catastrophic failure mode for a live performance app:

> **A misbehaving plugin can crash the entire host.**

For a DAW, this is annoying — you lose your unsaved work. For a live performance app **mid-show**, this ends a musician's career night. Every active keyboard player has at least one story about MainStage crashing during a critical cue.

The single most important property of Pit is that the show keeps running. Reliability is the single biggest differentiator vs. MainStage. Therefore the plugin model has to make "rogue plugin kills host" architecturally impossible, not merely unlikely.

## Decision

**Plugins run out-of-process in sandboxed child workers, communicating with the host via shared-memory ring buffers and a small control IPC channel.**

Architecture:

```
                stardust-pit  (host process, never holds plugin code)
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
        worker A   worker B  worker C    (one process per loaded plugin instance,
        │ VST3 │   │ CLAP │  │  AU  │     spawned on demand, hard-killable)
        └──────┘   └──────┘  └──────┘
              │        │        │
         shared ring   shared ring   shared ring
         (audio I/O + MIDI + control)
```

Each plugin worker:

- runs as an independent OS process
- loads exactly one plugin instance
- communicates via lock-free shared-memory ring buffers (audio + MIDI) plus a control channel (parameter changes, state save/load)
- is monitored by a watchdog in the host; if it crashes or hangs, the host detects it within a deadline (target ~10ms), substitutes silence for that slot, and surfaces a non-fatal error to the user
- can be restarted in-place without restarting the host

The IPC + worker lifecycle code lives in `stardust-core` (specifically `overture-plugin` and `overture-ipc`, pending the rename). The host (Pit) consumes them.

## Consequences

**Easier:**
- A crashing plugin no longer crashes the show. Substituted silence + visible warning > total host death.
- Per-plugin CPU isolation (host can throttle a runaway worker independently)
- Per-plugin permissions / capability scoping (filesystem, network) for future security model
- Plugins can be loaded/unloaded without restarting the host, including across architectures (e.g., x86_64 plugin on an aarch64 host via translation)
- Plugin debugging is independent (attach a debugger to one worker without freezing the host)
- Bit-level safer for proprietary/closed-source plugins (less worry about heap corruption affecting host state)

**Harder:**
- IPC overhead is real (target: <0.5ms round-trip for audio buffer transfer on a typical buffer size of 128 samples @ 48kHz)
- Sample-accurate parameter automation requires careful timestamp passing across the boundary
- Plugin GUIs require platform-specific window-embedding tricks (out-of-process GUI rendering into the host window)
- We have to ship and maintain the worker binary alongside the host
- Memory footprint per plugin is higher (per-process overhead vs. shared address space)

**New obligations:**
- Define and version the IPC protocol (see ADR-0003 on schema versioning — this is one of the protocols subject to that)
- Build a watchdog and recovery path before the v1 release; not optional
- Maintain plugin-format adapters for VST3, CLAP, and (macOS) AU within each worker

## Alternatives considered

### In-process hosting (the industry default)

Faster, simpler, well-trodden path. Rejected because the single most important property of Pit is "the show keeps running" and in-process hosting fundamentally cannot guarantee that. Every comparable competitor (MainStage, Camelot, Cantabile, Gig Performer) takes this approach and every one of them has stories of mid-show crashes.

### Hybrid: in-process for "trusted" plugins, out-of-process for others

Tempting but the trust model is unclear (who decides? user? signature? blocklist?) and the operational cost of maintaining two code paths is high. If we have to ship the out-of-process path anyway for safety, ship only that.

### Out-of-process via OS sandboxing (App Sandbox / seccomp) without separate processes

Doesn't solve the crash problem — sandboxing constrains what a plugin can do but not whether it can segfault the host. Different problem.

### Wasm-sandboxed plugins

Interesting long-term. Doesn't help today because the entire commercial plugin ecosystem is native code (VST3 / CLAP / AU). May become viable as a Stardust-specific plugin format in v2+; not a substitute for hosting native plugins.

## Revisit trigger

- If IPC overhead measurably impacts achievable latency at typical live-performance buffer sizes (target: full round-trip ≤6ms @ 128 samples @ 48kHz) we may need to revisit the IPC mechanism (consider io_uring on Linux, kernel-mode bypass, etc) — but not the out-of-process decision itself.
- If a future plugin format provides a memory-safe in-process model with crash isolation (e.g., a verified Wasm-based standard adopted across the industry), revisit whether to dual-host.
