# Stardust — work in progress handoff

**Last updated:** 2026-05-20 (post v0.5 patch bridge + macOS launch fix)
**Purpose:** Read this first in any new chat that's resuming Stardust work,
especially when switching machines. Bridges what `git log` can't show you
on its own: where we are in the roadmap, what's in flight, and what
decisions are baked in.

---

## Roadmap status

Phase model from earliest project memory; ticked items have working code on
`main` in the named repo.

### `stardust-core` (Rust audio engine)

- [x] **Phase 1.1–1.4** — `stardust-midi` (midir), `stardust-audio` (cpal),
  `stardust-rt` (rtrb SPSC), `stardust-dsp` (polyphonic sine + ADSR), plus
  `stardust-ipc` scaffold.
- [x] **Phase 1.5** — Integration CLI `stardust-poc-play` proves MIDI →
  SPSC ring → audio thread → synth → cpal output end-to-end.
- [x] **Phase 1.6** — `stardust-plugin` does CLAP **scan + describe** via
  `clack-host`. Recursive walk of standard search paths (Linux / macOS /
  Windows) + `CLAP_PATH`. `stardust-poc-clap-list` bin enumerates.
- [x] **Phase 1.7** — `stardust-poc-host-clap` bin **hosts a CLAP plugin
  live**: pick plugin + MIDI input + audio output, plays in real time.
  Verified working with Surge XT. sforzando installs but needs the GUI
  extension to pick an SFZ file (deferred — Pit will own this).
- [x] **stardust-sfz** — first-party CLAP SFZ sampler plugin (Phase 1.6½).
  **SHELVED** — user installed sforzando (which has CLAP) so the in-house
  player isn't needed. Crate stays in the workspace; don't proactively
  improve it unless asked.
- [x] **Shared envelope primitive** — `stardust-dsp::Envelope` (ADSR)
  used by both the sine synth and stardust-sfz. Template for future
  cross-utilised DSP primitives.
- [x] **`stardust-patch` crate** — patch-graph data model (ADR-0004).
  Pure data; faithful Rust mirror of the TS shape in
  `stardust-pit/src/src/components/patch-graph/_types.ts`. Serializes
  as camelCase JSON so the Tauri bridge round-trips without adapters.
  Schema-versioned per ADR-0003 (`kind: "stardust.patch"`, v1).
  Collect-all structural validation. 12 tests: 4 fixture round-trips
  from `_seed-data.ts` + 7 validation negatives + header sanity.

### `stardust-pit` (Tauri 2 app)

- [x] **v0.1 scaffold** — Tauri 2 + React 19 + Vite + Storybook + bun.
  React UI lives in `src/src/`, Rust host in `src-tauri/`. Builds via
  `bun dev` (uses `@tauri-apps/cli` JS, NOT `cargo-tauri`).
- [x] **v0.2 bridge** — Three read-only Tauri commands:
  `list_clap_plugins`, `list_midi_inputs`, `list_audio_outputs`. Wired
  to a diagnostic 3-card view in `App.tsx`. Confirmed working on
  Windows: shows real plugin / MIDI / audio device data.
- [x] **v0.3 patch editor in the app** — `bun dev` opens the full
  Stardust shell with the v5 patch editor + seed data. Client-side
  state only; engine wiring deferred to v0.4+.
- [x] **v0.4 engine thread + plugin-host commands** — dedicated
  `engine` module owns a thread that holds the `!Send` CLAP plugin.
  Three Tauri commands (`engine_start`, `engine_stop`, `engine_status`)
  + `engine://status` event stream. UI exposes a diagnostic
  `EnginePanel` above the patch editor: pick plugin + MIDI in +
  audio out, hit Start, the plugin plays live.
- [x] **v0.5 patch-document bridge** — Two Tauri commands:
  `load_patch(json) -> Result<PatchDocument, PatchError>` and
  `save_patch(doc) -> Result<String, PatchError>`. Structured errors
  (`Parse | Validation`) — UI can render parse failures as one
  message and validation failures as a list. Pure JSON ↔ struct; the
  React side owns the file dialog via `tauri-plugin-dialog` +
  `tauri-plugin-fs`. `stardust-patch` exposed via the umbrella
  `stardust-core` `patch` feature (included in `full`).
- [x] **v0.5 collateral: macOS launch fix** — on macOS 26 the app
  segfaulted in `HALDeviceList::GetData` during startup discovery.
  Two compounding bugs: (1) CLAP `dlopen` and CoreAudio enumeration
  were running concurrently on tokio workers, (2) cpal 0.16 predates
  macOS 26 and had no CoreAudio fixes. Fix landed: a
  `DiscoveryLock` (tokio async mutex) serializes all three `list_*`
  commands, and each now runs its blocking work via
  `tokio::task::spawn_blocking`. cpal bumped 0.16 → 0.17.1 in the
  workspace (0.17.0 reworked the CoreAudio FFI layer). Confirmed
  launching on macOS 26.3.1 / MacBook Air M1.

### Whole-ecosystem

- [x] All Storybook v5 patch editor work (rig-bound sources, composite
  blocks as real wire targets, zone color picker, undo coalescing,
  validation alias, MIDI Learn buttons, sustain pedal, looping, etc.)
- [x] stardustmt.github.io — marketing + docs site exists, separate cadence.

---

## Currently in flight

Nothing mid-extraction. v0.5 + the macOS launch fix just shipped.
Pending: commit + push (changes touch both repos), then a new chat.

Loose ends worth picking up next session:

- **v0.6: Open / Save buttons in the patch editor.** Wire the
  existing `load_patch` / `save_patch` Tauri commands to UI buttons
  via `tauri-plugin-dialog` (file picker) + `tauri-plugin-fs`
  (read/write). The Rust side is ready; the UI is not.
- **Round-trip smoke test still pending.** v0.5 ships the commands
  but nothing has yet round-tripped a `_seed-data.ts` fixture
  through `save_patch(load_patch(json))`. Worth doing from devtools
  before wiring up the UI buttons.
- **MIDI keyboard testing without hardware.** Today the EnginePanel
  needs a real MIDI input device. Idea worth pursuing: repurpose
  the preview keyboard UI element (from the patch editor stories)
  as an in-app MIDI source so the engine can be exercised without
  external hardware. Useful for laptop dev + headless CI.
- **`tsc --noEmit`** in `ui:build` fails on a pre-existing tsconfig
  project-references bug (`tsconfig.node.json` not marked composite).
  Storybook + cargo + `bun dev` all work; just `bun ui:build`'s
  type-check step trips. Predates v0.4.
- **Plugin metadata scan is eager + uncached.** Every app launch
  dlopens every installed `.clap`. Fine today, will need an
  mtime-keyed cache once users have large libraries. Patches
  themselves don't pull plugins; only the metadata scan does.
- **cpal `DeviceTrait::name` deprecation warnings (3).** cpal 0.17
  wants `description()` / `id()` instead. Functional, just noisy.
- **No graceful shutdown** on the engine thread. The thread is
  reaped when the process exits; `EngineCommand::Shutdown` is
  defined but unused. Fine for now.

---

## Bootstrap prompt for a new chat

When starting a fresh Claude Code chat (on any machine, after `/clear`,
or to begin the next feature), paste this verbatim into the first
message:

> Resuming Stardust work. Read `HANDOFF.md` (and `CLAUDE.md` for
> conventions). Tell me what shipped most recently, what loose ends are
> open, and what the next obvious feature is. Don't start any work yet —
> wait for me to pick.

That gets me oriented in one round trip without me re-reading half the
codebase or asking ten clarifying questions.

If you want to jump straight into a specific known-next feature,
substitute that for the last sentence:

> Resuming Stardust work. Read `HANDOFF.md` (and `CLAUDE.md` for
> conventions). Then push on `[feature name]`. Tell me the plan before
> you start coding.

## Resuming on a different machine

Steps to pick up cleanly on the laptop:

```bash
# 1. Pull every repo
cd ~/projects/stardust && git pull   # this meta-repo (CLAUDE.md + HANDOFF.md)
cd stardust-pit && git pull
cd ../stardust-core && git pull

# 2. JS deps (only once per machine + after package.json changes)
cd ../stardust-pit && bun install

# 3. Verify everything works
bun ui:build-storybook     # frontend TS compile
cd ../stardust-core && cargo check --workspace   # rust

# 4. Run the actual app
cd ../stardust-pit && bun dev
```

Then **open a fresh Claude Code chat** in the meta-workspace and say
something like: "Resuming Stardust work, read HANDOFF.md". The
CLAUDE.md callout will guide me there automatically too.

You do NOT need to copy memory files across — the durable preferences
in this repo's CLAUDE.md + HANDOFF.md are enough. (Memory files are
mostly redundant with these now.)

## Working efficiently with Claude on this project

Token cost on a single chat compounds — every new message pays for
the whole scrollback. To stretch your usage:

- **Start a fresh chat per chunk of work** (e.g., per phase / per
  feature). HANDOFF.md is the bootstrap.
- **End a chat by asking me to update HANDOFF.md** with the new state
  before you `/clear`.
- **Don't `/clear` mid-task** without writing state to HANDOFF first.
- **CLAUDE.md's terseness directives** keep my prose minimal — don't
  remove them.
- **Be specific in requests.** "Add X to the engine" is cheaper than
  "what should we do next?" which makes me write long options menus.

## What's the plan now that v0.5 is in

**Next feature: v0.6 — wire `load_patch` / `save_patch` into the
patch editor UI.** The Rust commands exist and return structured
`PatchError`; the UI needs Open / Save buttons and a file dialog.

Starting points for the next chat:

- `stardust-pit/src/src/` — patch editor lives here. Add toolbar
  buttons that call `load_patch` / `save_patch` via Tauri's
  `invoke()`. Use `tauri-plugin-dialog` for the file picker and
  `tauri-plugin-fs` to read/write the JSON; both are already
  registered.
- `stardust-pit/src-tauri/src/commands.rs` — the existing
  `load_patch` / `save_patch` commands. The TS-side error type
  mirrors `PatchError { kind: "parse" | "validation", ... }`.
  Render parse errors as a single message; render validation
  errors as a list.
- `stardust-pit/src/src/screens/_seed-data.ts` — the TS fixtures.
  Worth doing the round-trip smoke test (devtools console) before
  wiring the UI, to confirm camelCase serialization holds.

After v0.6: **Phase 5** — engine consumes `PatchGraph` instead of
the current `StartConfig { plugin_id, midi, audio }`. Engine
walks a graph (still one plugin in v1, multi-plugin later).

Other features deferred until after the bridge + engine
integration:

- Multi-plugin / chain hosting in the engine.
- Plugin GUI hosting (window embedding — separate platform work).
- Sample-rate re-activation when cpal negotiates a different rate.
- Plugin scan caching (mtime-keyed) — see loose ends.

---

## Decisions baked in (don't re-litigate)

- **Bun, not npm.** `bun dev` runs Tauri via the JS CLI
  (`@tauri-apps/cli`), not the Rust `cargo-tauri` subcommand.
- **CLAP only for plugins** for now; VST3 deferred until there's a
  shim. `stardust-plugin`'s default features dropped `vst3`.
- **`stardust-sfz` is shelved.** sforzando (proprietary, free, has
  CLAP) replaces it. Don't proactively improve the SFZ crate.
- **sforzando has CLAP, sfizz does not.** I had this backwards for a
  while; the memory file `feedback_sforzando_sfizz.md` is the
  correction.
- **No `Co-Authored-By: Claude`** footer in commits. Ever.
- **Storybook stays as a design-iteration surface.** Real screens
  extract into `src/src/screens/*.tsx`; the `.stories.tsx` files become
  thin wrappers that import + render with fixture data from
  `_seed-data.ts`.
- **Placeholder icons in `stardust-pit/src-tauri/icons/`** are
  procedural ugly. Don't touch until real branding lands; replace via
  `bun x tauri icon source.png` then.

---

## Cross-machine continuity tips

- **Memory files** (`~/.claude/projects/-home-chase-projects-stardust/memory/`)
  are local to one machine. If you want them on the laptop, `rsync` the
  whole directory across once. They're plain markdown — no special
  format constraints.
- **This file** (`HANDOFF.md`) is the single source of truth for
  in-flight work. Update it whenever you stop mid-task; any fresh chat
  reads it and knows exactly where to resume.
- **Avoid duplicating state into chat history.** If something matters
  for next session, write it here (or into a memory) — chat scrollback
  doesn't carry across machines.

---

## Recent commits worth knowing about

- `stardust-core` `1870592` — expose `stardust-patch` via the
  umbrella `patch` feature; bump `cpal` 0.16 → 0.17 (CoreAudio
  refactor needed for macOS 26).
- `stardust-pit` `c53d30e` — v0.5 `load_patch` / `save_patch`
  commands with structured `PatchError`; `DiscoveryLock` +
  `spawn_blocking` around discovery commands to unrace CLAP
  `dlopen` from CoreAudio enumeration.
- `stardust-core` `a671e51` — stardust-patch crate (patch-graph data
  model). Per ADR-0004.
- `stardust-pit` `9cc09ed` — v0.4 engine thread + plugin-host commands.
- `stardust-pit` `57e4229` — v0.3 cleanup (untrack gen, drop v4, rename v5).
- `stardust-pit` `530ac1b` — v0.3 patch editor in the Tauri app.
- `stardust-pit` `7818cf8` — v0.2 Tauri bridge with 3 read-only commands.
- `stardust-pit` `a8d6a01` — Switched scripts to `@tauri-apps/cli`.
- `stardust-core` `54b7ad4` — Phase 1.7 CLAP host bin.
- `stardust-core` `5a31bc1` — Recursive CLAP scanner.
