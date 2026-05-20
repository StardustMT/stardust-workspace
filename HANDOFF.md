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

Nothing mid-extraction right now. v0.3 (port v5 patch editor into the
Tauri app) shipped: `530ac1b` on `stardust-pit`. `bun dev` now opens
the full Stardust shell — the same UI the storybook iterates on, with
client-side state.

Files added during v0.3 (already on `main`):

- `src/src/screens/_seed-data.ts` — fixtures (songs / graphs / rigs).
- `src/src/screens/patch-editor-v5.tsx` — the `PatchEditor` component.
  Named `-v5` because the legacy v4 file at `screens/patch-editor.tsx`
  is still imported by `program-patch-editor.stories.tsx`. **Cleanup
  candidate**: delete the v4 file + its story + `_demo-data.ts` once
  we're confident nothing wants the old design as reference. Three
  files, ~75 KB total.
- `src/src/screens/program-patch-editor-v5.stories.tsx` — slimmed to
  ~80 lines (was 2530).
- `App.tsx` — renders `<PatchEditor>` with the casual cold-open seed.

Loose ends from v0.3 worth fixing in the next session:

- `src-tauri/gen/` was accidentally committed. Add to `.gitignore`,
  remove with `git rm -r --cached src-tauri/gen`.
- The v4 cleanup above.
- Storybook's `_seed-data.ts` and the v5 story share names with the
  v4 leftovers (`_demo-data.ts`, `program-patch-editor.stories.tsx`).
  Once v4 is gone, drop the `-v5` suffix everywhere for cleanliness.

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

- `stardust-pit` `530ac1b` — v0.3 patch editor in the Tauri app.
- `stardust-pit` `7818cf8` — v0.2 Tauri bridge with 3 read-only commands.
- `stardust-pit` `a8d6a01` — Switched scripts to `@tauri-apps/cli`.
- `stardust-pit` `a2b7f29` — Placeholder icons.
- `stardust-pit` `7dcbe2c` — `macOSPrivateApi` config to match Cargo features.
- `stardust-core` `54b7ad4` — Phase 1.7 CLAP host bin.
- `stardust-core` `5a31bc1` — Recursive CLAP scanner.
