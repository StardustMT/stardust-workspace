# Stardust Pit — v1.0 Planning Reference

> **Purpose:** This is the curated spec extract from multi-session planning conversations.
> `HANDOFF.md` carries the *decisions* (what we'll do); this carries the *reasoning + depth*
> (why, how, alternatives considered, full spec). Feature pages, ADRs, and per-version
> refinement sessions write *from* this document.
>
> **How to use this document:**
> - **Writing a feature page?** Find the feature section below; it has the full spec, rationale, and effort estimate already worked out.
> - **Starting a per-version refinement session?** Find the version section; it links to the relevant feature sections that need to be locked in for that version.
> - **Reopening a closed decision?** Find it in the Decisions Ledger; the reasoning is captured so you don't relitigate from scratch.
> - **New contributor onboarding?** Read Part 1 (vision) + the Decisions Ledger.
>
> **Maintenance:** Update this as planning evolves. If you make a v0.X refinement decision that contradicts something here, update both this doc and the relevant feature page. Sections marked `STATUS: refined` are locked-in; sections marked `STATUS: high-level` get drilled into during the version's refinement session.

---

# Table of contents

- [Part 1 — Vision + scope](#part-1--vision--scope)
- [Part 2 — Versioning + retro changelog](#part-2--versioning--retro-changelog)
- [Part 3 — Roadmap (per-version with full reasoning)](#part-3--roadmap-per-version-with-full-reasoning)
- [Part 4 — Architecture (data model, file format, engine)](#part-4--architecture-data-model-file-format-engine)
- [Part 5 — Screens (per-screen full spec)](#part-5--screens-per-screen-full-spec)
- [Part 6 — Widget catalog](#part-6--widget-catalog)
- [Part 7 — Rig component catalog](#part-7--rig-component-catalog)
- [Part 8 — Audio engineering (balance, click, transport, backing tracks)](#part-8--audio-engineering)
- [Part 9 — Show metadata model](#part-9--show-metadata-model)
- [Part 10 — Reliability (sandboxing, performance lock, validation, hot-plug)](#part-10--reliability)
- [Part 11 — Extension API](#part-11--extension-api)
- [Part 12 — Marketplace + ecosystem](#part-12--marketplace--ecosystem)
- [Part 13 — Show Control vision](#part-13--show-control-vision)
- [Part 14 — Tech landscape notes (WASM, ASIO/WASAPI, latency, hardware)](#part-14--tech-landscape-notes)
- [Part 15 — Tech debt log](#part-15--tech-debt-log)
- [Part 16 — Decisions ledger](#part-16--decisions-ledger)
- [Part 17 — Bootstrap prompt for the docs/kanban fix-it chat](#part-17--bootstrap-prompt-for-the-fix-it-chat)

---

# Part 1 — Vision + scope

## What Pit is

Pit is the **live-performance VST/CLAP host for musical theatre keyboardists and MDs**. It's the keyboard player's onstage rig: hardware MIDI → patch graph → CLAP plugins → audio outputs, with first-class theatre vocabulary (Show / Song / Patch), first-class theatre workflows (vamps / codas / transposition / cascading settings), and first-class theatre reliability (silent patch changes, plugin sandboxing, hot-plug recovery, pre-show validation).

## What v1.0 means

**v1.0 = "a working MT pit keyboardist can ditch MainStage for a real show with it."**

That gates on three things, in this order:

1. **Reliability** — the app doesn't crash mid-show, plugin crashes don't take it down, hardware unplugs don't take it down, patches load with reverb tails ringing through changes
2. **Workflow completeness** — the full 13-step user journey (splash → new show wizard → rig → program → patches → library → balance → perform layout → live) works end-to-end without dropping into developer tooling
3. **MD essentials** — tempo, click track editor, transpose, show notes, footswitch actions, backing tracks, pre-show validation, autosave

**Explicit non-goals for v1.0:**

- Sheets / multi-app ecosystem (post-Pit-v1)
- Cloud sync, marketplace, collaboration (v2.0+)
- VST3 hosting via first-party Rust host (v1.x with C++ shim is fine; pure-Rust is v2.0)
- AU hosting (tentatively v1.0 if scope allows; defer otherwise)
- Realtime WASM extensions (v2.0+)
- IP/RTSP/NDI conductor cam (USB-only for v1; richer in v2.0)
- DMX / lighting (revisit if Show Control unlocks demand)
- Velocity-curve balance measurement (v0.12 ships velocity-normalized; curve in v1.x)
- Piano roll editor for recorded MIDI (v1.x or v2.0)
- Full DAW MIDI import with parsed parts (v1.x or v2.0)

## User journey baseline (the 13 steps)

This is the canonical user flow that v1.0 must support end-to-end. Every screen and feature traces back to one of these steps.

1. Open Pit → splash with recent shows + New/Open buttons
2. New Show → wizard (metadata + optional pre-add of saved compound rig components)
3. Setup → Rig → build compound rig component (e.g., RD-2000 = 88-key keyboard + pitch wheel + mod wheel + expression pedal + footswitch + damper pedal), save as global
4. Per-component MIDI Learn — physically interact with hardware to bind MIDI channels + config (thresholds, behaviors)
5. Rig component widget editor — sub-screen with grid layout, drawing primitives, image widget — configure how the compound renders as a single Perform widget
6. Program → new song with new patch → drag rig component as controller, plugin as instrument, effects, main out → wire up
7. Per-node inspector — configure each node; live preview shows full configured controller widget (keys + wheels + sustain — excludes non-tone controllers per spec)
8. Save patch to patch library — reusable via aliases (single source of truth); show-local or global scope; per-instance name overrides (e.g., "b42. Full Strings")
9. Balance / EQ tool — measure loudness across patches, level-match intra-patch and cross-patch, set per-patch trim
10. Perform → Layout editor — drag widgets (song/patch list, dynamic text, rig component instance, volume meter)
11. Per-widget config — condensed song/patch list, dynamic text bindings (`{current.song}`, `{current.patch}`), volume meter source assignment
12. Grid editor — move/resize/rotate/reorient widgets on the live screen
13. Save show + Go Live → fullscreen reactive layout (responds to keys, pedals, wheels, volume, patch changes)

## Architectural philosophy (locked in)

These come from CLAUDE.md and don't change without an ADR:

- **UI never owns realtime.** React/Tauri IPC must never own audio scheduling or MIDI timing.
- **Core crates are UI-agnostic.** `stardust-core` doesn't depend on Tauri or React.
- **Out-of-process plugin hosting.** Plugin crashes never take down the host.
- **Protocol abstractions over raw protocols.** Apps consume Stardust abstractions for MIDI/OSC/DMX, not raw protocols.
- **Local-first, cloud-optional.** Every workflow works without a network.
- **Theatre vocabulary everywhere user-facing.** Show / Song / Patch / Sound — never Project / Track / Channel / Voice.
- **Stardust apps work standalone.** Pit must be useful without Sheets, Sheets without Pit.
- **UX scales from solo performer to full production.** Cabaret musician and regional MD use the same app.
- **Professional reliability over novelty.** The single most important property.
- **No enterprise bloat.** If a feature only makes sense for a 50-person production company, it doesn't ship.

---

# Part 2 — Versioning + retro changelog

Switched from `vX.Y-letter` to semver `major.minor.patch`. Retro mapping:

| New tag | Old tag | What shipped | Repos |
|---|---|---|---|
| v0.1.0 | v0.1 + v0.2 | Tauri 2 + React 19 + Vite + Storybook + bun scaffold. Three read-only bridge commands (`list_clap_plugins`, `list_midi_inputs`, `list_audio_outputs`). Diagnostic 3-card view. | stardust-pit |
| v0.1.1 | v0.3 | Patch editor wired in app shell. Storybook-extracted editor renders with seed data, client-side state only. | stardust-pit |
| v0.2.0 | v0.4 | First live engine. Dedicated thread, `!Send` CLAP host via clack-host, `engine_start/stop/status`, `engine://status` event stream, EnginePanel. | stardust-pit |
| v0.2.1 | v0.5 | Patch document load/save bridge with structured errors. macOS launch fix (DiscoveryLock + cpal 0.17 bump for macOS 26 CoreAudio). | stardust-pit + stardust-core |
| v0.3.0 | v0.6 | Show document load/save end-to-end. Zustand store, controlled PatchEditor, ShowToolbar, `.stardustshow` file format. ADR-0005. | stardust-pit + stardust-core (show crate) |
| v0.4.0 | v0.7 | Engine driven by Patch + on-screen MIDI playback. `engine_start_from_patch`, real plugin metadata, click/drag preview keyboard. | stardust-pit |
| v0.4.1 | v0.8a | Always-on engine reactive to current patch. Start/Stop buttons removed; sync effect drives engine state. | stardust-pit |
| **v0.5.0** | v0.8b | Multi-plugin chain hosting via `engine_graph` Plan. Native 3-band EQ + transpose + mix nodes. ADR-0006 Accepted. **← current** | stardust-pit + stardust-core |

### Going forward
- **Patch** (`x.y.Z`) — bug fixes, small tweaks, one-file polish. No exit criteria — just "the bug is fixed."
- **Minor** (`x.Y.0`) — a release with defined scope and explicit exit criteria. Each version below is a minor.
- **Major** (`X.0.0`) — v1.0 = public release. v2.0 = AU + mobile + marketplace + sync etc.

### Framing discipline
**Every version is a real release with defined scope and explicit exit criteria, not a planning convenience.** We don't ship a version unless it meets its exit criteria. The version number is meaningful.

---

# Part 3 — Roadmap (per-version with full reasoning)

This is the full per-version scope with reasoning. Use it as the source when writing the per-version roadmap doc entries.

## v0.6.0 — Engine completeness
**Size:** ~2 weeks · **Status:** 📋 next

**Why this is next:** v0.5.0 shipped multi-plugin chain hosting but left a pile of "engine handles the data but doesn't handle the edges" gaps. Per-source bindings missing, panic missing engine-side, plugin scan re-walks disk on every Start, no CI to catch regressions. This is the "engine actually feels complete" version before we move on to UI / shell work.

### In scope
- **`engine_rebind_routing`** — targeted command that swaps the cpal stream / midir input *in place* without tearing down the Plan. With multi-plugin chains the rebuild cost on every device change is high; this removes the audible glitch.
- **Per-source-node hardware MIDI binding** — pedals, wheels, pads, switches, knobs, faders. Today hardware MIDI fans only to the first `source.keyboard` node. Each source node needs to know which physical controller feeds it.
- **Engine-level Panic command** — all-notes-off + sustain-off broadcast on every channel. UI button currently has no engine support; first stuck note in a real venue is a liability.
- **Plugin scan caching (mtime-keyed)** — every Plan build today re-walks the disk to confirm bundle paths. Cache by mtime. Background rescan.
- **Button/switch rig component** — new primitive in the rig catalog. Configurable action: Next Patch / Prev Patch / Jump to Patch / Panic / Tap Tempo / Start Transport / Stop Transport / Toggle Bus Mute / Send MIDI Message / Custom Macro. Replaces hardcoded "footswitch actions" concept. MIDI-learnable to any hardware.
- **Plugin GUI hosting (basic)** — CLAP GUI extension + native window embedding per OS (NSView on macOS, HWND on Windows, X11/Wayland on Linux). Floating Window per plugin. PluginUIDock currently disabled; this enables it.
- **Learn Master tool** — new Setup → Re-learn All sub-screen. Lists every learnable field in every rig component in the show. One-button "Start re-learn" walks through each field sequentially, prompts user to interact with hardware, captures the new binding. Skip/back per field. Diff view at end ("These bindings changed: ..."). Save or cancel. Useful for: new machine, new keyboard, sharing show with someone, swapping rigs between gigs.
- **Default Windows audio = WASAPI Exclusive** — surface ASIO when available, WASAPI Shared as fallback. Support separate input/output devices (no ASIO single-device limit). See Part 14 ASIO/WASAPI deep dive.
- **Sine synth → `instrument.testtone`** — rename and hide from user-facing catalog. Exposed only via "Run engine self-test" diagnostic in Settings. Sine has been useful for "does my engine work" testing; doesn't belong as a user-facing default once SFZ player lands.
- **GitHub Actions PR CI** — Rust (cargo check + clippy + fmt + test), TS (eslint + prettier + tsc + vitest), Storybook build verification. macOS + Windows + Linux runners. Required-status-check on PRs.
- **Tech debt cleanup**: fix `tsc --noEmit` (tsconfig project-references bug), delete orphaned `sound/` components.

### Exit criteria
- Live device change has no audible glitch
- Pedals/wheels/pads/switches produce events end-to-end
- Engine-level Panic works (verified with stuck-note test)
- Patch switch doesn't re-scan disk
- Footswitch advances patches via the new button/switch rig component
- PR CI runs green on all three platforms
- Learn Master walks every learnable field and successfully rebinds

## v0.7.0 — Plugin sandboxing (out-of-process)
**Size:** ~6 weeks · **Status:** 📋

**Why this is next:** CLAUDE.md says "Out-of-process plugin hosting" is a hard rule. Currently violated (everything runs in-process via clack-host). Without sandboxing, a single buggy CLAP plugin can bring down the host mid-show — the single worst thing that can happen in live performance. This is the biggest architectural gap between "demo" and "Broadway-grade."

### In scope
- **Out-of-process plugin processes** — each plugin (or small group sharing memory) runs in a child process. Shared-memory ring buffer for IPC. Sub-millisecond IPC latency.
- **Watchdog supervisor** — monitors engine; can restart if engine deadlocks. UI keeps running; engine cycles in <500ms.
- **Plugin crash detection + recovery** — engine detects disconnect on next callback → all-notes-off all channels → either restart plugin or fall back to silence + sustain-off → UI notification toast → quarantine if crashes twice in same session.
- **Hot-plug resilience** — USB MIDI / audio device disconnect handled gracefully. Detect via CoreAudio Property Listeners (macOS) / WASAPI device notifications (Windows) / udev (Linux). Mute affected channel. UI warning toast. Attempt reconnect on device reappearance. Auto-resume on reconnect.
- **Performance Lock mode** — single toggle ("Go Live" / "End Show") that disables file ops, plugin scanning, allocation-heavy ops, and accidental edits during a show.
- **Show plugin requirements tracking** — show has computed `requiredPlugins: PluginRequirement[]` field, derived by walking all patches. On show load, compare required vs available. Patches with missing plugins:
  - ⚠️ icon on patch name in outline
  - ⚠️ icon on the plugin node in the graph
  - Plugin node renders greyed out + dashed border
  - Hover/click → tooltip with `pluginName · pluginVendor · bundle path expected at: ...`
  - "Find this plugin" button → uses CLAP `plugin.url` field → opens plugin homepage in default browser
  - Graph node never removed — fully preserved for when the plugin is available again
- **4-hour soak test in CI on macOS + Windows** — asserts no audio dropouts, no memory growth, no CPU drift, no file handle leaks, all notes properly cleaned up at end. Every release branch must pass before tagging.
- **ADR-0002 → Accepted** (currently Proposed; this is what fulfills it).

### Exit criteria
- Killing a plugin process mid-playback doesn't crash app; audio resumes within 500ms
- USB MIDI hot-plug recovers seamlessly (verified test)
- 4-hour soak test passes on both platforms
- Performance Lock blocks edits during Live
- Missing-plugin warnings render correctly on a synthetic show file referencing nonexistent plugins
- ADR-0002 moves Proposed → Accepted

## v0.8.0 — Transport + MD essentials
**Size:** ~4 weeks · **Status:** 📋

**Why this is next:** Sandboxing made plugins safe; now we make the engine MD-aware. Tempo, click, transport, MIDI clock — foundations for backing tracks (later) and the click track editor (later).

### In scope
- **Per-song + per-bar tempo** — drop master-show BPM. Tempo lives on Song. Bar-by-bar tempo is the Click Track Editor's job (v0.12).
  - Song has `defaultBpm` + `timeSignature` + `clickTrack` (optional)
  - If `clickTrack` exists, it overrides `defaultBpm` per bar
  - Patch has optional `tempoOverride` (Advanced — rarely used; for "this patch is half-time")
- **Engine transport state** — `stopped | playing | paused | position`. Exposed via Tauri event stream.
- **Click track engine node** — generates click samples per current tempo. Routes to a dedicated bus output (typically drummer's IEM).
- **MIDI clock send** — sync external rigs (drummer's drum machines, sequencers). Song-level, follows transport BPM.
- **Tap tempo via button/switch rig component** — already a button/switch action from v0.6.0; this version makes the engine consume it.
- **Per-patch transpose UI surface** — data model already supports; surface in patch inspector + outline.
- **Pre-show validation engine command + dashboard** — checks: all plugins load, MIDI devices present, audio device matches, sample rate matches, no parameter mappings reference missing plugins, disk space, CPU baseline, no quarantined plugins. Green/yellow/red dashboard. Override-able with confirm before entering Live.

### Exit criteria
- Click plays per-song with correct tempo + visual indicator
- Pre-show validation surfaces all 8+ check categories
- MIDI clock syncs an external rig (verified test)
- Tap tempo works from a footswitch
- Per-patch transpose UI works end-to-end

## v0.9.0 — Three-mode shell + splash + wizard + settings
**Size:** ~3 weeks · **Status:** 📋

**Why this is next:** The engine is now MD-ready. Now make the app shell that users actually open. Today App.tsx renders one screen (Patch Editor); this version wires the three-mode shell + splash + wizard + settings.

### In scope
- **ModeSwitcher wired into App.tsx** — Setup / Program / Perform. Persists last-active mode per show.
- **Splash screen** — pre-shell screen with:
  - Recent shows list (last N, mtime-sorted, with venue + last-opened timestamp)
  - New Show button → wizard
  - Open Show button → file picker
  - Settings shortcut
  - App version + update-check status
  - "What's new" panel on first launch after update (with "Don't show again" checkbox)
- **New Show wizard** — Modal. Full spec in Part 5.
- **Settings** — floating Window (not in-shell screen). Sections: Audio I/O, MIDI, Plugin scan paths + manual rescan, Theme, Autosave, Telemetry + crash reporter (opt-in), Keyboard shortcuts. See Part 5.
- **Setup → Show Settings screen** — metadata edit, buses (FOH, IEM-click, IEM-band, etc.), master controls, autosave interval, master volume + global panic key binding.
- **Production-version metadata structure** — handles revivals. See Part 9.
- **Native file menu** — File / Edit / View / Window / Help. NO mode switches in menu bar. File: New Show / Open Show / Open Recent ▸ / Save / Save As / Export to Bundle / Quit. Window: Settings / Plugin GUI ▸ / Live Mode.
- **Autosave** — opt-in checkbox in wizard, default on. Interval: 1m / 5m / 15m / on-blur.
- **Close-blocker on unsaved changes** — replaces the dirty dot. Modal with Save / Discard / Cancel.
- **Theme picker** — Light / Dark / System defaults. Full editor with color pickers + contrast checker in v0.15.0.
- **Concept doc rewrite** — delete `edit-vs-live`, add `setup-program-perform`.
- **Song page renders in patch-canvas area** when a song is selected in outline. Tabs: Settings / Click / Backing / Patches. (Click + Backing tabs are placeholders until v0.12 + v0.13.)

### Exit criteria
- A user can launch Pit, see recent shows, create a new show via wizard, configure it in Setup, program in Program, see layout editor in Perform
- Autosave runs at configured interval
- Closing with unsaved changes prompts
- Native file menu populated with all standard items
- Production-version metadata renders + persists correctly
- Concept doc rewrite landed; old edit-vs-live doc deleted

## v0.10.0 — Library + reuse + drawing + Pit Mixer
**Size:** ~5 weeks · **Status:** 📋

**Why this is next:** The shell is wired; now we make programming a real show feel right. Library/reuse is the difference between "I can build a 1-song demo" and "I can build a 30-patch show without losing my mind." Pit Mixer addresses the silent-pit/IEM use case that's a MainStage gap.

### In scope
- **All-patches-as-references model** — see Part 4 data model.
- **Library scope: show-local vs global** — single `scope: "show" | "global"` field on library entries.
- **Reference overrides** — Basic (name, notes, tempo, transpose, trim, color, tags) shown by default; Advanced (MIDI channel offset, bus routing override, plugin param overrides, FX bypass, on-enter/exit triggers, custom CSS class) collapsed.
- **Graph edit merge UI** — editing a shared patch's graph triggers a save dialog: "Save changes to global 'Full Strings' (affects 3 other uses)?" Lists other uses with dropdowns: Update / Keep / Three-way merge. Three-way merge view (per-node diff): shows base / source-edit / instance-overrides side-by-side, user picks per change. "Always update silently" checkbox becomes per-show preference.
- **Orphan handling** — library entry deletion sweeps all open shows' references, populates `orphan.snapshot` field on each ref with last-known graph. Reference becomes self-contained. Outline shows broken-chain icon. Banner with: Re-link to existing / Save as new global / Save as show-local / Keep as orphan.
- **Rig component widget editor** — sub-screen inside Setup → Rig. Grid editor (move/resize/rotate/z-order). Drawing primitives (box, line, divider with configurable weight/color/style: solid/dotted/dashed). Image widget. Snap-to-grid default on, toggleable.
- **`source.compound` node kind** — drag a saved rig component into a patch as a single node. Replaces today's individual primitive sources where the user wants a unified controller.
- **Live preview shows configured controller widget** — when a patch contains a `source.compound`, the patch editor's live preview renders the full configured controller (keys + wheels + sustain — explicitly excludes non-tone controllers like footswitch and expression).
- **Pit Mixer screen** — Program → Pit Mixer. Multi-channel audio input (USB multitrack only for v1.0; Dante/AVB v2.0+). Per-channel meter / gain / pan / mute / solo. MD's custom mix outputs to MD's IEM bus. State persisted per-show. See Part 5.
- **Visual regression CI** — Storybook via Chromatic or Percy. Catches accidental widget visual breakage.

### Exit criteria
- A user can save a patch globally, use it in multiple songs with per-instance name overrides
- A user can save a compound rig component globally
- Edit a globally-shared patch → merge UI surfaces correctly across multiple uses
- Delete a global patch → references in open show orphan with snapshot intact
- Rig component widget editor renders + persists per-component layout
- Pit Mixer screen shows N USB inputs from a connected mixer, per-channel controls work
- Visual regression CI runs on every PR

## v0.11.0 — Perform mode + widgets + conductor cam
**Size:** ~4 weeks · **Status:** 📋

**Why this is next:** Programming is solid; now we build the user's home screen. Perform mode is the actual deliverable for the keys player on stage. Everything before this is preparation; this is the payoff surface.

### In scope
- **Layout editor wired into App.tsx** — was Storybook-only.
- **Grid editor** — move / resize / rotate / z-order. Snap-to-grid default on, toggleable.
- **Global default layout + per-song override layouts** — cascading inheritance. Global default applies to all songs; per-song override replaces it when active.
- **Full widget catalog** — see Part 6 for every widget with spec.
- **All MIDI widgets reactive in Live** — keyboard widget shows pressed keys live; pedal widgets show position; wheels show position; volume meter shows live RMS; transport shows playhead; engine monitor updates per-block.
- **Live fullscreen mode** — renders the active layout (global or per-song). No hard-forced widgets — user-placed everything. Pre-show validation gate before Live (override-able with confirm).
- **Layout templates** — Blank, Minimal (song/patch list + dynamic text + volume + drawn placeholder), Cabaret (text-heavy), MD Console (multi-output meters + transport-heavy). Seed sensible starting layouts.
- **Conductor cam widget** — USB webcam only for v1.0. Settings: device pick, mirror toggle (POV cams sometimes flip), aspect ratio, crop, audio mute (always — analog cams sometimes have mics you don't want). Pop-out as floating Window for second-monitor display. Capture-card support works automatically via UVC abstraction (document, don't build dedicated UI).
- **Conductor cam overlay info** — toggleable per-element: song name, patch name, next-patch preview, bar number (when click active), beat indicator, tempo, time signature, show clock + splits, custom static text, custom dynamic text with bindings, watermark. Position (corner / free / edge banner), background (solid / semi-transparent / none), font size + family + weight + color, outline / drop-shadow for varied video readability, visibility rules ("only when changing patch" / "always" / "during click").

### Exit criteria
- A user can build a layout in Perform editor, hit Go Live, see widgets respond reactively to hardware
- Per-song layout overrides work
- Layout templates seed a usable starting point
- Conductor cam widget displays a USB webcam feed
- Overlay info renders on cam feed with correct binding semantics
- Pre-show validation gates Live entry

## v0.12.0 — Click track editor + balance tool
**Size:** ~4 weeks · **Status:** 📋

**Why this is next:** Perform mode works. Now we ship the two big MD-specific features: a proper click track editor (with bar-by-bar tempo, vamps, rits/ralls) and the balance tool (LUFS measurement, cross-patch level matching). Both are differentiators vs MainStage.

### In scope
- **Click track editor** — see Part 8 for full spec. Key points:
  - No bake step (data-driven, always-live)
  - Tempo curve graph with manual point editing
  - Bar-by-bar BPM; numeric / note=BPM / musical term input
  - Vamps, repeats, codas, cue points
  - Rits/ralls via region selection
  - Audition with playhead scrub
  - SMF Type 1 export/import (tempo + bar markers + cue points; vamps/repeats encoded via our marker naming)
- **Balance tool** — see Part 8 for full audio engineering breakdown. Key points:
  - LUFS measurement (`ebur128` Rust crate)
  - Offline render — no speakers needed (silent measurement via engine `RenderMode::Offline`)
  - Intra-patch (per-instrument-node)
  - Cross-patch (within song)
  - Show-wide audit
  - True Peak + Loudness Range + Integrated LUFS
  - Velocity-normalized at v80 for v1.0 (3-point curve at v40/v80/v120 in v1.x)
  - Per-patch trim suggestions + manual override
  - Tilt EQ per patch (single-knob low/mid/high)
  - A/B compare against reference patch

### Exit criteria
- Click track editor produces engine-readable tempo data; engine plays correct click + advances bar counter
- SMF roundtrip works (export from Pit → DAW shows correct tempo + markers; reimport reconstructs vamps via our marker naming)
- Balance tool measures all patches in a show offline (silent)
- Cross-patch level audit surfaces "Patch X is +N LU from median"
- Per-patch trim adjustments persist + apply at runtime

## v0.13.0 — Backing tracks + bundle file format
**Size:** ~5 weeks · **Status:** 📋

**Why this is next:** Click is live, balance is solid. Now we add backing tracks — the second-biggest MainStage-gap after sandboxing. This is what makes Pit viable for the 80% of MT cabarets / tours / school productions that use backing tracks for orchestral parts the live band can't cover.

### In scope
- **Audio file decoding** — symphonia (mp3 / wav / flac / ogg) into ring buffers.
- **Per-song tracks tab** — file, label, stem type (click / guide / orchestral / vocal / fx / custom), bus output assignment, gain, pan, mute, start offset.
- **Song transport** — play/pause/stop/seek/position. Independent of patch navigation by default.
- **Cue points within tracks** — for jump-to-section (vamp / chorus / bridge).
- **Patch transport triggers** — optional `transportTriggers` per patch: `onEnter: "none" | "play" | "pause" | "stop" | "jumpToCue:<cueId>"`, `onExit: "none" | "pause" | "stop" | "fadeOut:<ms>"`. Off by default; opt-in per patch.
- **Vamp interaction with transport** — vamp regions defined in click track. When transport enters a vamp region, it loops that region. Footswitch press signals "end vamp at next loop point" — track finishes current loop, transitions out. Patches can be tied to "exit vamp" event for auto-advance.
- **MIDI clock sync to transport BPM** — song-level (not per-track).
- **Sample-accurate cue jump** — decode forward seek.
- **Bundle file format migration** — `.stardustshow/` folder with extension. Contains `show.json`, `libraries/`, `assets/audio`, `assets/images`, `assets/samples`, `thumbnails/`. Opt-in `.zip` export for sharing. Schema migration from v1 single-JSON to v2 bundle.
- **MIDI recording + audio bounce** — captures MIDI input live, plays through patches, renders to audio file. No piano roll editor (v1.x). Enables MDs to create their own backing tracks within Pit by playing the orchestra parts.
- **Detailed UX refined during v0.13.0 spec session** — transport state machine, vamp transition behavior, cue-point UX details.

### Exit criteria
- A user can drop in stems for a song (click + orch + guide), assign each to a bus
- Configure first patch to start transport on enter; hit it live; hear playback synced and routed correctly
- Vamp interaction works: footswitch press during a vamp completes current loop, transitions to next section
- Bundle format migration: load a v1 .stardustshow file → save as v2 → reload → identical
- MIDI recording + bounce produces a usable audio track from a live performance

## v0.14.0 — Native SFZ player
**Size:** ~2 weeks · **Status:** 📋

**Why this is next:** Backing tracks ship; the audio file decode plumbing is built. Now we add native SFZ playback (a node in the patch graph, not a standalone CLAP — sforzando exists for that). This establishes the foundation for the v2.0 custom sampler + future marketplace SFZ packs.

### In scope
- **Native `instrument.sfz` node** in `stardust-core` — runs in-process like the testtone synth does.
- **SFZ 1.0 opcode support** minimum; key 2.0 opcodes for future sampler.
- **Bundled GM piano SFZ** (~3MB sample set) auto-loads as default when `instrument.sfz` node is added without a file.
- **Per-node settings panel** — load SFZ file, polyphony limit, output gain.
- No standalone CLAP build — sforzando already exists; users who want CLAP use that.

### Exit criteria
- A user can drag an SFZ file into an `instrument.sfz` node, hear it
- Default-load works: drop in node without picking file, get bundled GM piano
- Ships with the install bundle

## v0.15.0 — Polish + extension API + release CI
**Size:** ~4 weeks · **Status:** 📋

**Why this is next:** Functionality is done. Now we make it shippable: onboarding, accessibility, signed installers, demo shows, the extension API as a v1.0 launch differentiator.

### In scope
- **Onboarding tour** — first-launch wizard + welcome tour
- **Theme editor** — full color picker for every CSS token, contrast checker (fails sub-AA themes; warned but can be saved with user override), save/share themes as files
- **Performance profile pass** — verify smooth on a 4-year-old laptop
- **Accessibility audit** — all v1.0 surfaces pass WCAG 2.2 AA, full keyboard nav, screen reader (semantic HTML + ARIA), focus indicators, reduced-motion respected, color-blind safe palettes
- **Signed/notarized installers** — macOS DMG (notarized), Windows MSI/EXE (signed), Linux AppImage (best-effort)
- **Release CI/CD pipeline** — tag-triggered: build → signed artifacts → GitHub Releases → auto-update manifest publish. Release notes generation from PR labels.
- **Crash reporter** — opt-in. GlitchTip (self-hosted Sentry-compatible) or Sentry direct.
- **Telemetry** — anonymous, opt-in, aggregate-only (Plausible-style).
- **5 demo shows bundled** — Pirates of Penzance, HMS Pinafore, Mikado, one community-contributed, one tech-demo (showcases cue system + multi-patch song + click + transpose).
- **Documentation site full coverage** — every shipping feature documented with screenshots/GIFs. Getting Started guide. FAQ. Troubleshooting. Compatibility matrix.
- **Tutorial videos** — 3–5 short YouTube screencasts covering key concepts.
- **Extension API v1** — hybrid TypeScript + WASM, non-realtime. UI widgets, file importers/exporters, custom commands, hardware controllers. See Part 11.
- **ADR-0007** — Extension API architecture
- **Stream Deck support** as bundled example extension — first-party demo of the extension API. Maps Stream Deck buttons to show navigation actions (Next Patch / Prev / Panic / specific patch).
- **Latency Budget doc** — `/docs/pit/reliability/latency-budget.md`. Per-API latency floor, hardware recommendations, what's improving. See Part 14.
- **Tech debt sweep** — anything not naturally cleaned by another version. Cleared or explicitly deferred.

### Exit criteria
- Installers signed and notarized; download → install → launch → first run succeeds on a clean machine
- Demo shows bundle and load cleanly
- Docs site covers every shipping feature
- Accessibility audit passes
- Extension API allows a hello-world extension to ship a widget + import file format
- Stream Deck extension works end-to-end
- Tech debt list either resolved or explicitly deferred

## v1.0.0 — Public release
**Size:** ~2 weeks beta + launch · **Status:** 📋

**Why this is the bar:** Cross-platform public release with stable build, demo shows, community channels, signed distribution.

### In scope
- **Open beta** — 10–20 friendly MDs/keyboardists, 2–3 week window
- **Discord server** live, GitHub Discussions organized
- **Beta feedback addressed or triaged**
- **Public launch announcement**
- **Auto-update mechanism** via Tauri's built-in updater
- **Build pipeline auto-publishes** to GitHub Releases on tag

### Exit criteria
- A 1.0.0 build is publicly available on macOS + Windows + Linux
- Site is live with full documentation
- 5 demo shows ship with the app
- Discord active
- Public launch announcement made
- Tag triggers release publish

## v1.x — Post-launch backlog
- Velocity-curve balance measurement (3-point at v40/v80/v120)
- Piano roll editor for recorded MIDI tracks
- Plugin library UX polish (vendor grouping like "Surge XT" + "Surge XT Effects" → "Surge", favorites, tags, search)
- Full DAW MIDI import (multi-track SMF → click + per-instrument tracks parsed as backing)
- Layout templates expansion
- AU plugin hosting (if not in v1.0)

## v2.0+ — Major backlog
See Part 16 for full list. Highlights:
- Pure-Rust VST3 host (`stardust-vst3` extracted)
- Pure-Rust AU host
- Realtime WASM extensions
- Marketplace + Cloud sync + Collaboration
- Show Control (MSC / OSC / Art-Net / sACN / LTC / MTC — Stardust as ecosystem hub)
- Mobile companion, hot-spare rig, multi-keyboardist sync
- Custom sampler, AI sound search

---

# Part 4 — Architecture (data model, file format, engine)

## Data model — all-patches-as-references

**The decision:** every patch in every song is a reference to a library entry. There is no "inline patch" type. Single data model, single code path, single UX flow.

### Why this won

Without it (mixed model):
- Some patches are inline (defined in the song), some are references (point at library)
- Two data types, two code paths, two UX flows
- Save scope (show vs global) requires "promoting" an inline patch to a library entry
- Aliasing requires checking "is this a ref or inline?" everywhere
- File format handles both shapes
- Editing UX differentiates between source and call-site
- Sharing has to decide which patches to bundle

With it:
- Every patch lives in a library entry (show-local or global)
- Every patch in a song is a reference to a library entry
- "New patch" creates both a library entry (show-scope, "Untitled Patch") and a reference at the same time
- "Save to global" flips a `scope: "show"` field to `scope: "global"`. No restructure.
- "Duplicate" creates new library entry + reference (no shared history)
- One UX flow

### Storage

```
~/.stardust/library/
├── patches/
│   ├── 8e3f-9c2a.json         # one file per library entry, named by uuid
│   ├── 4a1c-7d8e.json
│   └── ...
├── rig-components/
│   ├── 2b9d-1f4e.json
│   └── ...
└── blocks/
    └── ...
```

```
my-show.stardustshow/
├── show.json                  # references library entries by id
├── libraries/
│   ├── patches.json           # show-scoped library entries
│   ├── rig-components.json
│   └── blocks.json
├── assets/
│   ├── audio/                 # backing track stems
│   ├── images/                # logos, conductor cam overlays
│   └── samples/               # SFZ files, recorded samples
└── thumbnails/                # cached widget previews
```

### Library entry shape

```ts
LibraryPatch {
  id: "8e3f-9c2a",              // uuid, unique
  scope: "show" | "global",
  name: "Full Strings",
  graph: PatchGraph,
  defaults: {
    tempo?: number,
    transpose?: number,
    trim?: number,             // dB
    notes?: string             // markdown
  }
}
```

### Reference shape

```ts
PatchRef {
  refId: "ref-12",              // unique within show
  libraryId: "8e3f-9c2a",       // points at library entry
  overrides: {
    // Basic overrides (shown by default in inspector)
    name?: string,
    notes?: string,
    tempo?: number,
    transpose?: number,
    trim?: number,
    color?: string,             // outline visual differentiation
    tags?: string[],
    // Advanced overrides (collapsed by default)
    midiChannelOffset?: number,
    busRoutingOverride?: BusRouting,
    pluginParamOverrides?: Record<string, number>,
    fxBypassOverrides?: string[],
    onEnterTrigger?: TransportTrigger,
    onExitTrigger?: TransportTrigger,
    customCss?: string
  },
  orphan?: {
    snapshot: PatchGraph,
    lostAt: timestamp
  }
}
```

### Resolution

- At show-open: walk show's `libraries/` first, then user's global `~/.stardust/library/`
- For each `PatchRef`: look up `libraryId` in resolved library
- If found: render with overrides applied (basic resolution: `displayName = ref.overrides.name ?? library.name`, etc.)
- If not found: check `orphan.snapshot`; render from snapshot with orphan banner; if absent (defensive), render error state

### Patch instance UX

- Outline: aliased patches show "Instance of 'Full Strings'" label, small chain icon
- Patch editor with shared patch open: banner "Shared — N instances. Graph edits trigger merge UI."
- Settings sections: Basic overrides visible; Advanced overrides collapsed but expandable
- All settings pre-populated from library defaults; user edits override only that field
- No explicit "detach" command — simpler UX
- Outline rename of reference → updates `name` override only (e.g., "Full Strings" library + "b42. Full Strings" instance)

### Graph edit propagation (merge UI)

When user saves changes to a globally-shared patch's graph:

- Modal: "Save changes to global 'Full Strings'?"
- Lists other uses (instances) with checkboxes per instance
- Per instance, dropdown: "Update this instance" / "Keep current" / "Three-way merge"
- Three-way merge view (per-node diff): shows base / source-edit / instance-overrides side-by-side, user picks per change
- "Always update silently" checkbox at bottom (becomes per-show preference)

### Orphan handling

When user deletes a library entry:
- System sweeps all references in all open shows + all show files known to it
- For each reference, populate the `orphan.snapshot` field with the last-known graph
- Reference is now self-contained (functional but disconnected)
- Outline icon: broken chain
- Patch editor banner: *"This patch references 'Full Strings', which was deleted. Frozen at last edit."*
- Buttons:
  - **Re-link to existing** → pick another library entry, copies graph from there
  - **Save as new global** → creates new global library entry from snapshot, re-points
  - **Save as show-local** → creates new show-scoped library entry, re-points
  - **Keep as orphan** → no action, ref keeps its snapshot
- Across-show orphan detection limited to open shows. If deleted global patch + show opened 6 months later, show's open-flow detects missing libraryId and populates orphan.snapshot on open (lazy orphaning).

### Sharing model

When you save/export a show:
- Walk show's references, find all global library entries used
- Snapshot them into show's `libraries/patches.json` (scope="show", with `derivedFrom: "global-id"` marker)
- Receiving user can: use as-is (snapshots stay show-local) OR "Import to global library" (copies snapshots into their `~/.stardust/library/`, re-points refs to global ids)

## File format — bundle structure

**Decision:** `.stardustshow/` is a folder (with extension). Industry-standard pattern (matches Logic `.logicx`, MainStage `.concert`, Ableton `.als` is a single-file outlier).

**Why folder over single JSON or SQLite:**
- Assets first-class, no base64-in-JSON bloat
- Streaming asset loads (don't load all backing tracks at startup)
- Easier marketplace packaging
- Compatible with git LFS for version-controlled shows
- macOS treats bundles as files visually but folders structurally
- Same file size as a zip if you tar+gzip for distribution
- Human-readable in editor (vs SQLite opacity)
- CRDT-friendly (individual files sync independently for future cloud sync)

**Bundle vs gzipped XML (Ableton style):** Ableton's monolithic gzipped XML is slow to parse for large projects and impossible to selectively load. Bundle wins.

**Bundle vs SQLite:** SQLite is good for incremental saves and queries but opaque, doesn't handle binary assets gracefully, harder to debug. Bundle wins for Pit's audience.

### Bundle contents

```
my-show.stardustshow/
├── manifest.json              # show metadata, schema version, required plugins, asset index
├── show.json                  # the show graph (songs, patches, rig, layouts)
├── libraries/
│   ├── patches.json
│   ├── rig-components.json
│   └── blocks.json
├── assets/
│   ├── audio/                 # backing tracks
│   ├── images/                # show logo, conductor cam overlays
│   └── samples/               # SFZ files, recorded samples
└── thumbnails/                # cached widget previews (optional)
```

### Export

- Default save: bundle as folder
- Opt-in: "Export to single file (.zip)" for emailing / marketplace upload
- The .zip is a tar+gzip of the bundle with extension `.stardustshow.zip` or similar

### Linux note

Linux file managers don't natively recognize bundle-as-file. Document `xdg` mime registration or just live with "looks like a folder on Linux."

## Engine architecture (current as of v0.5.0)

Already shipped:

- **`engine_graph` Plan model** (ADR-0006). `Plan::build(&PatchGraph)` produces an executable plan: flatten composites → topo-sort audio DAG → pre-allocate edge buffers → build MIDI routes → load + activate every plugin.
- **`Plan::process(cpal_buf, spec)`** runs per audio block. Drains hw + UI MIDI rings, iterates nodes in topo order, processes each (CLAP plugin / native sine / 3-band EQ / mix / sink), distributes outbox MIDI events to consumers via routing table.
- **Allocation-free per block**. RT-safe.
- **Per-output-port stereo edge buffers** pre-allocated.
- **MIDI routing tables** (with zone filters for split-keyboard outs) built per producing node.
- **Soft failures**: per-node failures become `PlannedNode::Silent`; rest of plan still loads.

Coming:
- **v0.6.0**: `engine_rebind_routing` (swap stream without rebuild), per-source binding, engine Panic
- **v0.7.0**: Out-of-process plugin processes via shared-memory IPC
- **v0.8.0**: Engine transport state (stopped/playing/paused/position), click engine node, MIDI clock send

## Architectural rules (durable)

- **UI never owns realtime.** React/Tauri IPC must never own audio scheduling or MIDI timing.
- **Realtime paths allocation-free.** Audio callback, MIDI dispatch, etc. must not allocate or lock.
- **`!Send` plugin instances pinned to one thread.** clack-host's `PluginInstance<H>` is `!Send`; engine thread is the only one that touches plugins.
- **Out-of-process plugin processes** (v0.7.0+): each plugin runs in a child process; shared-memory ring buffers; sub-ms IPC latency.

## Crate organization

**Decision:** stay flat workspace. Current layout:

```
stardust-core/
├── Cargo.toml             # workspace root
└── crates/
    ├── stardust-audio/
    ├── stardust-midi/
    ├── stardust-dsp/
    ├── stardust-patch/
    ├── stardust-show/
    ├── stardust-plugin/
    └── stardust-rt/
```

Group by naming convention (`stardust-audio-*`, etc.) if family grows. Don't introduce nested workspaces until past ~15 crates. Most large Rust projects (tokio, axum, bevy) stay flat.

---

# Part 5 — Screens (per-screen full spec)

Surface types:
- **Screen** = full-area, mode-switched
- **Window** = floating, OS-window, can be moved/resized independently
- **Modal** = blocks parent until dismissed
- **Inline** = lives inside a screen as panel/sidebar/inspector

## Splash (Screen — pre-shell)

**Purpose:** entry point when Pit launches without an active show.

**Contents:**
- Recent shows list (last N, mtime-sorted, with venue + last-opened timestamp)
- "New Show" button → opens New Show wizard (Modal)
- "Open Show" button → native file picker
- "Settings" shortcut → opens Settings (Window)
- App version + update-check status
- (Optional, low priority) "What's new" panel for release notes on first launch after update — with "Don't show on next launch" checkbox

**v0.9.0**

## New Show Wizard (Modal)

**Purpose:** guided show creation. Six steps, all skippable except step 1.

### Step 1 — Show metadata (required)
- Show name
- Subtitle / production type (optional)
- Venue (optional)
- Dates: start, end, opening, closing (all optional)
- Music director credit (optional)
- Keys / instrument credit (optional)
- Show notes (markdown, optional)

### Step 2 — Audio I/O
- Output device dropdown (auto-detect, smart default = system default)
- Sample rate (auto / 44.1k / 48k / 96k)
- Buffer size (auto / 64 / 128 / 256 / 512)
- Test tone button → plays 1 kHz @ -18 dBFS to verify
- "Configure buses now or later" — defer to sub-wizard; default = single stereo bus "Main Out"

### Step 3 — MIDI inputs
- Auto-detected MIDI inputs listed with light-up activity indicator
- Per-input: "Add to rig as keyboard / pads / pedal / leave unassigned"
- "Light up which input is which" — flash indicator when user plays a key, helps identify devices
- Skip + add manually in Setup → Rig

### Step 4 — Pre-add rig components (optional)
- Scrollable list of components in user's global library
- Multi-select to drop into the new show's rig
- Quick search/filter
- If global library empty: shown but skippable with "build your first rig component" hint

### Step 5 — Songs
- Add songs one at a time (name + number)
- Bulk-add via paste: textarea where each line becomes a song ("1. Overture\n2. Skid Row\n...")
- Reorder via drag
- Skippable — empty show is valid

### Step 6 — Preferences
- Autosave: checkbox, **default on**, interval (1m / 5m / 15m / on-blur)
- Tempo default for new songs (default 120 BPM)
- Confirm patch changes during Live (default off — fast and dangerous, like MainStage; opt-in for safety)
- Theme: light / dark / system (default system)

### Wizard exit
- "Create Show" → opens empty-but-configured show in Setup → Rig mode
- "Skip and use defaults" → creates show with metadata only, jumps to Setup → Rig

**v0.9.0**

## Settings (Window — floating)

**Purpose:** app-wide preferences. Not a fourth mode.

**Sections:**
- Audio: device + buffer + sample rate, separate I/O on Windows (per Part 14)
- MIDI: inputs, channel routing
- Plugins: scan paths, manual rescan, scan progress, quarantine list
- Theme: light/dark/system (full editor in v0.15.0)
- Autosave: on/off + interval
- Telemetry: opt-in toggle + crash reporter opt-in
- Keyboard shortcuts
- About: version + license + credits + update check

**v0.9.0** (skeleton), **v0.15.0** (full theme editor)

## Setup mode

The "I'm getting ready" mode. Configure the rig and show metadata before authoring patches.

### Setup → Rig (Screen)

**Purpose:** build hardware rig.

**Contents:**
- Component library: keyboard, pads, footswitch, expression pedal, sustain pedal, button/switch
- Compound component builder (drag primitives into named compound)
- Save scope toggle: show-local / global
- MIDI Learn on every learnable field (engine-backed `midi_learn_capture` command)
- Per-component config inspector (see Part 7 for per-primitive customization)
- Rig component widget editor (sub-screen — grid editor for widget appearance in Perform)

**v0.9.0** wire-up, **v0.10.0** library scope + widget editor

### Setup → Show Settings (Screen)

**Purpose:** show-level configuration.

**Contents:**
- Production / Source / Distribution metadata (see Part 9)
- Tempo defaults (master BPM removed — tempo lives on songs)
- Audio output buses (FOH, IEM-click, IEM-band, etc. — named multi-output bundles)
- Autosave settings (surfaced from wizard prefs)
- Master volume + global panic key binding
- Plugin scan paths

**v0.9.0**

### Setup → Re-learn All (Screen — sub-screen)

**Purpose:** Learn Master tool. Re-learn every learnable field in the show.

**Contents:**
- List every learnable field in every rig component in the show
- "Start re-learn" button → walks through each field sequentially
- Per-field prompt: "Interact with [field name]"
- Skip / back per field
- Diff view at end: "These bindings changed: ..."
- Save or cancel

**Use case:** moved to new machine; got new keyboard; sent show to someone else.

**v0.6.0**

## Program mode

The "I'm authoring" mode. Build patches, manage library, balance.

### Program → Patch Editor (Screen)

**Purpose:** edit the active patch.

**Currently shipping** (v0.5.0). New additions:
- `source.compound` node (drag rig component as single node) — v0.10.0
- Live preview renders full configured controller widget (keys + wheels + sustain, excludes non-tone controllers) — v0.10.0
- Per-patch tempo metadata (Advanced override) — v0.8.0
- Per-patch trim/gain field — v0.10.0 (with library work)
- Shared-patch banner "Instance of 'X'" — v0.10.0
- Missing-plugin warning icons + greyed nodes — v0.7.0

### Program → Patch Library (Screen)

**Purpose:** manage show + global patch library.

**Contents:**
- All patches in show filtered by song
- "Save to global" toggle per patch
- Drag patch from library into song → creates reference (alias)
- Reference inspector: overridable fields (Basic + Advanced)
- "Find usages" → query references by library ID
- Orphan handling banners

**v0.10.0**

### Program → Balance / EQ Tool (Screen)

**Purpose:** level-match patches.

**Contents:**
- LUFS measurement per patch (offline render — no speakers)
- Cross-patch level audit table
- Per-patch trim adjustment with live monitoring
- Tilt EQ per patch (low/mid/high single-knob)
- A/B compare against reference patch
- Reference sequence picker (sustain / attack / dynamic)

**v0.12.0** (full audio engineering breakdown in Part 8)

### Program → Pit Mixer (Screen)

**Purpose:** multi-channel audio input for MD in silent-pit / IEM contexts.

**Use case:** silent pit with IEMs sent back from sound board. MD wants to see everyone's individual levels, customize their own mix.

**Contents:**
- Per-input meter (live)
- Per-input controls: gain, pan, mute, solo, send to MD's IEM bus
- Routing matrix: which inputs go to which MD-side buses
- State persisted per-show
- Per-channel widgets available for Perform layout

**Hardware compatibility for v1.0:**
- ✅ USB Class-Compliant multitrack: X32 (32ch), SQ (32ch), QL/CL/RIVAGE, Allen & Heath, Midas, PreSonus, Soundcraft Ui
- ✅ Local USB audio interfaces with N inputs (Focusrite 18i20, etc.)
- ⚠️ Dante / AVB: requires Audinate licensing + drivers. **v2.0+**
- ⚠️ MADI / AES: requires special interface hardware. **v2.0+**

**v0.10.0**

### Program → Click Track Editor (Screen — Song tab)

**Purpose:** author bar-by-bar tempo curves with vamps/repeats/cues.

See Part 8 for full spec.

**v0.12.0**

## Perform mode

The "I'm playing" mode. Configure live layout; go fullscreen for show.

### Perform → Layout Editor (Screen)

**Purpose:** design the live screen.

**Contents:**
- Widget palette (full catalog in Part 6)
- Grid canvas (snap-to-grid default on, toggleable)
- Per-widget config inspector (per-widget options refined in v0.11.0 spec)
- Drawing primitives: box, line, divider (weight / color / style: solid/dotted/dashed)
- Image widget (PNG/JPG drop)
- Move / resize / rotate / z-order
- **Global default layout + per-song override layouts** (cascading, optional per-song override)
- Layout templates picker (Blank, Minimal, Cabaret, MD Console)

**v0.11.0**

### Perform → Live (Screen — fullscreen)

**Purpose:** what the player sees during the show.

**Contents:**
- Renders the active layout (global or per-song override)
- All widgets reactive (see Part 6)
- Pre-show validation gate before entering (overrideable with confirm)
- **No hard-forced widgets** — user-placed everything. Panic + outline are widgets, not chrome.
- Exit Live returns to Perform editor

**v0.11.0**

## Song page (Screen — renders in patch-canvas area)

**Purpose:** configure a song. Lives in the patch-canvas area when a song is selected in the outline (same affordance pattern as patch editing).

**Tabs:**
- **Settings** — song metadata, default BPM, time signature, transport behavior
- **Click** — embedded Click Track Editor (Part 8)
- **Backing** — embedded backing tracks pane (Part 8 / v0.13.0)
- **Patches** — overview / reorder

**v0.9.0** (skeleton + Settings tab), **v0.12.0** (Click), **v0.13.0** (Backing)

## Status bar / breadcrumb (Inline)

Shows: `Show › Song › Patch` when in patch; `Show › Song` when in song. Affordance-only navigation aid.

---

# Part 6 — Widget catalog

Every widget below ships in v0.11.0. Per-widget detailed config specs refined in v0.11.0 spec session — what's below is the locked-in feature list + binding model.

## Reactive widgets (Live mode)

All MIDI widgets are **reactive in Live**: hardware events drive on-screen state in real time.

### MIDI controller widgets

| Widget | Reactive to | Notes |
|---|---|---|
| Keyboard | Pressed keys, velocity | Range configurable (25/49/61/76/88) |
| Pad bank | Hit pads, velocity, pressure | Per-pad color/label |
| Sustain pedal | On/off, half-pedal position | Visual depression |
| Expression pedal | Continuous position | Vertical/horizontal bar |
| Pitch wheel | Position | Vertical track with center marker |
| Mod wheel | Position | Vertical track |
| Knob | Position | Circular indicator |
| Fader | Position | Vertical or horizontal slider |
| Button/switch | Pressed state | Momentary or latching visual |
| Rig component instance | All children reactive | Renders the compound's widget editor layout |

### Text / status widgets

| Widget | Behavior |
|---|---|
| Static text | Fixed string, full text formatting |
| Dynamic text | Token bindings: `{show.name}`, `{current.song}`, `{current.song.number}`, `{current.patch}`, `{current.patch.number}`, `{current.tempo}`, `{current.bar}`, `{next.patch}`, `{transport.position}`, `{transport.state}` |
| Big text | Large display readable from across stage. Manual or bound text. |
| Section banner | Auto-fills with current song section name (from click track cue points) |
| Status banner | Auto-fills with engine warnings (xrun, plugin crash, etc.) |
| Show notes pane | Markdown-rendered notes for current song/patch |
| Notepad widget | Live-editable markdown. Persists changes back to show. Per-widget vs per-song scope. |

### Show control widgets

| Widget | Behavior |
|---|---|
| Song/patch list | Full mode or condensed (current song's patches only) |
| Next-patch preview | Shows what's coming next |
| Cue countdown | "Next patch in: 8 bars" (when click active) |
| Panic button | Tap = engine Panic. Configurable confirm. |
| Tap tempo button | Touchable tap target |
| Quick action button | Configurable macro (e.g., "send all-notes-off on channels 2,3,5") |
| Recording indicator | Red dot when performance recording on |

### Metering / monitoring widgets

| Widget | Source | Notes |
|---|---|---|
| Volume meter | Configurable source (per-bus, per-output, per-patch) | RMS + peak hold |
| Bus meter | Specific bus | Multi-channel display |
| Spectrum meter | Real-time FFT | Useful for spotting feedback / mud |
| VU meter | Output bus | Analog-style needle |
| Engine monitor | Engine state | See full spec below |

### Engine Monitor widget (detail)

**Compact mode:** single row of indicators. **Expanded mode:** detailed table.

| Field | Source | In widget? |
|---|---|---|
| CPU % (overall) | OS process stats | ✅ single number + 60s sparkline |
| CPU % (per plugin) | Per-thread sampling | ✅ collapsed by default; expandable |
| RAM (resident overall) | OS process stats | ✅ |
| RAM (per plugin) | Sandbox process stats (post v0.7.0) | ✅ once sandboxing lands |
| Audio xruns / dropouts | cpal callback overrun counter | ✅ **critical metric** |
| Audio peak / clip per output | Per-output meter | ✅ |
| Audio roundtrip latency | Buffer size × sample rate calc | ✅ single ms number |
| MIDI input activity per device | Event-rate counter | ✅ small activity light per device |
| Plugin status per plugin | Sandbox supervisor heartbeat | ✅ alive / quarantined / crashed |
| Plugin crash count (session) | Counter | ✅ red if > 0 |
| Uptime since Go Live | Counter | ✅ |
| Disk I/O (backing tracks) | Per-track byte counter | ✅ only when backing tracks active |
| **Thermal pressure / CPU temp** | — | ❌ **dropped** — fragile cross-platform, more hassle than worth |
| Network status | — | ❌ skip — Pit is local-first |

**v0.11.0** (sandboxing-dependent fields fully populate after v0.7.0)

### Performance control widgets

| Widget | Behavior |
|---|---|
| Macro knob | One knob controls N plugin params at once (filter cutoff + reverb mix + ...) |
| Plugin parameter knob/slider | Live-tweak specific plugin param without opening plugin GUI |
| Parameter favorite | Bound parameter with custom label, configurable visual |
| Crossfader | A→B between two patches/layers |
| Solo / mute per bus | Quickly silence FOH while keeping IEM |
| Send-level slider per bus | Adjust how much of current patch goes to each bus |
| Transport | Play / pause / stop / position / cue-jump dropdown (for backing tracks) |
| Per-track mute | Mute specific backing track stem (e.g., guide vocal mid-song) |

### Time-related widgets

| Widget | Behavior |
|---|---|
| Click indicator | Visual beat flash, optional bar number |
| Transpose indicator | Current key + transpose offset |
| Bar/beat counter | Shows current bar position (driven by click track) |
| Time elapsed | Time since X (configurable: song start, show start, etc.) |
| Clock widget | See full spec below |

### Clock widget (detail)

**Per-clock-widget config:**
- Display source: current local time / time since Go Live / time since current song started / time since current patch started
- Format: 12h/24h, with/without seconds, with/without date
- Color / font / size
- **Pause/resume button** — for timing dress rehearsals where you take a break that shouldn't count
- **Reset button**
- **Split button** → captures current value as labeled split (e.g., "Act 1 end: 47:32")
- **Splits source:**
  - Manual — user defines list of labels in widget config
  - Auto from song list — labels auto-populate from show's songs in order
  - Auto from cue points — labels from active song's click-track cue points
  - Hybrid — auto-populate + user can edit/append
- **Splits behavior:**
  - Hit split (button or hotkey) → captures current value at next label, advances pointer
  - Display: current split label, time within current split, time total
  - Splits list (collapsible) shows: label, split time (within), elapsed total
  - "Skip split" / "Back" controls
  - "Reset all" + "Export splits as CSV"
- **Useful side effect:** auto-from-songs mode gives MDs a real timing report — "Act 1 ran 47:32, target was 45:00. Skid Row took 4:18 vs 4:00."

**v0.11.0**

### Visual / decoration widgets

| Widget | Behavior |
|---|---|
| Box / line / divider | Configurable weight, color, style (solid/dotted/dashed) |
| Image | Drop PNG/JPG. Show logos, branding. |
| Custom markdown | Free-form formatted text (richer than notepad) |

### Conductor Cam widget (detail)

**Purpose:** display conductor video feed on player's screen.

**v1.0 scope: USB webcam only.** UVC cameras work via `getUserMedia` in Tauri webview.

**Per-widget config:**
- Device pick (which USB camera)
- Mirror toggle (POV cams sometimes flip)
- Aspect ratio
- Crop
- Audio mute (always — analog cams sometimes have mics you don't want)
- Pop-out as floating Window for second-monitor display

**Overlay info elements** (toggleable, positionable):
- Song name (with optional number)
- Patch name (with optional number)
- Next-patch preview
- Bar number (when click active)
- Beat indicator (visual flash)
- Tempo + time signature (when click active)
- Show clock + splits
- Custom static text
- Custom dynamic text with token bindings
- Watermark (Pit logo or custom image, useful for archive recordings)

**Per-overlay config:**
- Position (anchored corner, free-position, edge banner)
- Background style (solid, semi-transparent, none)
- Font size + family + weight + color
- Outline / drop-shadow for video readability
- Visibility rules ("show only when changing patch", "always", "during click")

**Output paths:**
- Local rendering on MD's screen
- Pop-out floating Window for second monitor (cast backstage feed, FOH feed)
- Streaming output (v2.0+) — bake composite to virtual webcam device (OBS / Zoom can consume)

**Capture-card note:** capture cards like Elgato HD60 family ship as UVC and work as USB webcams. Document this; no dedicated UI affordance needed for v1.0.

**v0.11.0** (basic), **v2.0+** enhancements: IP camera (RTSP), NDI, low-latency mode, virtual webcam streaming output.

## Widget customization principle

Every widget has a config inspector with per-widget options. Per-widget detailed config refined during v0.11.0 spec session. Defaults to sensible; full customization for power users.

---

# Part 7 — Rig component catalog

Per-primitive customization. Locking in now so v0.10.0 dev has a concrete spec.

## Keyboard
- Key count (25 / 37 / 49 / 61 / 76 / 88 / custom)
- Lowest key (MIDI note number)
- Channel (default 1, filter "listen only to channel N" or "all")
- Velocity curve (linear / soft / hard / custom curve editor)
- Velocity scale (min/max clamp)
- Aftertouch enabled (channel pressure / poly aftertouch / none)
- Note name labels (sharps/flats, scientific pitch / Helmholtz)
- Color theme override (uses show theme by default)
- Show pressed keys in Live (default on, can disable per layout)
- Default transpose offset
- Note range filter (e.g., only A0–C8 forwarded)

## Pads
- Pad count (4 / 8 / 16 / 64 / custom grid m×n)
- Layout (grid / single row / custom)
- Per-pad note assignment (default = chromatic from C2)
- Per-pad MIDI channel (default = component channel)
- Per-pad color (default theme; per-pad override)
- Per-pad label
- Velocity sensitive (yes/no, fixed velocity if no)
- Pressure sensitive (channel pressure y/n)
- LED feedback (if hardware supports — sysex pattern)
- Note-off behavior (release on lift / sustain until next press / hold-to-toggle)

## Footswitch / button-switch
- Type (momentary / latching / toggle)
- Action (Next Patch / Prev Patch / Jump to Patch / Panic / Tap Tempo / Start Transport / Stop Transport / Toggle Bus Mute / Send MIDI Message / Custom Macro)
- Debounce time (ms, default 25)
- Long-press action (optional secondary, with threshold ms)
- Double-tap action (optional)
- LED feedback (if hardware supports)
- Polarity invert (some pedals are normally-closed)
- Throttle (max activations per second)

## Expression pedal
- Min/max raw range (calibration — "press fully down" → "lift fully up")
- Output range (typically 0–127, can clamp tighter)
- Curve (linear / log / exp / S-curve / custom)
- Target assignment (volume / plugin param / aftertouch / CC# / bus send)
- Deadzone at min/max (percentage)
- Smoothing (0–100 ms low-pass)
- Polarity invert

## Sustain pedal
- Type (momentary / half-pedal)
- Threshold for "on" (for half-pedal, 0–127)
- Polarity invert
- Channel
- CC override (default 64 damper; could send 66 sostenuto or 67 soft pedal instead)

## Pitch wheel
- Range (semitones up / down — default ±2)
- Snap to center (yes/no — most have spring return)
- Smoothing
- Curve

## Mod wheel
- Target CC (default CC1 modulation)
- Range (0–127 default, can clamp)
- Curve
- Smoothing

## Knob / fader
- Target assignment
- Range mapping (raw → output)
- Curve
- Pickup mode (jump / scale / relative)
- Step quantize (continuous / N steps)
- Smoothing
- Polarity invert

---

# Part 8 — Audio engineering

## Balance / EQ tool — full audio engineering breakdown

### The problem

Patches sound different at the same MIDI velocity. A bright sawtooth synth at velocity 100 is +12dB louder than a piano at velocity 100. A pad with slow attack feels quieter than a percussive piano even at identical RMS levels. Without balancing, the keys player has to manually trim every patch by ear.

### The measurement: LUFS

Loudness ≠ peak level. Use **LUFS** (Loudness Units Full Scale, defined in EBU R128 / ITU-R BS.1770):
- **Frequency weighting** — human ear is more sensitive to mids than bass/treble; LUFS applies K-weighting filter (high-shelf + high-pass) to match perception
- **RMS-style integration** — not instantaneous peak, but 400ms windowed mean
- **Gating** — silence between notes doesn't count

Three flavors:
- **Momentary LUFS** (400ms window) — what's playing now
- **Short-term LUFS** (3s window) — sustained sections
- **Integrated LUFS** (entire duration) — headline number

Plus:
- **True Peak (dBTP)** — peak after oversampling; catches inter-sample peaks that simple dBFS misses
- **Loudness Range (LRA)** — difference between loud + quiet sections; measures dynamic range

Rust crate: [`ebur128`](https://crates.io/crates/ebur128). Drop in.

### Within a patch (intra-patch)

Patches can have multiple instrument layers (split-keyboard piano below + strings above; chord patch layering piano + pad).

Each `instrument.*` node measured independently:
- Play standardized reference MIDI sequence through *each* instrument node
- Capture audio from that node's output edges (in engine's offline render)
- Compute integrated LUFS per instrument

Result: "Your piano layer is -14 LUFS; your strings layer is -19 LUFS — strings are 5 LU quieter."

UX: per-instrument trim sliders inside the patch with current values. Auto-balance button suggests trims to equalize against loudest layer (or user-chosen target).

### Within a song (cross-patch)

For every patch in the song:
- Play reference sequence
- Measure integrated LUFS
- Show as bar chart, x-axis = patch order, y-axis = LUFS

**Reference sequences:**
- **Sustain sequence** — hold 5-note chord for 4 seconds (sustained loudness)
- **Attack sequence** — 8 staccato notes at consistent velocity (attack character)
- **Dynamic sequence** — scale from velocity 30 → 60 → 90 → 120 (velocity response)

Default for cross-patch bar chart: integrated LUFS of sustain sequence at velocity 80.

Result: "Patch 4 'Soft Strings' is -22 LUFS; song median is -16 LUFS. Suggest +6 dB trim."

User options:
- Match to song median (auto)
- Match to specific patch (pick reference)
- Match to target loudness (e.g., -16 LUFS)
- Manual per-patch trim

### Across show (show-wide)

Same but spans all songs. Show-wide median. Auto-balance suggests trims to bring every patch within ±3 LU of show median.

### Velocity handling — the tricky bit

**Approach A: Velocity-normalized** (simple) — v1.0 ships this
- Always measure at velocity 80
- Trim adjustments are static (per-patch gain)
- Works well if patches have similar velocity response

**Approach B: Velocity-curve** (proper) — **v1.x enhancement**
- Measure at velocity 40, 80, 120
- Show three loudness numbers per patch
- Identifies patches with weird velocity curves
- Tool suggests both per-patch trim AND per-patch velocity curve adjustment

### Attack / transient handling

For patches with huge initial transients (piano hammer):
- True Peak (dBTP) catches the transient
- Integrated LUFS doesn't (window averages it out)
- Show both numbers
- Warning when patches have wildly different dynamic ranges ("Patch 3 has 20 LU loudness range; show median is 8 LU — will feel inconsistent")

### Silent measurement (offline render)

The cpal audio callback can be replaced with offline render target during measurement.

Engine has `RenderMode::Realtime(cpal_stream)` vs `RenderMode::Offline(buffer: Vec<f32>)`.

For balance measurement:
- Switch to offline mode
- Feed standard reference MIDI sequence per patch
- Capture output samples
- Run LUFS analysis on captured samples
- No audio hits speakers
- Returns to realtime mode when done

**Bonus:** this offline render plumbing is the foundation for performance recording (v2.0+) and MIDI bounce (v0.13.0). Free architectural reuse.

### Performance

Offline render runs much faster than realtime (CPU-bound only, no audio-clock pacing). 5-second reference per patch × 40 patches = ~5–15 seconds on modern machine. Background job, non-blocking.

### One-liner summary

The tool answers "if I play any patch at velocity 80, will I have to ride the volume fader?" — by measuring LUFS through the actual engine path offline, suggesting per-patch trim values to equalize perceived loudness, with optional dimensions for velocity curve and attack character.

## Click track editor — full spec

### Data model

```ts
ClickTrack {
  bars: Bar[],
  events: ClickEvent[],          // points on tempo curve
  vamps: VampRegion[],
  repeats: RepeatRegion[],
  cuePoints: CuePoint[]
}

Bar {
  number: number,
  timeSignature: TimeSig,
  accentPattern: number[]        // beat emphasis
}

ClickEvent {
  bar: number,                   // with fractional beat
  tempo: number,                 // BPM
  curveType: "linear" | "instant" | "ease-in" | "ease-out" | "manual"
}

VampRegion {
  startBar: number,
  endBar: number,
  label: string,
  loopCount: "infinite" | number
}

RepeatRegion {
  startBar: number,
  endBar: number,
  label: string,
  repeatCount: number
}

CuePoint {
  bar: number,
  label: string                  // "Verse 1", "Chorus", "Bridge"
}
```

### Editor UI

- **Tempo curve**: horizontal graph
  - Tempo axis (Y) on left
  - Bar axis (X) on bottom
  - Line shows tempo across bars
  - Click anywhere on line → adds control point
  - Drag points up/down to change tempo at that bar
  - Right-click point → curve-type (instant / linear / ease-in / ease-out / manual bezier)
- **Marker overlays**: vamps (looping bracket), repeats (Coda symbol), cue points (flag)
- **Side panel**: bar list with editable per-bar BPM + time sig + accent
- **Input modes per click event**:
  - Numeric BPM ("80")
  - Note-value=BPM notation ("♩ = 80", "♩. = 100", "♪ = 160")
  - Musical term ("Andante", "Allegro", "Presto" — maps to standard BPM ranges, configurable)
- **Rits/ralls**: select region → "Apply rit. from X to Y BPM over N bars"
- **Audition**: scrub playhead through click; hear in real time

### No bake step

Click data is part of the song document, engine reads it directly per audio block. Tempo curve is interpreted live (interpolation between control points done per-sample). Same architectural pattern as patch graph: data is source of truth, no compiled artifacts.

### DAW interop — SMF Type 1 with tempo map

**The universal format.** Every DAW reads/writes:
- Tempo events as `Set Tempo` meta-events (μs-per-quarter resolution = sample-accurate at any BPM)
- Time signature as `Time Signature` meta-events
- Bar markers as `Marker` meta-events
- Vamps / repeats encoded via our marker naming convention (e.g., `vamp:start:bar17`, `vamp:end:bar24`) — most DAWs render as labeled bar markers but don't loop

| Direction | Format | Scope |
|---|---|---|
| Export tempo to DAW | SMF Type 1: tempo + bar markers + cue points + vamp markers | ✅ v0.12.0 |
| Import tempo from DAW | Same SMF format | ✅ v0.12.0 |
| Export full song (tempo + per-instrument tracks) | SMF Type 1 with N MIDI tracks | 💭 v1.x if recording lands |
| Import full song (parsed tempo + bundled MIDI tracks as backing) | Multi-track SMF | 💭 v1.x or v2.0 |

**For MDs:**
- Write click in Pit's editor
- Export as SMF
- Import to DAW (Logic / Ableton / Cubase / Pro Tools / Reaper)
- Add other instruments, render audio stems
- Bring stems back into Pit as backing tracks
- Tempo stays in sync because SMF roundtripped

### Engine integration

- Engine drives click playback + MIDI clock sync from click data
- Patches can be bar-numbered → auto-advance based on click position (opt-in)
- Vamp regions in click data + transport interaction (Part 8 backing tracks)

## Backing tracks — workflow spec

**High-level for now; refined during v0.13.0 dev session.**

### Why "a play button on a patch" is wrong

Backing tracks aren't patches. They're a **per-song resource** with a transport, and patches *interact* with the transport rather than *being* the transport.

### Data model

```ts
// Song gains:
tracks: Track[]
transport: SongTransport

Track {
  id, label, file,
  stemType: "click" | "guide" | "orchestral" | "vocal" | "fx" | "custom",
  busOutput: BusId,
  gain, pan, mute,
  startOffsetMs: number          // negative = pre-roll
}

SongTransport {
  bpm, timeSignature,
  cuePoints: { id, label, positionMs }[],
  followClick: boolean           // if true, click is master tempo for band — sends MIDI clock
}

// Patch gains optional:
transportTriggers: TransportTriggers

TransportTriggers {
  onEnter: "none" | "play" | "pause" | "stop" | "jumpToCue:<cueId>"
  onExit: "none" | "pause" | "stop" | "fadeOut:<ms>"
}
```

### Workflow

1. **Setup → Show Settings → Buses**: configure FOH (stereo 1–2), IEM-click (mono 3), IEM-band (stereo 4–5)
2. **Program → Song → Tracks tab**: drop in `click.wav`, `orch.wav`, `guide.wav`. Assign click to IEM-click bus, orch to FOH, guide to nothing (mute default)
3. **Program → Song → Cue points**: scrub orch track, mark "Verse 1", "Chorus", "Bridge", "Vamp out"
4. **Program → Patch (first patch of song)**: in Settings, set `onEnter: play` so transport starts when patch is selected
5. **Program → Patch (vamp patch)**: set `onEnter: jumpToCue:vamp` so selecting it during extended vamp resyncs
6. **Perform → Layout**: add **Transport widget** (play/pause/stop/position/cue jump dropdown) and **per-track Mute widget** so MD can mute guide vocal mid-song
7. **Live**: hit first patch, transport rolls. Switch patches as needed (transport keeps playing). Hit vamp patch during extended scene — transport jumps to vamp cue. Bridge patch's `onExit` fades out orch over 4 seconds

### Vamp + click interplay

- Click track has vamp regions defined (Part 8 click editor)
- Transport enters vamp region → loops that region
- Footswitch press signals "end vamp at next loop point" → track finishes current loop, transitions out
- Patches can be tied to "exit vamp" event for auto-advance
- Requires click track editor (v0.12) for vamp-region definition

### Engine implications

- `stardust-audio-file` crate or module — file decode (mp3/wav/flac/ogg) into ring buffers (symphonia)
- Transport state in engine, polled by audio callback
- Multi-output bus routing (already needed for v1.0 anyway per Show Settings)
- Sample-accurate cue jump (decode forward seek)
- MIDI clock output synced to transport BPM (song-level, not per-track)

### What this gets you over MainStage Playback

- **Patches drive transport** (not separate Playback plugin) — feels native
- **Cue points** tied to patches let you handle vamps/codas/conductor variations cleanly
- **Per-bus stem routing** is first-class (MainStage requires manual channel-strip plumbing)

### MIDI recording (v0.13.0 — same version)

**What's cheap:**
- MIDI capture from rig → write to Song track: ~3 days (engine already captures MIDI)
- Audio bounce (render MIDI track through patches to audio file): ~1 week (uses offline render plumbing from balance tool)
- Multi-take support: ~3 days

**What's expensive (defer to v1.x):**
- Piano roll editor (note-grid, drag/drop, velocity edit, quantize, swing): ~3–4 weeks basic, 8+ production-quality
- Timeline editor (audio waveform display, region edit): ~3 weeks

**v0.13.0 ships:** record MIDI → bounce to audio. **v1.x:** piano roll. Positions Pit as more than a host — lightweight production environment for MT pit work.

---

# Part 9 — Show metadata model

Three-section structure handles MT-specific needs (revivals, sharing, licensing).

## Production (this performance/run)
- Show name, subtitle
- Production type (regional / community / school / tour / etc.)
- Venue
- Run dates (start/end/preview/opening/closing)
- MD credit
- Keys / instrument credit
- Production company
- Production notes (markdown)

## Source (the work itself, often immutable)
- Title
- Composer / Lyricist / Book writer
- **Productions list** (covers revivals — e.g., Little Shop of Horrors 1982 Off-Broadway vs 2003 Broadway Revival vs 2018 West End):
  - Production label
  - Year
  - Venue
  - Director
  - MD
  - Orchestration credit (Original / Reduced / Custom / etc.)
- **This show uses production**: dropdown → which production this show file's score/orchestration is based on
- Music publisher (often varies per production)
- License version (e.g., "MTI Educational Edition v2", "Concord Standard Orchestration")
- Performance license number
- ISMN / ISBN / catalog number

## Distribution (when sharing / marketplace)
- Author / creator (of this show file specifically)
- Last modified by
- Description
- Tags / categories
- License (MIT / CC-BY / Proprietary / Commercial — for the show *file* not the work)
- Suggested price (for marketplace)
- Required plugins (auto-computed per v0.7.0)
- Distribution notes

## On share/export
- Option to strip Production fields (venue, MD, dates) so share is generic
- Strip Distribution author info if user wants anonymity

---

# Part 10 — Reliability

## Plugin sandboxing (v0.7.0)

Architectural rule from CLAUDE.md, currently violated, scheduled v0.7.0.

**Approach:**
- Each plugin (or small group sharing memory) runs in child process
- Shared-memory ring buffers for IPC (sub-ms latency)
- Audio engine communicates with plugin processes via these rings

**Crash recovery:**
1. Engine detects disconnect on next callback
2. Sends `all-notes-off` to all channels (panic)
3. Either restarts plugin or falls back to silence + sustain-off
4. UI gets notification toast
5. Plugin flagged for quarantine if it crashes twice in same session

**Watchdog:**
- Small supervisor process monitors audio engine
- Can restart engine if it deadlocks
- UI keeps running; engine cycles in <500 ms

## Hot-plug resilience (v0.7.0)

USB MIDI / audio device disconnect handled gracefully:
- Detect via platform-specific notifications (CoreAudio Property Listeners on macOS, WASAPI device notifications on Windows, udev on Linux)
- Mute affected channel
- Surface UI warning toast
- Attempt reconnect on device reappearance
- Auto-resume on reconnect

**Why it matters:** every working musician has had a USB MIDI cable wiggle mid-show. Most music software doesn't bother with this.

## Pre-show validation (v0.8.0)

Before "Go Live," run check:
- All plugins load successfully
- All MIDI devices present and responsive
- Audio device matches saved config
- Sample rate matches
- No parameter mappings reference missing plugins
- Disk space adequate
- CPU baseline reasonable
- No quarantined plugins

Surface green/yellow/red dashboard. Override-able with confirm.

## Performance Lock mode (v0.7.0)

Single toggle ("Go Live" / "End Show") that disables:
- File ops
- Plugin scanning
- Allocation-heavy ops
- Accidental edits

**Why:** during show, accidental edits or background scans cause dropouts. Lock mode is the difference between "demo software" and "show software."

## Soak tests (v0.7.0)

Automated 4-hour playback test on macOS + Windows, asserts:
- No audio dropouts
- No memory growth
- No CPU drift
- No file handle leaks
- All notes properly cleaned up at end

Every release branch must pass before tagging.

## Voice tracking + Panic (v0.6.0 engine command, UI exists)

Pre-allocated tracking of active notes by `(channel, note, plugin)` so we can issue clean note-offs on patch change.

Panic command broadcasts `all-notes-off` + `sustain-off` on every channel.

UI Panic button (already designed in Storybook); v0.6.0 wires the engine.

## Voice tracking & patch change

When switching patches, voice tracker knows which notes are held and:
- Optionally issues note-offs to outgoing patch (default: no — preserves reverb tails when sandboxing is in)
- Routes new notes to incoming patch
- Avoids stuck notes from hold-pedal-engaged-when-patch-changes scenarios

## Silent patch change with tails (post-v0.7.0 / v1.x consideration)

MainStage's reverb-tail-during-patch-change is the bar. Today every plugin tears down on switch.

Requires: keeping *outgoing* plugin alive and rendering for N seconds while new one fades in. Warm-pool work helps with latency but doesn't fully solve tails.

**Slot:** explore in v0.7.0 sandboxing work since process model changes anyway. Full silent-patch-change may end up v1.x.

---

# Part 11 — Extension API

## Decision

**v0.15.0 ships Extension API v1: hybrid TypeScript + WASM, non-realtime.**

- TypeScript for UI extensions and importers/exporters (faster to write, no compile step for authors)
- WASM for compute-heavy with future realtime in mind
- Sandboxed by default (Web Worker for TS, WASM sandbox for compiled)
- Manifest-driven (`manifest.json` per extension)

**v2.0+ adds: realtime WASM extensions** (custom DSP / graph nodes; verified realtime contract).

## Why not native modules

Three reasons to avoid native module plugins for extensions:
1. **Crashes take down the host.** Same reason we're going out-of-process for VST/CLAP. Extensions are user-installable; the average user shouldn't be diagnosing whether an extension crash bricked their show file.
2. **Cross-platform binaries are a chore.** Every extension would need macOS + Windows + Linux + Apple Silicon + Intel variants. Wasm sidesteps all of this.
3. **No sandboxing.** Native module can read your filesystem, network, anything. Hard to publish marketplace with that liability.

## What extensions can do (v1.0 scope)

**Non-realtime (safe for any architecture):**
- New Perform widgets (e.g., "Eventide H9 controller widget", "Stream Deck button mirror")
- New file format importers/exporters (e.g., "Import .concert from MainStage")
- New rig component types (e.g., "OSC controller", "MIDI over LAN device")
- New hardware controllers (Stream Deck, Loupedeck, etc.)
- Custom commands / macros
- Theme components
- Marketplace integrations
- Cloud sync providers
- Analytics / show stats backends

## What extensions can't do (v1.0 — punted to v2.0+)

**Realtime (hard — only safe for native or carefully sandboxed Wasm):**
- Custom patch graph nodes (new MIDI processors, new audio FX)
- New plugin format hosts (e.g., AU support via extension)
- Custom DSP nodes
- Custom transport handlers

## Architecture

- Extension is TypeScript module + optional WASM module
- Manifest declares permissions: `["midi-out", "show-read", "ui-extend", ...]`
- Registers handlers: `onPatchChange`, `onSongChange`, `provideWidget`, `provideFileImporter`
- Runs sandboxed in Web Worker (no DOM access, only message-passing to host)
- Custom widgets render in iframe with strict CSP

## Authoring

- Write `manifest.json` + TypeScript file (and/or WASM)
- Pit reads from `~/.stardust/extensions/` (or per-show in bundle)
- No compilation step if accepting TS via on-the-fly transpile (esbuild) or just `.js` files

## Stream Deck as bundled example

Ships as first-party demo of extension API:
- Manifest declares Stream Deck device support + button-mapping config
- Maps buttons to show navigation actions (Next Patch / Prev / Panic / specific patch)
- Live state feedback (button LEDs reflect current patch)
- Custom widget for "Stream Deck mirror" in Perform layout

**v0.15.0**

## ADR needed before any code: **ADR-0007**

Covers TypeScript-vs-Wasm-vs-native rationale, sandboxing model, permissions, manifest format. Write during v0.15.0 prep.

## WASM rationale (separately)

**What it is:** binary instruction format that runs in sandboxed VM. Languages compile to WASM: Rust, C/C++, Zig, AssemblyScript, Go.

**Properties:**
- Sandboxed by default
- Near-native performance (~5–15% slower than native Rust for compute-heavy)
- Single binary cross-platform
- Language-agnostic

**Are we using it?** No, current stack is all native Rust + React.

**Would we benefit?** Yes, in specific places:

| Use case | WASM fit | Why |
|---|---|---|
| Extension API (v0.15.0) | ✅ Strong | Third-party code from random authors — sandboxing essential |
| Custom user DSP nodes (v2.0+) | ✅ Strong | Same reasons, plus realtime safety statically verifiable at load |
| User-built CLAP/AU shim plugins | ✅ Good | Lets users build format adapters without C++ |
| Marketplace-distributed instruments | ✅ Good | Distribute first-party "Stardust effects" as WASM, works on every platform without per-OS builds |
| Internal Stardust code | ❌ No | We're already Rust native; WASM would add 10% overhead for no gain |
| Patch / show file format | ❌ Wrong tool | These are data, not code |
| React UI | ❌ No benefit | Webview JS is fine |

**Realtime audio in WASM specifically:** emerging but not yet at native parity. Component Model + WASI 0.2 making it plausible; by v2.0 timeframe (18–24 months) ecosystem likely matured enough for user-authored WASM audio nodes.

---

# Part 12 — Marketplace + ecosystem

**Skip for v1.0.** All of this is v2.0+. Documented here so future planning has the reference.

## Three tiers

**Tier 1 — Community sharing** (free, no payments)
- Upload + download shows, patches, rig components, themes, layouts, SFZ packs
- Search / browse / filter / tag
- Ratings + reviews
- Creator pages
- Reporting / moderation tooling

**Tier 2 — Marketplace** (paid + free)
- Tier 1 plus: creator-set pricing, payment processing, license verification (downloads tied to purchaser's account), tax compliance (US sales tax, EU VAT, ROW), creator payouts, refunds + disputes, verified creator badges

**Tier 3 — Cloud sync + collaboration** (per-account)
- Show backup to cloud
- Library sync across user's devices
- Multi-MD collaboration on shared shows (CRDT-backed real-time)
- Hot-spare rig sync (LAN-primary, cloud-fallback)
- Multi-keyboardist position sync (LAN-primary)
- Optional: cloud-rendered backing track previews, cloud-stored crash reports

## Architectural principles

- **Local-first, cloud-optional** — every cloud feature additive, never gates
- **Self-hostable** — open-source server side (AGPL ethos). Community/enterprises can run own marketplace + sync. Stardust hosts canonical instance.
- **Pluggable account system** — anonymous downloads (free content), Stardust account (canonical), self-hosted account (federated), future: OIDC bring-your-own-provider
- **No tracking, no ads, no dark patterns** — telemetry opt-in only, analytics aggregate-only, payment data only where required

## Recommended tech stack

| Layer | Recommendation | Why |
|---|---|---|
| API | Rust + Axum (or Go + Chi if team grows beyond Rust) | Type safety, perf, single binary, matches stack |
| Database | PostgreSQL on Neon (serverless) or self-hosted | Boring, reliable; Neon branching for staging |
| Object storage | Cloudflare R2 | S3-compatible, no egress fees (huge for marketplace downloads), cheap |
| CDN | Cloudflare | Free tier covers a lot; integrates with R2 |
| Real-time messaging | Soketi (Pusher protocol) or raw WebSocket via Axum | Soketi if want client library ecosystem; raw WS if want zero deps |
| Search | Meilisearch (self-hosted) or Postgres full-text | Meilisearch fast + typo-tolerant; PG full-text fine for marketplace v1 |
| Auth | Clerk (managed) or self-hosted Ory Kratos | Clerk = ship fast; Ory = full control + self-hosted |
| Payments | Lemon Squeezy or Polar.sh (Merchant of Record) | MoR handles tax compliance globally — do NOT build yourself |
| Email transactional | Resend or Postmark | Cheap, reliable |
| Crash reporter | GlitchTip (self-hosted Sentry-compatible) | Open source, no per-event fees |
| Site analytics | Plausible (managed or self-hosted) or Umami | Privacy-first, no cookie banner |
| Hosting | Fly.io or Railway for API; Cloudflare Pages for marketing/docs | Cheap, low cognitive overhead, scales reasonably |

## Why not AWS / GCP

You can use them — architecture stays the same. For Stardust specifically:

### Pricing model
- AWS/GCP charge per-everything: egress fees, per-API-call, per-IP-address
- Marketplace = downloads = egress. AWS S3+CloudFront 1TB/mo egress: ~$85; Cloudflare R2 same: ~$15. At 10TB/mo: $850 vs $150
- Smaller modern providers have **flat, predictable pricing**

### Cognitive overhead
- AWS ~200 services. GCP ~100. Most aren't relevant, but learning which to use is a time sink
- "AWS Solutions Architect" is a multi-month cert because surface area is huge
- Smaller providers have sane defaults — deploy Docker container; it runs

### Lock-in
- AWS Lambda + DynamoDB + SQS → hard to leave
- Cloudflare R2 S3-compatible → swap to anything S3-compatible
- Fly.io runs Docker → swap to anything Docker
- Neon is Postgres → swap to any Postgres

### When AWS/GCP make sense
- You already know them
- You have credits (startup programs)
- Enterprise customers require it
- You need specific managed services (Bedrock for AI)

For Stardust today, none apply. **User is AWS Solutions Architect certified** — comfortable with either stack. The architecture is provider-agnostic; can swap if preferred.

## Sync architecture — CRDT (Automerge)

Three patterns considered:
- **Last-write-wins (LWW)** — simple; data loss on conflict
- **Operational Transform (OT)** — server resolves edits; needs always-on server
- **CRDTs** (Automerge, Yjs) — edits merge mathematically; works offline + P2P + via server

**Recommendation: CRDTs (Automerge)**

Reasons:
- Local-first principle satisfied — works fully offline, sync when reconnected
- Multi-device for one user — same show on laptop + studio Mac sync automatically
- Multi-user collaboration — two MDs editing same show resolve cleanly
- Hot-spare rig — same sync protocol, just over LAN
- Multi-keyboardist position sync — same protocol, ephemeral state
- Mature — Automerge 2 production-ready
- Open source — MIT/Apache, no licensing concerns

Show file format is amenable to CRDTs (node-based graph + reference-based patches = exactly the shape CRDTs handle well). Migration from "save whole document" to "CRDT-backed document with change history" is non-trivial but pays off across many features.

## Phasing

| Phase | Versions | What ships |
|---|---|---|
| v1.0 (no cloud) | through v1.0.0 | Pit fully local. No account. No marketplace. No sync. |
| Bridge | v1.1 – v1.3 | Anonymous share hub: upload as public URL, download with link. No accounts, no payments. Cloudflare-only stack. Foundation before commerce. |
| Marketplace v1 | v1.5 (or v2.0) | Tier 2: full marketplace with accounts, paid content, Lemon Squeezy MoR, creator pages. ~3–4 months dedicated. |
| Sync + collaboration | v2.0 (or v2.x) | Tier 3: CRDT migration, cloud backup, multi-device sync, real-time collab, hot-spare LAN, multi-keyboardist LAN. ~6 months. |
| Federation / self-host | v2.x | Documented self-hosted marketplace server; federated identity. marketplace.stardust.org canonical, others run their own. |

## Rough cost projection

Canonical marketplace instance scaled to ~10k users / 1k creators / 100k downloads per month:

| Service | Cost |
|---|---|
| Fly.io (API + workers) | $30–80 |
| Neon PostgreSQL | $20–50 |
| Cloudflare R2 (storage + CDN) | $20–100 |
| Clerk auth (10k MAU) | $0–25 |
| Lemon Squeezy | 5% + $0.50 per transaction (no fixed) |
| Plausible analytics | $9 |
| GlitchTip crash | $0 self-hosted |
| **Total fixed** | **~$80–270/month** |
| Plus transaction fees | Variable |

Affordable for indie. Lemon Squeezy MoR fee is biggest cost but covers global tax compliance.

## ADRs needed when marketplace work starts

- ADR: Marketplace tech stack + Merchant of Record selection
- ADR: CRDT vs OT vs LWW for sync
- ADR: User accounts + identity (managed vs self-hosted, federation)
- ADR: Self-hosting + federation model
- ADR: Content moderation policy + enforcement tooling

## What to do now (before any work)

- **Don't build any of it for v1.0.** Pit shipping local-first is right; cloud after.
- **Reserve domains**: marketplace.stardust.org, accounts.stardust.org, api.stardust.org
- **Add stubs to v2.0+ backlog** (done)
- **Design data model with sync in mind** — all-patches-as-references already helps; CRDT-friendliness is free side-effect of structured normalized data
- **Be careful about file format** — bundle format (.stardustshow/ folder) is more CRDT-friendly than monolithic JSON (individual files sync independently)
- **Keep ADR drafts folder** for future-you

## What NOT to do

**Don't build a Stardust account requirement into v1.0 "just in case."** Local-first means local-first. Adding cloud features later doesn't need account migration — the local install just starts offering optional account features.

---

# Part 13 — Show Control vision

**v2.0+ major feature.** Documented here so v1.0 architecture doesn't paint us into a corner.

## What it is

Stardust as the brain of a full theatre show. When you advance a patch in Pit:
- **Send MSC** to lighting console → "go cue 47"
- **Send OSC** to QLab → "fire sound cue Q23"
- **Send OSC** to ProPresenter → "advance to slide 12"
- **Send DMX** directly via Art-Net for simple atmospherics (haze, low-level color washes)
- **Send MIDI clock** so drum samples and tempo-locked plugins stay synced
- **Send/receive LTC** for backing track sync with rest of building

## Latency budget for cross-system show control

| System | Tolerable | Ideal | Achievable on Cat6 LAN |
|---|---|---|---|
| Lighting cue advance | <50ms | <20ms | <2ms |
| Audio cue trigger | <20ms | <10ms | <2ms |
| Video cue trigger | <100ms | <50ms | <5ms |
| Sample-accurate audio sync | <1ms | <0.5ms | requires word clock |
| Cross-system show step | <33ms (1 frame @ 30fps) | <16ms | <2ms over wired |

**Network rarely the problem.** Properly-configured show network (wired Cat6, managed switch with QoS, dedicated VLAN) hits sub-ms. Actual bottlenecks:
- WiFi: 5–30ms with variance. Don't use for cues. OK for non-critical status displays.
- Receiving devices: lighting consoles often add 10–30ms cue processing internally; QLab adds 5–10ms
- Cellular: 30–100ms+, never

## Protocols (already standard in pro theatre)

| System | Protocols |
|---|---|
| Lighting | DMX-512, Art-Net / sACN (DMX over ethernet), OSC for newer consoles |
| Sound cues + playback | MSC (MIDI Show Control, 1991), OSC (QLab), Dante (audio over ethernet) |
| Video / projection | OSC (Hippotizer, Resolume, ProPresenter), NDI for content |
| Automation (flies, turntables) | Proprietary per vendor; some MSC support |
| Comms | ClearCom / Riedel — separate analog/digital intercom |
| Cross-system sync | LTC (audio timecode), MTC (MIDI timecode), Word Clock, GenLock |

## Effort breakdown (v2.0+)

| Capability | Effort | Notes |
|---|---|---|
| OSC sender/receiver | ~3 days | well-specced UDP, Rust crates exist |
| MSC sender | ~3 days | well-specced MIDI subset |
| Art-Net / sACN sender (DMX) | ~1 week | open standards, libraries exist |
| LTC encoder + decoder | ~2 weeks | audio-based, careful sync |
| MTC | ~3 days | trivial |
| Show Control panel UI | ~3 weeks | per-cue-system mapping editor |
| Network discovery (Bonjour/Avahi) | ~1 week | auto-find consoles on network |
| Show Control templates (QLab, Eos, MA3) | ongoing | per-system spec packs |

**Total: ~8–12 weeks for credible v1 Show Control.** Slots v2.0 as major theme.

## Viability summary

- **School / community / regional / small touring**: fully viable software-only. Stardust as show brain works.
- **Mid-size regional / off-Broadway**: viable, supplement with hardware where pros prefer it
- **Broadway / large touring**: viable for keys-and-musician layer; full show control would typically still want dedicated stage manager rig (Cuelab or similar) for risk isolation. Stardust integrates *into* that rig rather than replacing it.

## Where custom hardware would help (but isn't required)

- **Hot-spare redundancy** — Broadway wants two-of-everything with auto-failover. Software possible (two laptops, MIDI A/B switcher) but purpose-built failover box cleaner.
- **Hardware show buttons** — physical "Go" buttons feel right for stage management. Stream Deck (extension API) addresses this for most cases.
- **Genlock / sample-accurate sync** — requires Word Clock or hardware sync source. Software can request but can't guarantee sample-level without hardware reference.

---

# Part 14 — Tech landscape notes

For the latency-budget + infrastructure docs.

## Audio latency landscape

| Path | Best-case 2026 latency | Notes |
|---|---|---|
| Analog SDI/composite | 0–5ms | Physics limit, electron speed |
| Apple Silicon CoreAudio | 2–4ms | M-series tuned for audio; AU3 sandboxing helps |
| Intel/AMD Windows ASIO | 3–8ms | Good ASIO driver + 64-sample buffer |
| Windows WASAPI Exclusive | 5–15ms | Catching up to ASIO |
| USB Audio Class 2 | adds 1–3ms over native | Universal driver, mature |
| USB Audio Class 3 | adds 0.5–2ms | 2018 standard, not widely adopted |
| Thunderbolt audio | adds <1ms over native | Universal Audio Apollo, Apogee Symphony |
| DSP-accelerated (UAD-2, AAX DSP) | effectively 0ms for DSP | FX on dedicated chip on interface |
| NDI (network video) | 30–80ms | Improving with NDI HX3 |
| WebRTC video | 100–400ms | Browser-dependent |
| USB UVC webcam | 100–300ms | Hardware + codec + browser overhead |

### What's changing
- **Apple Silicon** is biggest move. M-series native chips run ~2ms reliably; OS audio stack tuned for it
- **Thunderbolt 4 / USB4** make external interfaces nearly indistinguishable from internal. Universal Audio Apollo on TB ~1.1ms claimed
- **DSP-accelerated processing** — running effects on interface's chip — gives "0ms" plugin latency for supported plugins (UA, Antelope, Apogee, RME)
- **Linux PipeWire** has made real strides for pro audio. Approaching CoreAudio/ASIO parity
- **Windows low-latency drivers** — Microsoft incrementally improved WASAPI; some pro interfaces ship Class-Compliant USB drivers competitive without vendor ASIO

### What's not changing
Video stays an order of magnitude behind audio. Even cutting-edge NDI HX3 is ~30ms. **Analog remains king for conductor cam in any serious venue.**

## Hardware recommendations for Pit users

### Best-in-class (no compromise)
- Apple Silicon Mac (M2 or newer)
- Universal Audio Apollo Twin/x4/x8 (Thunderbolt) — DSP-accelerated, ~1.5ms roundtrip
- DIN MIDI 5-pin from controllers where possible (USB MIDI fine but DIN lower jitter)
- Wired Ethernet for any networked components (no Wi-Fi for show-critical)

### Pro-grade (excellent value)
- Apple Silicon Mac or modern Windows with WASAPI Exclusive
- RME Babyface Pro FS or Fireface UCX II (USB) — best-in-class stable drivers, low jitter
- Sustain + expression pedals from Boss / Roland (reliable wear)

### Budget-friendly (school / community)
- Any 2020+ laptop with USB-C
- Focusrite Scarlett 2i2 (4th gen) or Native Instruments Komplete Audio 6 — competent at ~6ms
- USB MIDI from any class-compliant keyboard

### Avoid
- Wireless MIDI (Bluetooth: 30–50ms, WiFi: variable) for performance-critical paths
- Cheap USB hubs between interface and computer (introduces jitter)
- Power-save modes during shows (forces buffer renegotiation)

## ASIO vs WASAPI — Windows audio API breakdown

| API | Year | Audio path | Typical latency | Notes |
|---|---|---|---|---|
| MME | 1991 | OS mixer → driver | 50–150ms | Legacy, don't use |
| DirectSound | 1995 | OS mixer → driver | 30–80ms | Legacy, don't use |
| WASAPI Shared | 2007 (Vista) | OS mixer → driver | 20–50ms | Default Windows; mixes with system audio |
| WASAPI Exclusive | 2007 (Vista) | Direct to driver | 5–15ms | Locks device to your app; competitive with ASIO |
| ASIO | 1997 (Steinberg) | Direct to driver | 3–10ms | Pro audio standard; requires vendor ASIO driver per device |

### Why DAWs prefer ASIO
- **Historical**: when ASIO launched, Windows audio was MME — DirectSound was slow, WDM new. ASIO bypassed everything → only path to <10ms
- **Vendor-tuned**: ASIO drivers are device-specific — Focusrite, RME, MOTU each ship optimized ASIO drivers
- **Multi-client behavior**: ASIO typically single-client; WASAPI Exclusive also single-client; WASAPI Shared multi-client
- **Channel count**: pro ASIO drivers expose all hardware channels (32-in/32-out for X32); WASAPI sometimes collapses to stereo
- **Industry inertia**: every DAW supports it; users expect "ASIO Focusrite USB" in device list

### ASIO replacement landscape
**Honest answer: no, nothing in pipeline meant to replace ASIO.** 28 years of inertia. What's happening:
- WASAPI Exclusive slowly catching up; supports split I/O natively
- WaveRT (kernel-mode under WASAPI) abstracted away
- ASIO 3.0 discussed for 20 years, never materialized
- CLAP organization has discussed audio I/O API alongside plugin spec; nothing public
- PipeWire rapidly displacing JACK + PulseAudio on Linux
- Apple Silicon CoreAudio approaches "no audio API choice needed"

### Practical answer for Pit
Support all three. Default rules:
- **macOS**: CoreAudio (no driver wars)
- **Linux**: ALSA → JACK if available, PipeWire fallback
- **Windows**: 
  - Default to **WASAPI Exclusive** (ships with Windows, no driver install, 5–15ms achievable)
  - Surface **ASIO** if vendor drivers present (user opt-in for best latency + multi-channel)
  - WASAPI Shared as fallback (casual / desktop use)
- Never default to MME or DirectSound

Sample-rate sanity: if user picks device that doesn't support show's sample rate, warn + offer resample on the fly (slight quality hit) or switch device.

### Separate I/O on Windows
- WASAPI handles separate input/output natively
- ASIO traditionally locks to one device for both
- macOS solves via CoreAudio Aggregate Devices (combine multiple into one logical)
- Linux PipeWire handles natively
- **Pit must expose separate input/output device pickers** — this is a known pain point in DAWs

---

# Part 15 — Tech debt log

Tracked here per CLAUDE.md tech-debt rule. Most cleaned up by upcoming version work.

## Engine / Rust
- `PluginEntry` leaks intentionally (`mem::forget`) — bundles never unload. **Cleaned by v0.7.0 sandboxing rewrite**
- Plan rebinds only on plugin-choice change — editing EQ/mix/transpose config doesn't rebind. **Cleaned by v0.11.0 live audio-fx editing**
- Plugin scan eager + uncached on app launch. **Cleaned by v0.6.0 scan caching**
- Hardware MIDI hardcoded to first `source.keyboard` node. **Cleaned by v0.6.0 per-source binding**
- EQ crossover frequencies are constants (250/1k/4k). **Revisit alongside audio.eq settings panel**
- No graceful engine shutdown. **v0.15.0 cleanup**
- cpal `DeviceTrait::name` deprecation warnings (3). **v0.15.0 cleanup**

## Frontend / TypeScript
- `tsc --noEmit` in `ui:build` fails on tsconfig project-references bug (`tsconfig.node.json` not marked composite). Predates v0.4. **Fix in v0.6.0 (touching build anyway)**
- `sound/` components (plugin-browser, plugin-parameter-panel, midi-mapping-row, sound-flow) orphaned — superseded by patch graph. **Delete during v0.10.0 library work**
- Storybook `PluginUIDock` has no plugins. **v0.6.0 plugin GUI work fixes**
- Dirty-tracking is a dot, not close-blocker. **Cleaned by v0.9.0 close-blocker**
- On-screen keyboard: no velocity (fixed 100), no channel choice, no sustain pedal, no QWERTY mapping. **Velocity + sustain v0.6.0; QWERTY v0.15.0**

## Docs
- `/docs/pit/roadmap/` was years out of date — **fixed by previous doc rewrite**
- `edit-vs-live` concept doc contradicted current shell — **fixed by v0.9.0 concept rewrite**
- 20 feature pages lacked status badges — **fix in doc rewrite**
- Several feature pages reference URLs that don't exist (Widget Registry, Screen Inventory, Data Model, File Format) — **stub or fix in doc rewrite**
- ADR-0002 status Proposed but unbuilt — **resolved by v0.7.0**

## Architectural / strategic
- CLAUDE.md "out-of-process plugin hosting" rule violated by current implementation. **Resolved by v0.7.0**
- No autosave anywhere. **Resolved by v0.9.0**
- No backup / recovery / .swp-style protection. **v0.9.0 or v0.15.0**
- No telemetry / crash reporter. **Resolved by v0.15.0**
- Pre-CI gap (no automated tests on PRs). **Cleaned by v0.6.0**
- No release pipeline. **Cleaned by v0.15.0**
- Sine synth as primary built-in misleading branding. **Cleaned by v0.6.0 rename + v0.14.0 replace**
- Save file format is single JSON. **Cleaned by v0.13.0 bundle migration**
- No multi-channel audio input. **Cleaned by v0.10.0 Pit Mixer**
- No native file menu. **Cleaned by v0.9.0**

## Critical (would fix sooner)
- None critical right now. `tsc --noEmit` is the closest to "should fix sooner" since it silently breaks type-checking guarantees on the frontend build — fix v0.6.0.

---

# Part 16 — Decisions ledger

Every locked-in decision with reasoning. Don't relitigate; reference here.

## Versioning
- **Semver `major.minor.patch`** — switched from `vX.Y-letter`
- **Every version is a real release with explicit exit criteria** — not a milestone framing
- Patches = bug fixes; Minors = scoped releases; Major = v1.0 public, v2.0 = post-launch ecosystem

## Engine + audio
- **CLAP only for plugins** in v1.0; VST3 + AU as v1.x or v2.0
- **Pure-Rust VST3 host** is v2.0+ (`stardust-vst3` extracted)
- **Pure-Rust AU host** is v2.0+ (`stardust-au`, macOS-only, ~4–6 months)
- **Plugin sandboxing out-of-process** is hard requirement — currently violated, scheduled v0.7.0
- **Realtime paths allocation-free** (CLAUDE.md rule)
- **Engine consumes whole patch graph** — Plan::build → topo-sort → allocation-free Plan::process (ADR-0006)
- **Audio I/O on Windows**: WASAPI Exclusive default, ASIO surfaced when available, WASAPI Shared as fallback. macOS CoreAudio. Linux ALSA → JACK → PipeWire fallback. Support separate input/output devices.
- **Sine synth → `instrument.testtone`** (hidden, diagnostic only). Default built-in instrument becomes SFZ player with bundled GM piano (v0.14.0).
- **Ship native SFZ player as graph node**, not standalone CLAP (sforzando exists for users wanting CLAP)
- **Ship built-in GM piano SFZ** (~3MB) in install bundle
- **No VST2 support, ever** — Steinberg deprecated 2018, SDK not available to new licensees

## Data model
- **All patches are references to library entries** (no inline-vs-ref dichotomy)
- **Library entries have `scope: "show" | "global"`** — single field
- **Show file bundles snapshots of global entries on share**
- **Orphan handling**: deleted library entry → refs freeze the last graph as `orphan.snapshot`, banner + reattach/save-new/keep options
- **Patch reference overrides**: Basic (name, notes, tempo, transpose, trim, color, tags) + Advanced (MIDI channel offset, bus routing, plugin params, FX bypass, on-enter/exit triggers, custom CSS). Tempo override = Advanced.
- **Graph edits to shared patches** trigger merge UI with per-instance update/keep/three-way-merge
- **Show metadata** structured as Production / Source / Distribution — Source includes Productions list for revivals
- **Schema-versioned everything** per ADR-0003
- **Crate organization stays flat workspace** — group by naming convention; revisit if past ~15 crates

## File format
- **`.stardustshow/` bundle** (folder with extension) — not single JSON
- **Contents**: `show.json`, `libraries/`, `assets/audio`, `assets/images`, `assets/samples`, `thumbnails/`
- **Opt-in zip export** for sharing
- Migration scheduled v0.13.0 (backing tracks force the issue)

## UI shell
- **Three modes: Setup / Program / Perform** (locked in for now; may revisit names later)
- **Settings is a floating Window**, not a fourth mode
- **Plugin GUIs are floating Windows**, per-plugin
- **New Show wizard is a Modal**
- **Splash is pre-shell screen** (separate from three modes)
- **Native menu bar** for File/Edit/View/Window/Help — mode switches NOT in menu bar
- **Song page renders in patch-canvas area** when song selected in outline
- **No hard-forced Live widgets** — user places everything; layout templates seed starting layouts
- **Confirm-patch-changes-during-Live**: default off (MainStage style instant), opt-in confirm available
- **Layout**: global default + per-song override (cascading)

## Widget customization
- **Every widget has config inspector**, detailed specs refined v0.11.0 spec session
- **MIDI widgets reactive in Live** (keys/pads/wheels/pedals reflect hardware state)
- **Conductor cam**: USB webcam only v1.0; RTSP/NDI/virtual-webcam v2.0+
- **Engine monitor**: includes CPU/RAM/xrun/peak/MIDI activity/plugin status/crash count/latency/uptime. **Excludes thermal pressure + raw temp** (cross-platform fragility).
- **Clock widget**: pause + splits (manual / auto-from-songs / auto-from-cuepoints)

## Click track + transport + backing tracks
- **Click track editor: no bake step** — data-driven always-live
- **SMF Type 1 export/import** for DAW interop (tempo + bar markers + cue points; vamps/repeats via our marker naming)
- **Tempo per song + per bar** (no master-show BPM)
- **Backing tracks decouple from patches** — tracks on songs, transport independent, patches optionally interact
- **Vamp interaction**: vamp regions in click track; transport loops; footswitch signals end-of-vamp
- **MIDI clock sync**: song-level (not per-track)
- **MIDI recording + audio bounce** in v0.13.0; **piano roll editor** in v1.x

## Balance tool
- **LUFS via `ebur128`** crate
- **Offline render** (silent measurement)
- **Velocity-normalized at v80** for v1.0; **velocity-curve at v40/v80/v120** for v1.x
- **True Peak + LRA + Integrated LUFS** reported per patch

## Plugin missing handling
- **Warning icons** on patch name + plugin node + greyed-out missing node
- **"Find this plugin"** link via CLAP `plugin.url` metadata
- **Graph node never removed** when plugin missing — preserved for when plugin returns
- **Show plugin requirements** auto-computed and surfaced in pre-show validation

## Sync + ecosystem (post-v1.0)
- **CRDT (Automerge)** for sync + collaboration
- **Local-first non-negotiable** — every cloud feature additive
- **MoR for payments**: Lemon Squeezy or Polar.sh (do not build payment infra)
- **Self-hostable marketplace server** — open source
- **No mandatory accounts ever** — anonymous downloads stay available
- **Cloud provider stack provisional**: Cloudflare R2 + Fly.io + Neon Postgres + Clerk/Ory + Plausible + GlitchTip. **Provider-agnostic** — user is AWS-certified, can swap to AWS/GCP if preferred.

## Extension API
- **Hybrid TypeScript + WASM** for v0.15.0 — TS for UI/importers/commands, WASM for compute-heavy
- **Realtime WASM extensions** v2.0+
- **Sandboxed by default** — no native module plugins
- **Stream Deck support** ships as bundled example extension

## Tooling
- **Bun, not npm** for stardust-pit (uses `@tauri-apps/cli` JS)
- **GitHub Projects v2** for kanban (columns: Planned → In Progress → Testing → Review → Done → Deferred)
- **GitHub Actions** for CI: basic PR CI v0.6.0, soak tests v0.7.0, visual regression v0.10.0, release pipeline v0.15.0
- **No `Co-Authored-By: Claude`** footer in commits, ever
- **Storybook stays as design-iteration surface**; real screens in `src/src/screens/*.tsx`
- **Placeholder icons in `stardust-pit/src-tauri/icons/`** — don't touch until real branding
- **Storybook-first for UI features** (CLAUDE.md rule)
- **Pre-feature refinement + post-feature review sessions** (CLAUDE.md rule)

## CLAUDE.md additions (all locked in)
- Roadmap discipline
- Tech debt tracking
- Storybook-first for UI features
- Feature refinement + review sessions
- Accessibility is a hard requirement
- Audio + ecosystem tech awareness

## What's NOT in v1.0
- AU plugin hosting (tentatively v1.0 if scope allows; defer otherwise)
- Multi-channel audio input via Dante/AVB (USB multitrack only)
- Cloud sync, marketplace, collaboration (all v2.0+)
- Sheets app (post-Pit-v1)
- Piano roll editor (v1.x or v2.0)
- Pure-Rust VST3 host (v1.x with C++ shim is fine)
- Realtime WASM extensions (v2.0+)
- IP/RTSP/NDI conductor cam (v2.0+)
- DMX / lighting (revisit if Show Control unlocks demand)
- Velocity-curve balance (v0.12 does velocity-normalized; curve v1.x)
- Show Control as full theatre brain (v2.0+)
- Full DAW MIDI import (v1.x or v2.0)

## v2.0+ backlog (full list for context)

- Pure-Rust VST3 host
- Pure-Rust AU host
- Realtime WASM extensions (custom DSP / graph nodes)
- Marketplace (Tier 2: paid + free)
- Community share hub (Tier 1: free, v1.x bridge)
- Cloud sync + collaboration (CRDT-backed)
- Hot-spare rig sync (LAN-primary, cloud-fallback)
- Multi-keyboardist LAN sync
- Show Control (MSC + OSC + Art-Net/sACN + LTC + MTC)
- Mobile companion (Tauri Mobile, LAN remote)
- Federation / self-hosted marketplace
- Advanced cue system (MSC deeper, QLab bidirectional, cue list timeline)
- AI sound search
- Audio input rigs (guitar/bass/vocals/winds via NAM/Guitarix/AIDA-X/Neural DSP)
- Plugin bundles + one-click installer
- Custom sampler (record/import → SFZ generation)
- DMX / lighting (revisit)
- Conductor cam enhancements (RTSP/IP, NDI, capture-card UI, virtual webcam streaming)
- Piano roll editor (if not v1.x)
- Velocity-curve balance (if not v1.x)
- Show analytics
- Practice mode
- MainStage / Gig Performer migration wizard
- Custom device profile editor

---

# Part 17 — Bootstrap prompt for the fix-it chat

The doc-writing chat is mid-execution but is missing depth from this planning conversation. Use this prompt to get it back on track.

## The prompt

> Major context update — the prior planning chat had significant depth that didn't all make it into HANDOFF.md. I've consolidated it into `PLANNING.md` in the workspace root. **Stop current work, read `PLANNING.md` end-to-end, then redo or augment any feature pages, roadmap entries, ADRs, or kanban issues you've already written that lack the depth captured there.**
>
> Specifically:
>
> 1. **Read `PLANNING.md` fully** (it's long — ~3000 lines — but every section matters; the Table of Contents lets you jump to specific features when writing per-feature docs)
> 2. **Audit your existing work** against PLANNING.md:
>    - Does each per-version roadmap entry match the per-version scope in Part 3? (Especially: full reasoning, all in-scope items, explicit exit criteria)
>    - Does each feature page have the depth from the relevant PLANNING section? (Balance tool — Part 8 has full audio engineering breakdown. Backing tracks — Part 8 has the workflow + vamp interaction. Click track editor — Part 8 has data model + DAW interop. Conductor cam — Part 6 has full widget spec + Part 14 has the analog-vs-software analysis. Engine monitor — Part 6 has the field table. Pit Mixer — Part 5 has the use case + hardware compat. Etc.)
>    - Are kanban issues for v0.6.0 detailed enough? (Part 3 v0.6.0 section has the full in-scope list with reasoning)
>    - Are the cross-cutting decisions (all-patches-as-refs, file format bundle, WASM extensions, infrastructure choices) reflected in the docs that depend on them?
> 3. **Specifically write or rewrite these per-feature pages with full depth from PLANNING.md:**
>    - `/docs/pit/features/balance-tool.md` — Part 8 has the full audio engineering content (LUFS / velocity / attack / silent measurement)
>    - `/docs/pit/features/backing-tracks.md` — Part 8 has the workflow + data model + vamp interplay
>    - `/docs/pit/features/click-track-editor.md` — Part 8 has data model + UI spec + SMF roundtrip
>    - `/docs/pit/features/engine-monitor.md` — Part 6 has the field table + compact/expanded modes
>    - `/docs/pit/features/conductor-cam.md` — Part 6 widget spec + Part 14 analog-vs-software analysis (+ the integration with theatre tech setup)
>    - `/docs/pit/features/pit-mixer.md` — Part 5 use case + hardware compat
>    - `/docs/pit/features/patch-library.md` — Part 4 all-patches-as-refs full spec (data model, resolution, orphan handling, merge UI, sharing model)
>    - `/docs/pit/features/extension-api.md` — Part 11 architecture + Stream Deck example
>    - `/docs/pit/features/new-show-wizard.md` — Part 5 full 6-step spec
>    - `/docs/pit/features/button-switch-component.md` — Part 7 footswitch spec (now generalized as button/switch)
>    - `/docs/pit/features/show-control.md` (v2.0+ vision) — Part 13 full landscape + viability + effort breakdown
>    - `/docs/pit/reliability/latency-budget.md` — Part 14 has the full audio latency landscape + hardware recommendations
>    - `/docs/ecosystem/marketplace-architecture.md` — Part 12 full tier model + tech stack + phasing + cost projection
>    - `/docs/ecosystem/infrastructure-choices.md` — Part 12 "Why not AWS / GCP" rationale (+ note user is AWS-certified, stack is provider-agnostic)
>    - `/docs/pit/concepts/setup-program-perform.md` — Part 5 mode breakdown
> 4. **Add a `Status` badge to every existing feature page** (`✅ shipped` / `📋 planned-v0.X.0` / `💭 v2.0+`) per Part 16 decisions ledger
> 5. **Update kanban issues for v0.6.0** to have detailed acceptance criteria from Part 3 v0.6.0 scope. The user explicitly wants kanban issues to be granular enough that any contributor could pick one up.
> 6. **Add tech debt items** from Part 15 to the kanban with `tech-debt` label, with cleanup-version references
> 7. **For anything in PLANNING.md you have a question about, ask before writing** — the user has spent multi-session depth on these decisions and would rather clarify than have you guess
>
> When done, update HANDOFF.md to note that PLANNING.md is required reading for any future chat resuming Stardust work, and add it to the bootstrap prompt for new chats.

## Why this works

- PLANNING.md is self-contained and exhaustive — fix-it chat doesn't need to re-derive
- Specific file list tells fix-it chat exactly what to rewrite vs leave alone
- "Ask before writing" instruction prevents fix-it chat from confidently filling in gaps with guesses
- The HANDOFF.md update at the end ensures PLANNING.md becomes part of the permanent bootstrap context

---

**END OF PLANNING.md**

Maintenance: when a v0.X refinement session locks in a decision that contradicts something here, update both this doc and the relevant feature page. When a new feature is added to scope, write the spec here first, then the feature page. This doc is the single source of truth for "what does v1.0 look like."
