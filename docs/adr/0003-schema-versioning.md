# ADR-0003: Schema versioning for persisted formats

- **Status:** Accepted
- **Date:** 2026-05-18
- **Deciders:** @ChaseCondon
- **Affects:** stardust-core, stardust-pit, future apps

## Context

Stardust will persist several kinds of data across versions of the app:

- **Show files** — top-level performance document containing song order, master settings, post-mix FX chain, references to a rig
- **Song files** — within a show: patches in playback order, transitions, vamp markers, tempo/key info
- **Patch files** — within a song: sound chain, instrument settings, MIDI mappings, zone splits, effects chain
- **Rig profiles** — physical hardware layout (keyboards, pedals, controllers) and their default settings
- **Library entries** — local catalog of installed instruments, effects, presets, MIDI device profiles
- **User preferences** — global app settings

These files live on the user's filesystem and must remain openable across upgrades. A musician who built a show in v0.4 must be able to load it in v0.7 without losing data. Conversely, a user who downgrades (or shares a file with someone on an older version) should get a clear error rather than silent corruption.

A naive "just use serde defaults" approach silently breaks the moment fields are added, removed, or renamed.

This is a problem that has to be solved before the first persisted file format ships, because retrofitting versioning onto unversioned files is harder than designing it in from the start.

## Decision

**Every persisted format carries an explicit `schema_version` field, and `stardust-core` provides a migration framework that turns "old document on disk" into "current in-memory representation" with explicit, reviewable steps.**

Concretely:

1. **Every persisted file starts with a header.** At minimum:
   ```json
   {
     "kind": "stardust.show",
     "schema_version": 3,
     "stardust_version": "0.7.2",
     "saved_at": "2026-05-18T14:32:11Z",
     ...
   }
   ```
   `kind` namespaces the format. `schema_version` is the only field used to drive migrations. `stardust_version` is informational (which app build wrote this) and never used for parsing logic.

2. **Schema versions are monotonically increasing integers, scoped per `kind`.** A `stardust.show` at v3 is independent from `stardust.patch` at v5.

3. **Migrations are explicit, one-step, and reviewable.** For each `kind`, `stardust-core` ships a chain of `migrate_v{N}_to_v{N+1}` functions. Loading a v1 show on app v0.7 (current schema v3) runs migration 1→2 then 2→3 in sequence. Each migration is a small, tested, reviewed function with a clear input and output type.

4. **Migrations are pure data transformations.** They do not depend on the running app's state, plugin availability, or user input. If a migration cannot succeed deterministically, it must record an explicit unresolved field in the migrated document for the app layer to handle, not silently drop or guess.

5. **Forward compatibility is not promised by default.** A v3-only app encountering a v5 document errors out with a clear "this document was saved by a newer version of Stardust" message. A flag may opt into best-effort forward load for power users.

6. **Schema version bumps are reviewable changes.** The PR that introduces a new schema version must include: the migration function, tests covering at least one realistic document at the prior version, and an entry in `docs/schemas/CHANGELOG.md`.

7. **Cross-app protocols use the same model.** IPC payloads between Pit and plugin workers (ADR-0002), and eventually wire formats between Pit and Galaxy, carry the same `schema_version` discipline.

8. **Persistence format is JSON for now.** Reasoning: human-inspectable during debugging, every editor can open it, easy to version-control alongside scores in user repos, performance is not the bottleneck for these files (they're loaded once at show open, not per-sample). Move to a binary format (e.g., msgpack, postcard) only if profiling shows persistence is a real bottleneck.

## Consequences

**Easier:**
- Old documents continue to load forever (subject to maintenance of the migration chain)
- Format evolution doesn't require waiting for a major version bump
- Reviewing a schema change forces an explicit migration discussion, which catches design mistakes early
- Debugging a corrupted file is straightforward — open it, inspect the header
- File format becomes part of the public API surface with proper change management

**Harder:**
- The migration chain accumulates over time; we will eventually have v1→v2→...→vN. Long migration chains have to actually run during load, and have to keep working.
- Every developer must remember the rule: "if you change a persisted struct, bump the schema and write the migration."
- Tests for migrations have to be maintained against real-shaped historical documents, not just synthetic minimal ones.
- Cross-cutting refactors that touch multiple persisted types require multiple migrations.

**New obligations:**
- Maintain `stardust-core` migration framework (proposed crate: `overture-schema` / future `stardust-schema`)
- Maintain a corpus of realistic historical documents under `stardust-core/crates/.../tests/fixtures/` covering each prior schema version
- Document the migration story in `docs/schemas/` (separate from ADRs — ADRs cover the decision, `docs/schemas/` covers the format itself)
- Add a CI check that fails any PR which modifies a versioned struct without bumping the schema or providing a migration

## Alternatives considered

### Implicit migration via serde defaults

Works for adding optional fields. Falls apart immediately for renames, type changes, or removed fields. Reviewer also has no signal that a schema-affecting change happened. Rejected.

### Semantic versioning of the app dictates document compatibility

Couples document format to release cadence — a small format tweak forces a major version bump, or a major version bump forces breaking format changes. Document format and app version are different concerns. Rejected.

### Single global `schema_version` across all kinds

Forces a bump for every file in the ecosystem whenever any one format changes. Migrations become artificially intertwined. Rejected.

### Use protobuf / Cap'n Proto / FlatBuffers

These solve forward/backward compatibility at the wire-format level via field numbers. Real benefit, but:

- Binary formats hurt debuggability for user-edited files
- Schema-as-IDL forces a tooling layer
- Migrations still needed for semantic changes that aren't just field additions
- The wins compound at high throughput, which doesn't apply to once-per-load show files

Worth revisiting for the **IPC protocol** specifically (Pit ↔ plugin workers, Pit ↔ Galaxy) where binary efficiency matters more than human inspectability — that's a separate decision and can land in a later ADR if it makes sense.

## Revisit trigger

- If migrations become a significant percentage of the codebase or routinely break, consider whether the underlying data model has factoring problems (often the real fix isn't a better migration, it's a cleaner model)
- If we add a fundamentally different persistence target (e.g., live sync to Galaxy with conflict resolution), revisit whether schema versioning is sufficient or whether we need a true CRDT/operational-transform layer
- If IPC throughput becomes a measurable problem, revisit JSON-vs-binary for that specific surface
