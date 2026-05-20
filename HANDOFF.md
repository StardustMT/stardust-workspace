# Stardust — work in progress handoff

**Last updated:** 2026-05-20
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

### `stardust-pit` (Tauri 2 app)

- [x] **v0.1 scaffold** — Tauri 2 + React 19 + Vite + Storybook + bun.
  React UI lives in `src/src/`, Rust host in `src-tauri/`. Builds via
  `bun dev` (uses `@tauri-apps/cli` JS, NOT `cargo-tauri`).
- [x] **v0.2 bridge** — Three read-only Tauri commands:
  `list_clap_plugins`, `list_midi_inputs`, `list_audio_outputs`. Wired
  to a diagnostic 3-card view in `App.tsx`. Confirmed working on
  Windows: shows real plugin / MIDI / audio device data.
- [ ] **v0.3 patch editor in the app** ← **IN FLIGHT, this is what
  we're mid-extraction on**. See "Currently in flight" below.

### Whole-ecosystem

- [x] All Storybook v5 patch editor work (rig-bound sources, composite
  blocks as real wire targets, zone color picker, undo coalescing,
  validation alias, MIDI Learn buttons, sustain pedal, looping, etc.)
- [x] stardustmt.github.io — marketing + docs site exists, separate cadence.

---

## Currently in flight

**Goal:** Port the Storybook v5 patch editor into the real Tauri app, so
`bun dev` shows the actual Stardust UI instead of the v0.2 diagnostic
view. Backed by client-side state for now — engine wiring lands later.

**File-by-file plan:**

1. ✅ `src/src/screens/_seed-data.ts` — extracted. Pure data:
   `LSOH_SONGS`, `casualPatchGraph`, `transposedSplitPatchGraph`,
   `pianoWithSendsPatchGraph`, `compositeBlockPatchGraph`,
   `DEFAULT_RIG`, `FULL_RIG`. No React imports.
2. ⏳ `src/src/screens/patch-editor.tsx` — the `PatchEditor` component
   itself. **THIS IS THE BLOCKED STEP.** The Write tool wanted me to
   Read the (non-existent) file first; that's a harness quirk. Workaround:
   `Bash: touch src/src/screens/patch-editor.tsx` to create the empty
   file, then Read it (will show empty), then Write the content.
   Contents to write: take everything from `program-patch-editor-v5.stories.tsx`
   from line 300 (Zone defaults section) through end of file (2530), with:
   - Top of file: imports preserved minus `@storybook/react` and `makeNode`
     usage (now lives in seed-data).
   - Rename `PatchEditorShell` → `PatchEditor`, **export** it.
   - Add `showName: string` + `songs: ShowOutlineSong[]` to props.
   - Inside the component, replace hardcoded `"Little Shop of Horrors"`
     and `LSOH_SONGS` references with the new props (two sites: lines
     1196 + 1199–1200 of the original file).
3. Slim `screens/program-patch-editor-v5.stories.tsx` — keep only the
   `Meta` declaration + 4 stories, each rendering `<PatchEditor>` with
   seed-data imports. ~60 lines total instead of 2530.
4. Replace `App.tsx` body with `<PatchEditor showName="Little Shop of
   Horrors" songs={LSOH_SONGS} graph={casualPatchGraph()}
   selectedPatchId="p1.1" patchName="Cold open" songName="Prologue"
   rigSources={DEFAULT_RIG} />`.
5. `bun run build-storybook` to verify, then commit + push.

**Risks for the next session:**

- After the file split, the storybook should build clean (everything
  is the same code, just relocated). If it doesn't, check imports in
  the new `patch-editor.tsx` — the four most likely missing imports
  are `makeNode` (only needed by seed-data, drop from patch-editor),
  `Story / Meta / StoryObj` (only needed by stories file).
- The hardcoded `"Little Shop of Horrors"` in `PatchEditorShell` is
  duplicated at two sites — both need replacing with the prop. Easy
  to miss the second one if you only grep once.

---

## What's the plan once v0.3 is in

Engine thread + start/stop Tauri commands so the React UI can actually
host a plugin live (basically `stardust-poc-host-clap` wrapped as a
command + GUI). That requires owning a dedicated engine thread inside
stardust-pit because `PluginInstance<H>` is `!Send` — Tauri commands
talk to it via channels.

After that: patch graph data model in `stardust-core` (ADR-0003
schema-versioned types), then persistence, then the engine starts
operating on real serialised patches instead of fake client-state.

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

- `stardust-pit` `7818cf8` — v0.2 Tauri bridge with 3 read-only commands.
- `stardust-pit` `a8d6a01` — Switched scripts to `@tauri-apps/cli`.
- `stardust-pit` `a2b7f29` — Placeholder icons.
- `stardust-pit` `7dcbe2c` — `macOSPrivateApi` config to match Cargo features.
- `stardust-core` `54b7ad4` — Phase 1.7 CLAP host bin.
- `stardust-core` `5a31bc1` — Recursive CLAP scanner.
