# Schema CHANGELOG

Per [ADR-0003](../adr/0003-schema-versioning.md), every persisted-format
schema bump lands here with: the new version, the migration function
location, and a one-line rationale. Entries are append-only; never edit
a shipped migration in place — write a new migration on top.

## stardust.patch

### v2 — 2026-07-03 (v0.6.0, stardust-pit#9)

- Renamed node kind `instrument.sine` → `instrument.testtone`. The
  diagnostic-only built-in synth is no longer surfaced in the
  user-facing palette.
- Migration: `stardust_patch::document::migrate_patch_v1_to_v2` rewrites
  every `graph.nodes[*].kind` field with the old value to the new one.
  Pure JSON value rewrite — runs before typed deserialization so the
  removed `instrument.sine` enum variant cannot reach serde.
- Tests:
  `stardust-core/crates/stardust-patch/tests/migration.rs::v1_sine_node_migrates_to_testtone`,
  plus an end-to-end migration + audio assertion in
  `stardust-pit/src-tauri/src/engine_graph.rs::tests::v0_5_0_sine_show_migrates_and_produces_audio`
  driven by `stardust-pit/src-tauri/tests/fixtures/v0.5.0-sine-show.json`.

### v1 — initial (v0.5.0)

Initial patch-document shape per ADR-0004. Stored as
`{ kind: "stardust.patch", schemaVersion: 1, graph: PatchGraph }`.

## stardust.show

### v2 — 2026-07-03 (v0.6.0, stardust-pit#9)

- Every embedded patch graph runs through the patch v1→v2 migration
  (sine → testtone rename). No fields on the show document itself
  changed.
- Migration: `stardust_show::document::migrate_show_v1_to_v2` walks
  `show.songs[*].patches[*].graph` and reuses
  `stardust_patch::migrate_patch_value`.
- Tests:
  `stardust-core/crates/stardust-show/tests/migration.rs::v1_show_embedded_sine_nodes_migrate_to_testtone`.

### v1 — initial (v0.5.0)

Initial show-document shape per ADR-0005.
