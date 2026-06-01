# Stardust Workspace — Claude Instructions

> **New chat resuming Stardust work?** Read `HANDOFF.md` first — it
> tracks in-flight work that's mid-extraction, the active roadmap
> phase, and decisions worth not re-litigating. This file (CLAUDE.md)
> covers durable conventions; HANDOFF.md covers "what are we doing
> right now".
>
> **Token efficiency directives** (the user pays per token, threads
> grow expensive fast):
>
> - **Be terse.** Skip explanatory framing. Get to the action. End-of-
>   turn summary = one sentence max.
> - **Prefer `Edit` over `Write`** for changes to existing files —
>   Edit sends just the diff. Only use `Write` for genuinely new files
>   or full rewrites.
> - **Don't re-read files you've already seen this session.** Use what's
>   in context.
> - **Don't narrate the plan before each step** — the user can see the
>   tool calls.
> - **Suggest new chats** when the user starts a meaningfully different
>   chunk of work; long threads dominate cost.
> - **When a feature ships, stop and hand off.** As soon as a discrete
>   piece of work is done (committed + pushed + working), do this in
>   order: (1) explicitly tell the user "feature X is complete";
>   (2) update `HANDOFF.md` with the new state — bump the worklog,
>   move "in flight" items to "shipped", record new commits worth
>   knowing, list any loose ends; (3) point the user at the "Bootstrap
>   prompt for a new chat" section of HANDOFF.md and tell them to
>   `/clear` (or open a new chat) before the next feature. Do NOT
>   automatically start the next feature in the same thread.

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

Pit is the active focus, currently at **v0.5.0** (multi-plugin chain hosting). Sheets is post-Pit-v1. Everything else (Rehearse, Produce, Stage, Lighting, Galaxy) is speculative — do not scaffold those repos or write code targeting them.

Versioning is **semver `major.minor.patch`**. The roadmap to v1.0 lives in `stardustmt.github.io/src/content/docs/docs/pit/roadmap/` — that is the source of truth for shipping scope and exit criteria. `HANDOFF.md` is the short-term in-flight tracker; the docs roadmap is the long-term release plan.

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

---

## The three living documents (roadmap · issues · docs)

There is no separate planning doc. The roadmap, the GitHub issues, and the docs site **are** the source of truth — collectively and permanently. Each has a distinct job, and each is a *living* document that must be checked at the start of work and updated as work proceeds. Never let them drift from reality.

**Division of responsibility:**

- **Roadmap** (`stardustmt.github.io/.../pit/roadmap/`) — high-level *what ships and in what order*. Per-version scope, exit criteria, tech-debt log, v1.x / v2.0+ backlogs. The human narrative.
- **Issues** (GitHub Project board at the StardustMT org) — the *individually-implementable specifics*. One issue = one pickup-able piece of work. Each issue carries: context, detailed acceptance criteria, refinement notes, work-log notes, links to any issues it spawned, and a closure summary. Commits and PRs reference issues.
- **Docs** (`stardustmt.github.io/.../pit/` feature/concept/architecture pages) — the in-depth *textbook*. At v1.0 a user should be able to learn Pit entirely from the docs. Every shipping feature has an accurate, current page.

**Obligations — these are not optional:**

1. **Check before you work.** Before starting any feature or issue, read its roadmap entry, its issue(s), and the existing docs page. Don't re-derive what's already written down.
2. **Issues are the work log.** During refinement, append the locked-in decisions to the issue (tighten the acceptance criteria, add a "Refinement notes" section). During implementation, log meaningful progress + decisions as issue comments. If work reveals a new piece of work, **file a new issue, cross-link it** (both directions), and tag it to a milestone. On completion, close the issue with a summary of what shipped + the commit/PR reference.
3. **Docs ship with the feature.** When a feature ships or materially changes, update its docs page in the *same* change — status badge, behavior, screenshots/GIFs where relevant. A shipped feature with stale docs is an incomplete feature. Docs are the user's textbook, not a marketing artifact: write them so a musician can get their bearings and learn to use Pit.
4. **Refinement updates docs and the board in the same session — not "with the eventual PR."** When a decision changes during refinement (a reversal, a scope shift, a milestone move, an estimate revision), the update isn't deferred to whoever implements months later. Update everything affected, in the refinement session that made the change:
   - **`decisions.md`** — if a locked decision was reversed or added, write it there with a one-line "refined YYYY-MM-DD during #N refinement" pointer. This is the canonical decision log; it cannot lag.
   - **Roadmap entry** — if version scope changed, update the version's section + the tech-debt log. If a deliverable moved to a different version, edit both versions' entries.
   - **Affected feature / concept / screen / reliability docs** — anywhere the page documented the *old* shape of the decision is now wrong. Fix it now; don't wait for the implementation PR. The same-PR-as-feature rule (obligation 3) is for *new* docs that ship with new behavior; *existing* docs that became wrong during refinement must be fixed in the refinement session itself.
   - **Project board fields** — `Status` (🔍 Under refinement → 📋 Planned when criteria lock), `Estimate`, `Priority`, `Milestone` — all updated on the board as part of the refinement pass, not "from memory later." Verify field values match the refinement notes you wrote in the issue body — they can drift.
5. **Keep the three in sync.** Roadmap scope change → reflect on the board. Issue spawns scope → reflect on the roadmap. Feature ships → roadmap badge + docs page + issue closure, together.

The refinement and review sessions (below) are the formal checkpoints for this; but the obligations apply continuously, not just at session boundaries.

---

## Issue hygiene (the fields every issue carries)

Every issue is created and maintained with a consistent set of fields. This is what makes the board searchable and the work durable.

**At creation:**

- **Title** — short imperative; one implementable thing
- **Body** — context, acceptance criteria checkboxes, references (PLANNING moved into docs/ADRs; cite roadmap entries + related issues + relevant docs)
- **Milestone** — the target version (every issue has one)
- **Labels** — area labels (`screen:*`, `engine:*`) + cross-cutting labels (`tech-debt`, `infrastructure`, `documentation`, `extension`, `needs-refinement`)
- **Type** — GitHub native Issue Type. Use **Feature** for new user-visible functionality, **Task** for infrastructure / docs / tech-debt / chore, **Bug** for unexpected behavior. Set at creation.
- **Project** — added to the StardustMT Pit board immediately; **Status** = 📋 Planned

**Set during the version's pre-feature refinement session:**

- **Estimate** — XS (`<0.5d`) / S (`~1d`) / M (`2–3d`) / L (`~1wk`) / XL (`2wk+`). Don't estimate at creation — wait for refinement so the number means something. Mark `🔍 Under refinement` while in the session; back to `📋 Planned` once criteria are locked.
- **Priority** — P0 (show-blocker) / P1 (important) / P2 (normal) / P3 (someday). Most pre-1.0 work is P2 with reliability + critical-path bumped to P1. P0 reserved for actual show-blocking bugs once shipping.
- **Refinement notes** — append the locked-in decisions to the issue body (or a dedicated "Refinement notes" section). Tighten acceptance criteria from rough to concrete.

**At pickup (start of work):**

- **Assignee** — self-assign
- **Status** — flip to 🔨 In Progress

**During work:**

- Log meaningful progress + decisions as **issue comments** (the work log)
- If new work surfaces, **file a new issue** + cross-link it both directions. Use **native GitHub sub-issues** when the new work is a child of an umbrella (don't use text-only `#42` cross-links for parent/child — text links are fine for siblings or peer references). The `needs-refinement` umbrellas (widget catalog, click editor, balance tool, etc.) spawn sub-issues this way.

**At completion:**

- Close the issue with a comment summarising **what shipped + commit/PR ref**
- Status → ✅ Done (or 🧊 Deferred with a one-line reason)
- If it was a UI feature, the **Storybook screenshot automation** (issue #113, once shipped) posts a screenshot to the issue automatically; until then, attach a screenshot manually

**Commits reference issues.** Every commit message that lands work for an issue includes `#N` so cross-references resolve. This is what feeds the screenshot automation pipeline.

---

## Roadmap discipline

`stardustmt.github.io/src/content/docs/docs/pit/roadmap/` is the source of truth for what Pit will ship and in what order. Every code change that affects shipping scope updates the roadmap in the same change:

- **Feature ships**: bump the version entry from 📋 planned to ✅ shipped with the actual git tag. Move loose ends into a tech-debt entry if any remain.
- **Feature added to scope**: insert it into the appropriate version's section with explicit exit criteria. Don't add anything without exit criteria.
- **Feature deferred or dropped**: move it to a later version (or v2.0+ backlog) with a one-line reason. Don't silently disappear features.

The GitHub Project board mirrors the roadmap — keep both in sync. Issues represent the operational unit (commits, PRs reference them); the roadmap doc is the human narrative.

This applies in addition to the existing HANDOFF.md ship workflow. HANDOFF tracks short-term in-flight state; the roadmap doc tracks release-shaped scope.

---

## Tech debt tracking

When you introduce tech debt — a known-suboptimal choice, a deferred cleanup, a workaround that should be revisited — add it to the Tech Debt section of the roadmap doc. Include:

- One-line description of the debt
- Why it's acceptable for now (or why we shipped it)
- Which future version is expected to clean it up (or "no plan yet")

The pre-v1.0 polish release (v0.15.0) explicitly clears outstanding debt items, so anything not naturally cleaned up by another version must be resolved or explicitly deferred before tagging 1.0.

Don't silently introduce debt. `// TODO:` comments are fine in code, but the debt list is what gets reviewed.

---

## Storybook-first for UI features

Any UI-related feature with no matching Storybook story must have one created first, before functional code is written. Storybook is where the user critiques and locks in UX before wiring happens.

Applies to:

- New screens (Splash, Pit Mixer, Click Track Editor, etc.)
- New widgets (every Perform widget)
- New modals (wizards, validation, confirms)
- New inspector panels

Does NOT apply to:

- Pure engine work with no UI surface
- Bug fixes to existing UI (the story already exists)
- Internal refactors with no user-visible change

Workflow: create the Storybook story → demo it to the user → iterate until UX is approved → THEN wire up the functional code.

---

## Feature refinement + review sessions

Each version has two bookend sessions, in addition to the implementation work.

**Pre-feature refinement session** — when starting work on a version, walk through the roadmap entry *and the version's issues* with the user, issue by issue. Surface every ambiguity, lock in concrete details (UX, data model, exit criteria). Write the outcome where it belongs: refined acceptance criteria + a "Refinement notes" section **on each issue**; the refined spec on the **roadmap** entry; any newly-discovered work as **new cross-linked issues** on the board. Catch hand-wavy items before they become guessed-at code. Flip refined issues from 📋 Planned → 🔍 Under refinement → 📋 Planned (criteria locked) so the board shows refinement state.

**Post-feature review session** — after the version ships, walk through what was actually built vs what was spec'd. Items in scope that didn't land become follow-up tickets in the next version (filed + cross-linked). Items spec'd that proved unnecessary get removed from the roadmap with a one-line reason. Bugs found get fixed immediately (if small) or filed as tickets. Every shipped item's **docs page is brought current** as part of this review.

Both sessions update HANDOFF.md + the roadmap doc + the GitHub issues + the affected docs pages — together, in the same pass.

---

## Accessibility is a hard requirement

Every shipping feature must pass an accessibility audit for that feature's surfaces before its version is tagged. No "we'll fix it in v0.15.0" excuses.

Minimum bar:

- WCAG 2.2 AA contrast (AAA where feasible)
- Full keyboard navigation (no mouse-only interactions)
- Screen reader compatibility (semantic HTML + ARIA labels)
- Focus indicators visible on every focusable element
- Live regions for engine status announcements
- Reduced-motion preference respected

Theme work must include a contrast checker that fails the theme if it falls below AA. Custom themes that fail are warned but can be saved (user choice).

When the user is part of the audit, frame the ask as: "Try operating this screen with keyboard only" / "Try this screen with VoiceOver." Real testing, not just label compliance.

---

## Audio + ecosystem tech awareness

When you become aware of relevant updates to the audio, sync, plugin, or ecosystem tech landscape — realtime WASM maturing, new platform audio APIs, new sync protocols, latency-relevant hardware shifts, new plugin formats, anything that materially affects what Stardust can build — surface it to the user. Especially if it bears on a currently active feature or a near-term roadmap item.

Be relevant, not exhaustive. The signal is "this changes what we should consider doing," not "here's the news."
