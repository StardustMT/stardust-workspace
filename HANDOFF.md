# Stardust — work in progress handoff

**Last updated:** 2026-05-22 (post v0.8a always-on engine)
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

### Whole-ecosystem

- [x] All Storybook v5 patch editor work (rig-bound sources, composite
  blocks as real wire targets, zone color picker, undo coalescing,
  validation alias, MIDI Learn buttons, sustain pedal, looping, etc.)
- [x] stardustmt.github.io — marketing + docs site exists, separate cadence.

---

## Currently in flight

Nothing mid-extraction. v0.8a just shipped — engine is always-on and
follows the selected patch automatically.

Loose ends worth picking up next session:

- **Single-plugin still.** The engine walks the patch graph for the
  first `instrument.plugin` node and ignores the rest. Multi-plugin
  chain hosting (v0.8b) is the obvious next: engine takes the whole
  graph and wires audio nodes / effects / splits. Likely needs an
  ADR for the engine graph-walker abstraction.
- **Rebind glitches audio briefly.** Each patch switch fully drops the
  prior plugin then loads + activates the next. The audio thread
  pauses while CLAP init runs (varies by plugin — Surge XT is fast,
  others can take 100s of ms). Acceptable for a dev tool; needs a
  smarter strategy (preload, crossfade, or warm-pool) before live use.
  Fast click-through of multiple patches also queues serial rebinds.
- **Live device change tears down the plugin.** Changing the MIDI
  input or audio output dropdown while a plugin is running goes
  through the same `Start`-tear-down path. A dedicated
  `engine_rebind_routing` command that only swaps the cpal stream /
  midir input without reloading the plugin would be nicer.
- **Plugin GUI hosting still missing.** The PluginUIDock has a
  disabled "Open full plugin UI" button — needs CLAP GUI
  extension + native window embedding (separate platform work per OS).
- **Velocity / sustain / QWERTY on the on-screen keyboard.** Fixed
  velocity 100, channel 0, no sustain pedal source, no
  computer-keyboard mapping. Easy follow-ups; skipped to keep v0.7
  focused. Mainstage-style click-position-as-velocity is fancier
  but trivial once we want it.
- **Dirty-tracking is a dot, not a close-blocker.** Closing the app
  or opening another show without saving silently discards changes.
  Fine for the POC; add a modal confirm when this surfaces a real
  loss-of-work moment.
- **One show seeded; no "new show" or "recent shows" UI.** The store
  boots from `_seed-data.ts`; Open Show replaces. No menu to start
  fresh or jump to a recent file. Add when the workflow demands it.
- **`tsc --noEmit`** in `ui:build` fails on a pre-existing tsconfig
  project-references bug (`tsconfig.node.json` not marked composite).
  Storybook + cargo + `bun dev` all work; just `bun ui:build`'s
  type-check step trips. Predates v0.4.
- **Plugin metadata scan is eager + uncached.** Every app launch
  dlopens every installed `.clap`. `usePluginScan()` now memoises
  for the session, but a cold start still hits everything. Will
  need an mtime-keyed cache once users have large libraries.
- **cpal `DeviceTrait::name` deprecation warnings (3).** cpal 0.17
  wants `description()` / `id()` instead. Functional, just noisy.
- **No graceful shutdown** on the engine thread. The thread is
  reaped when the process exits; `EngineCommand::Shutdown` is
  defined but unused. Fine for now.
- **Storybook PluginUIDock has no plugins.** The picker calls
  `list_clap_plugins` via Tauri — outside Tauri the dropdown is
  empty. Picker still renders; just nothing to choose. Real flow
  works in `bun dev`.

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

## What's the plan now that v0.8a is in

No single mandatory next feature. Some natural candidates in rough
order of payoff vs. cost:

- **v0.8b — multi-plugin chain hosting.** Engine walks the patch
  graph beyond the first instrument and connects audio nodes,
  effects, splits. Likely needs an ADR (engine graph-walker).
  Largest of the remaining audio-path items; unlocks the rest of
  what the patch editor already lets users draw.
- **`engine_rebind_routing` command.** Today, changing MIDI input
  or audio output mid-session tears down the plugin and reloads.
  A targeted command that only swaps the cpal stream / midir input
  in place would remove the audio glitch on routing changes.
- **Plugin scan caching (mtime-keyed).** Currently `usePluginScan`
  memoises per session but every cold start dlopens every `.clap`.
  Small infra fix; gets nicer the more plugins users install.
- **Close-blocker modal on unsaved changes.** `dirty` flag already
  exists in the show store; just needs a beforeunload hook + Radix
  confirm. Small + immediately useful.
- **"New show" / "Recent shows" menu.** Show store always boots
  from `_seed-data.ts`; Open Show replaces it. UX gap once anyone
  has more than one `.stardustshow`.
- **Plugin GUI hosting.** Per-OS window embedding work. Largest
  scope; defer until the rest of the audio path matures.
- **On-screen keyboard polish:** velocity from click-Y, sustain
  toggle, QWERTY → MIDI mapping. Each is a small additive change to
  `Keyboard` + a small command-extension on `engine_send_midi`.

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
