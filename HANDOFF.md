# Stardust — work in progress handoff

**Last updated:** 2026-05-26 (v0.8b multi-plugin chain hosting shipped; teeing up `engine_rebind_routing`)
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
- [x] **`stardust-show` crate** — show document data model (ADR-0005).
  Per-show structure: songs, patches (each inlining its `PatchGraph`),
  rig, saved blocks. Re-uses `stardust-patch::Header` rather than
  factoring a third `stardust-schema` crate. Validation walks every
  embedded patch graph and wraps errors with patch context. Schema-
  versioned (`kind: "stardust.show"`, v1). 10 tests: LSOH fixture
  round-trip + duplicate-id negatives (song/patch/block, patch ids
  unique show-wide) + wrapped-graph-error context + wrong-kind +
  newer-schema rejection.

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
  plus an `engine://status` event stream. UI exposes a diagnostic
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
- [x] **v0.6 Open Show / Save Show end-to-end.** Tauri commands
  `load_show` / `save_show` mirror v0.5's patch ones with structured
  `ShowError` (parse vs. validation, each error carrying patch
  context). UI state lifted into a Zustand show store; `PatchEditor`
  is now controlled (graph + onGraphChange), per-patch undo history
  resets on patch switch. New `ShowToolbar` in the app-shell header
  fires Open / Save flows via `tauri-plugin-dialog` +
  `tauri-plugin-fs` (filter `*.stardustshow`), with a Radix dialog
  rendering parse errors as one message and validation errors as a
  list. Capabilities grant `fs:allow-read-text-file` /
  `fs:allow-write-text-file` scoped to `$HOME` / `$DOCUMENT` /
  `$DOWNLOAD` / `$DESKTOP`. Round-trip confirmed on macOS 26 / M1:
  save → tweak → open → state restores cleanly.
- [x] **v0.7 engine consumes a `Patch` from the show store + on-screen
  MIDI playback.** `engine_start` replaced by
  `engine_start_from_patch(patch, midiInput?, audioOutput?)` — Rust
  walks the patch graph for the first `instrument.plugin` node and
  lifts its plugin choice into `StartConfig`. `instrument.plugin`
  config now carries real `{ bundlePath, pluginId, pluginName,
  pluginVendor }` (no more fictional `pluginUri`); a Radix Select
  picker on the node's Settings pane writes those keys back. Shared
  `usePluginScan()` zustand store so EnginePanel + picker share one
  scan. Engine grew a second SPSC ring + `engine_send_midi(msg)`
  command for UI-originated notes; the live-preview keyboard is now
  a click/drag-playable MIDI source (`elementFromPoint` hit-test
  during drag, pseudo-3D depressed-key look via translateY + inset
  shadow). Hardware MIDI input is now optional — "On-screen keyboard
  only" is a valid Start path. Structured `EngineStartError` with
  `noInstrumentNode | missingPluginConfig | engine` variants.
  Cleanup: v0.5's orphaned `load_patch` / `save_patch` commands
  removed in the same diff.
- [x] **v0.8a always-on engine driven by the current patch.** Start /
  Stop buttons removed from `EnginePanel`. Engine state is now a pure
  function of (current patch, plugin choice, MIDI input, audio output);
  a sync effect calls `engine_start_from_patch` whenever the patch has
  a hostable plugin and `engine_stop` otherwise. Switching patches in
  the outline rebinds the hosted plugin without user action; switching
  to a patch with no instrument node or no plugin choice silences the
  engine. MIDI input + audio output dropdowns are live now — changing
  either rebinds with the new routing. No Rust changes: the engine's
  `Start` command already tears down any prior plugin before bringing
  up the next. Drive-by fix: `tauri.ts` had `engineStartFromPatch`'s
  `midiInput` typed as `string` but Rust accepts `Option<String>` and
  the existing call already passed `null` — widened to `string | null`.
- [x] **v0.8b multi-plugin chain hosting.** Engine consumes the whole
  patch graph, not just the first instrument. Per ADR-0006: a new
  `engine_graph` module in `stardust-pit/src-tauri/` transforms the
  graph into an executable `Plan` at start time — composites are
  pre-flattened, audio DAG is topo-sorted, per-output-port stereo
  edge buffers are pre-allocated, MIDI routing tables (with zone
  filters for split-keyboard outs) are built per producing node, and
  every `instrument.plugin` loads + activates in one shot. The cpal
  audio callback now drives the Plan: drains hw + UI MIDI rings,
  iterates nodes in topo order, processes each (CLAP plugin / sine /
  EQ / mix / sink), distributes outbox events to consumers via the
  routing table. Allocation-free per block. Native DSP gained a real
  3-band stereo EQ in `stardust-dsp` (cookbook biquads — low shelf
  250 Hz, peaking mid 1 kHz Q 0.71, high shelf 4 kHz, slope 1.0);
  `instrument.sine` is wired as a native node reusing the existing
  POC synth + ADSR. `midi.transpose` shifts note numbers; `midi.mix`
  merges streams; `audio.mix` sums N stereo input pairs. Composites
  are inlined at plan-build (wires targeting `CompositeBlock` ids
  are rewritten to their promoted-port internal endpoints) and don't
  exist in the runtime repr. Hardware MIDI fans to the first
  `source.keyboard` node in the graph (other source kinds — pedals,
  wheels — are silent in v0.8b; per-source-node controller binding
  is a v0.9 concern). `EngineStatus::Running` reshaped: `plugins:
  Vec<HostedPluginStatus>` + `native_nodes: NativeNodeCounts`
  instead of singular `plugin_name`/`plugin_id`. `EngineStatus::Error`
  now carries `messages: Vec<String>` so plan-build failures (cycle
  detection, dangling composite ports, plugin load / activation
  failures, malformed EQ / transpose config) render as a list. Per-
  node soft failures (unconfigured `instrument.plugin`, plugin that
  failed to load) become `PlannedNode::Silent` and the rest of the
  plan still loads. Plan builder has 7 unit tests covering topo
  sort, cycle detection, composite flattening, zone filtering, hw-
  MIDI keyboard targeting, transpose shifts, and a realistic seed-
  shape build (keyboard zones → transpose → 2 plugins → audio.mix
  → sink). Stardust commit set: `stardust-core` gains the EQ +
  `StereoChannel` re-export; `stardust-pit` rewrites
  `engine_start_from_patch` to ship the whole graph, replaces the
  audio closure with `Plan::process`, and updates `EnginePanel` to
  render `N plugins (a, b, c) · 2 EQ, 1 mix` status summaries.

### Whole-ecosystem

- [x] All Storybook v5 patch editor work (rig-bound sources, composite
  blocks as real wire targets, zone color picker, undo coalescing,
  validation alias, MIDI Learn buttons, sustain pedal, looping, etc.)
- [x] stardustmt.github.io — marketing + docs site exists, separate cadence.

---

## Currently in flight

**Next up: `engine_rebind_routing`.** v0.8b just shipped — engine
consumes the whole patch graph, hosts multiple plugins concurrently,
and runs native EQ / mix / transpose nodes. The natural follow-on is a
targeted command that swaps the cpal stream / midir input *in place*
without tearing down the plan. With multi-plugin chains the rebuild
cost on every device change is higher than v0.8a (every plugin reloads
and re-activates), so the payoff is bigger now. Scope sketch:

- New Rust command `engine_rebind_routing(midiInput?, audioOutput?)`
  in `stardust-pit/src-tauri/src/commands.rs`. Forwards to the engine
  thread.
- Engine thread handler: if the running engine has a Plan, swap only
  the cpal output stream (or rebuild it on a new device) and only the
  midir input handle — leave the Plan, plugin instances, edge
  buffers, and MIDI routing tables untouched.
- `EnginePanel`'s sync effect should call `engine_rebind_routing`
  when only `(midiInput, audioOutput)` changed and the plan signature
  is stable; full `engine_start_from_patch` still fires when patch or
  plugin choice changes.
- Acceptance: switching headphones → speakers (or USB MIDI keyboard
  in / out) mid-session no longer produces the audible glitch caused
  by plan teardown.

Loose ends worth picking up after that (or before, if smaller fits):

- **Patch-switch latency scales with plugin count.** Each patch switch
  fully tears down the prior plan then loads + activates every plugin
  in the next. With 3+ plugins the gap is noticeable. Warm-pool /
  preload-from-next-patch is the obvious mitigation (likely its own
  ADR). v0.8a's same loose end, worse with multi-plugin.
- **Plan rebinds only on plugin-choice change.** `EnginePanel`'s sync
  effect tracks `(patchId, planSignature, midiInput, audioOutput)`
  where `planSignature` is a hash of every instrument node's plugin
  choice. Adding / removing / editing audio effects (EQ, mix) doesn't
  trigger a rebind — user has to switch patches and back. Acceptable
  for v0.8b; revisit when the editor gains live-update affordances.
- **PluginEntry leaks intentionally.** `try_instantiate_plugin`
  `mem::forget`s the `PluginEntry` so it outlives the
  `StartedPluginAudioProcessor` (clack-host's `PluginInstanceInner`
  Arc keeps the plugin alive across drops, but the entry holds the
  `dlopen` handle and must outlive everything that came from it).
  Bundles never unload across the process lifetime, even on patch
  switch. Fine for now; clean up alongside warm-pool work.
- **Live device change tears down the plan.** Same as v0.8a — fixed
  by the `engine_rebind_routing` work teed up above; moved into the
  in-flight section.
- **Hardware MIDI binds to first source.keyboard.** Other source
  nodes (pedals, mod/pitch wheels, pads, switches) exist in the graph
  but receive zero events in v0.8b — there's no UI to assign which
  hardware controller feeds which source. ADR-0006 documents this;
  per-source-node controller binding is v0.9 scope.
- **EQ crossover frequencies are constants.** The 3-band EQ uses
  low=250 Hz / mid=1 kHz Q 0.71 / high=4 kHz / shelf slope 1.0 with
  no per-band frequency editing. Acceptable — patch editor doesn't
  expose those controls. Revisit alongside any "audio.eq settings"
  panel work.
- **Plugin GUI hosting still missing.** The PluginUIDock has a
  disabled "Open full plugin UI" button — needs CLAP GUI extension +
  native window embedding (separate platform work per OS). With
  multi-plugin, the picker may want to pick *which* plugin to show.
- **Velocity / sustain / QWERTY on the on-screen keyboard.** Fixed
  velocity 100, channel 0, no sustain pedal source, no
  computer-keyboard mapping. Same as v0.7 / v0.8a.
- **Dirty-tracking is a dot, not a close-blocker.** Closing the app
  or opening another show without saving silently discards changes.
  Same as v0.6 / v0.7.
- **One show seeded; no "new show" or "recent shows" UI.** Same as
  v0.6.
- **`tsc --noEmit`** in `ui:build` fails on a pre-existing tsconfig
  project-references bug (`tsconfig.node.json` not marked composite).
  Storybook + cargo + `bun dev` all work. Predates v0.4.
- **Plugin metadata scan is eager + uncached.** Every app launch
  dlopens every installed `.clap`. v0.8b's plan builder also rescans
  on every Start to confirm bundle paths — so each patch switch
  re-walks the disk. Add mtime-keyed caching.
- **cpal `DeviceTrait::name` deprecation warnings (3).** Same as v0.5.
- **No graceful shutdown** on the engine thread. Same as v0.4.
- **Storybook PluginUIDock has no plugins.** Same as v0.7.
- **`PlanBuildError::UnknownWireEndpoint` and structural errors are
  fatal.** Today's plan builder rejects any wire pointing at a node
  id it doesn't know about. The data model's `validate.rs` should
  catch this before the engine sees it, so this is belt-and-suspenders
  — but if it ever fires in practice the UI just shows the error
  message; there's no per-wire highlight in the editor yet.

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

## Backlog after `engine_rebind_routing`

Rough payoff-vs-cost order; pick whichever fits the next session:

- **Warm-pool / preload for patch switching.** Patch-switch latency
  scales linearly with plugin count in v0.8b. Pre-loading the next
  song's patches in the background (or keeping recently-used plugin
  instances in an LRU pool) closes the gap. Likely its own ADR.
- **Per-source-node controller assignment.** Today hardware MIDI is
  hardcoded to the first `source.keyboard` node. To make pedals,
  wheels, pads, and switches actually do something, each source node
  needs to know which physical controller feeds it. UI work in the
  rig + node settings; Rust validation; ADR likely.
- **Plugin scan caching (mtime-keyed).** v0.8b made this worse —
  every plan build re-scans the disk to confirm bundle paths still
  exist. Small infra fix; matters once libraries are large.
- **Close-blocker modal on unsaved changes.** `dirty` flag exists;
  needs beforeunload + Radix confirm.
- **"New show" / "Recent shows" menu.**
- **Plugin GUI hosting.** With multi-plugin, the picker may want a
  "which plugin's GUI?" dropdown. Largest scope of the remaining
  items; per-OS window embedding work.
- **On-screen keyboard polish:** velocity from click-Y, sustain
  toggle, QWERTY → MIDI mapping. Same easy follow-ups as v0.7.
- **Live audio-fx parameter editing.** The patch editor lets users
  set EQ band gains, transpose semitones, etc., but the engine reads
  config once at plan-build time. To make these knobs feel live, the
  engine needs a `parameter_changed` command path that mutates the
  running plan without reload.

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

- `stardust-pit` `20bfeaa` — v0.8b multi-plugin chain
  hosting. New `engine_graph` module: `Plan::build(&PatchGraph)`
  produces an executable plan (flatten composites → resolve nodes →
  topo-sort audio DAG → pre-allocate edge buffers → build MIDI
  routes → load + activate every plugin → instantiate native DSP).
  `Plan::process(cpal_buf, spec)` runs the plan per audio block —
  allocation-free, drains hw + UI MIDI rings, iterates nodes in
  topo order, distributes outbox events via the routing table,
  sums sink edges into cpal output. `engine.rs` rewritten around
  the Plan; `EngineStatus::Running` gains `plugins: Vec<_>` +
  `native_nodes: NativeNodeCounts`; `EngineStatus::Error` gains
  `messages: Vec<String>`. `commands.rs::engine_start_from_patch`
  ships the whole graph; `EngineStartError` trimmed to the
  channel-closed case (plan errors come back async via status).
  `EnginePanel` renders multi-plugin status as
  `2 plugins (Surge XT, Piano) · 1 EQ, 1 mix`. 7 plan-builder
  tests including a realistic seed-shape integration test.
- `stardust-core` `8eeff2f` — 3-band stereo EQ in
  `stardust-dsp` (cookbook biquads: low shelf 250 Hz, peaking mid
  1 kHz Q 0.71, high shelf 4 kHz, slope 1.0). `StereoChannel`
  re-exported from `stardust-patch`'s top-level so consumers don't
  reach through `types::`.
- `stardust-pit` `d88b8d9` — v0.8a always-on engine. Start/Stop
  buttons removed; EnginePanel's sync effect fires
  `engine_start_from_patch` or `engine_stop` based on (current patch,
  plugin choice, MIDI input, audio output). Patch-switch rebinds the
  hosted plugin; switch-to-empty-patch silences. Live MIDI/audio
  routing changes also rebind. No Rust changes. `tauri.ts` type fix
  on `engineStartFromPatch.midiInput` (`string` → `string | null`)
  to match Rust's `Option<String>`.
- `stardust-pit` `4e42c7d` — v0.7 engine consumes a `Patch` +
  on-screen MIDI playback. `engine_start_from_patch` walks the
  active patch's graph for the first `instrument.plugin` and lifts
  its `{ bundlePath, pluginId, pluginName, pluginVendor }` into the
  engine. Radix Select picker on the node's Settings pane writes
  those keys; `usePluginScan()` zustand cache shared with EnginePanel.
  Engine grew a second SPSC ring + `engine_send_midi` command so the
  preview keyboard is click/drag-playable (elementFromPoint hit-test,
  pseudo-3D depressed-key visual). Hardware MIDI optional.
  `EngineStartError` distinguishes noInstrumentNode /
  missingPluginConfig / engine. Dropped v0.5's orphaned
  `load_patch` / `save_patch`.
- `stardust-pit` `a933d33` — v0.6 Open Show / Save Show end-to-end.
  Rust `load_show` / `save_show` commands + structured `ShowError`;
  UI state lifted into a Zustand show store; `PatchEditor` becomes
  a controlled component; `ShowToolbar` in the app-shell header
  with file dialog + error dialog. `.stardustshow` extension.
- `stardust-core` `be1eecb` — stardust-show crate (show data model).
  Per ADR-0005. Re-uses `stardust-patch::Header`; validation walks
  every embedded `PatchGraph` and wraps errors with patch context.
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
