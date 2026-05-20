# ADR-0005: Show document data model

- **Status:** Proposed
- **Date:** 2026-05-20
- **Deciders:** @ChaseCondon
- **Affects:** stardust-core, stardust-pit

## Context

ADR-0004 gave us a patch-graph data model (`stardust-patch`) and ADR-0003 set the schema-versioning convention for persisted files. Patches now have a canonical Rust shape, JSON wire format, and structural validation. But a Stardust *show* is more than one patch — it's an ordered set of songs, each containing one or more patches, plus the rig configuration that maps physical inputs (keyboards, pedals, pads) to the source kinds patches consume, plus any user-saved composite blocks.

Today, all of this lives as hardcoded fixtures in [`stardust-pit/src/src/screens/_seed-data.ts`](../../stardust-pit/src/src/screens/_seed-data.ts). The patch editor only ever sees one `PatchGraph` at a time, and the rig / song outline never round-trips to disk. To ship Open Show / Save Show — the next user-visible feature — we need:

1. A canonical Rust representation of the whole-show shape.
2. A persistence format with schema versioning (per ADR-0003).
3. A wire format the React UI can produce and consume unchanged via the Tauri bridge.
4. A validation pass that catches structural problems before the engine sees them — including the embedded per-patch graphs.

A naive alternative — save individual patches as `.stardustpatch` files and stitch them together at runtime — would force the user to manage a dozen sibling files per show and reinvent a directory-as-show convention on top of the OS file picker. The user-facing primitive is the show, not the patch.

## Decision

**Introduce a new crate `stardust-show` inside the `stardust-core` workspace that owns the show data model, its persistence format, and its validation rules. The Rust types mirror the existing TypeScript shapes in `_seed-data.ts` and the patch editor's `RigSource` / `OutlineSong` types, serialized as camelCase JSON. `Patch` inlines its `PatchGraph` directly; `stardust-show` depends on `stardust-patch` for the graph type and its validator.**

Concretely:

### 1. New crate: `stardust-show`

Lives at `stardust-core/crates/stardust-show/`. Pure data model — depends on `serde`, `serde_json`, `thiserror`, and `stardust-patch`. No audio, IPC, or UI deps. Same shape as how `stardust-patch` is structured.

The umbrella `stardust-core` crate gains a `show` feature (parallel to `patch`) and includes it in `full`. The Tauri host enables `patch` + `show` (or `full`).

### 2. Schema versioning per ADR-0003

```rust
pub struct ShowDocument {
    pub header: Header,    // kind, schema_version, stardust_version, saved_at
    pub show: Show,
}
```

- `kind = "stardust.show"`
- `schema_version = 1` initially
- The header struct is **re-used from `stardust-patch`** via `pub use stardust_patch::Header` — both document types share the exact same header layout, so factoring a third `stardust-schema` crate just to hold one struct would be ceremony. ADR-0004's revisit trigger ("factor out when the second persisted format lands") gets resolved this way: same struct, two consumers, no third crate.

### 3. Show shape

```rust
pub struct Show {
    pub name: String,
    pub songs: Vec<Song>,
    pub rig: Rig,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub saved_blocks: Vec<SavedBlock>,
}

pub struct Song {
    pub id: SongId,
    pub number: u32,
    pub name: String,
    pub patches: Vec<Patch>,
}

pub struct Patch {
    pub id: PatchId,
    pub number: u32,
    pub name: String,
    #[serde(default)]
    pub compound: bool,
    pub graph: stardust_patch::PatchGraph,
}

pub struct Rig {
    pub sources: Vec<RigSource>,
}

pub struct RigSource {
    pub kind: NodeKind,        // re-exported from stardust-patch
    pub label: String,
}

pub struct SavedBlock {
    pub id: BlockId,
    pub name: String,
    pub node_count: u32,
}
```

`SongId`, `PatchId`, `BlockId` are `string_id!` newtypes (transparent serde, distinct in Rust) following ADR-0004's pattern.

**Graph is inlined per patch, not a side-table.** A `Map<PatchId, PatchGraph>` would split one logical object across two structures with no benefit; inlining matches how both the user and the React code think about the shape (a song has patches; a patch has a graph).

### 4. camelCase JSON, no adapter layer

Every struct uses `#[serde(rename_all = "camelCase")]`. Field names match the TS source 1:1 (`savedBlocks`, `nodeCount`, etc.). The Tauri bridge deserializes JSON straight into `ShowDocument` and serializes back without translation.

### 5. Validation collects all errors, walks contained graphs

```rust
impl Show {
    pub fn validate(&self) -> Result<(), Vec<ShowValidationError>>;
}
```

v1 validation rules:

- No duplicate `SongId` within the show.
- No duplicate `PatchId` within the show (not just within one song — patch ids must be unique show-wide so they can be referenced from setlists, transitions, etc.).
- No duplicate `BlockId` within `saved_blocks`.
- Every contained `PatchGraph` passes its own structural validation. Errors from `stardust_patch::ValidationError` get wrapped in a `ShowValidationError::PatchInvalid { patch, errors }` variant so the UI can show "Patch X has 3 problems" rather than a flat list with no context.
- Rig sources are not deduplicated. Two `source.keyboard` entries with different labels is valid (someone with two keyboards), and uniqueness on label alone is too restrictive.

Deferred:

- Cross-reference checks (patches reference rig sources that exist). Patch graphs use `NodeKind` not rig-source-id; the binding from "this keyboard node in this patch" to "the Nord on MIDI port 2" is a future engine concern.
- Setlist / running order beyond song.number. v1 uses the `number` field on `Song` for ordering; explicit ordering tooling waits for a use case.

### 6. Re-exports from `stardust-patch`

`stardust-show` re-exports `PatchGraph`, `Header`, `NodeKind`, and `ValidationError` so downstream consumers (the Tauri host) only have to depend on `stardust-show` for the full surface.

### 7. No mutation API in v1

Same as ADR-0004: `stardust-show` exposes types, parsers, serializers, validator. Mutation lives in the React store. A builder API can come later if there's a second mutating consumer.

## Consequences

**Easier:**

- One file holds a complete show — no sibling-file management, no implicit "this directory is a show" conventions.
- The engine eventually consumes a whole `Show` (or one `Patch` at a time pulled from it) without needing a separate "where does this patch live" lookup.
- Validation is one call: `show.validate()` walks every patch graph and returns one error set with patch context attached.
- Header re-use means ADR-0003 stays clean: two document kinds, one header struct, no `stardust-schema` ceremony crate.

**Harder:**

- Every change to either `_seed-data.ts` shape (rig, song outline) or the patch-graph TS shape requires a paired Rust change. Same mitigation as ADR-0004: TS is the source of truth, Rust is the mechanical mirror, drift is a bug.
- A bad patch graph in any song fails the whole show validation. This is the right default — you don't want to silently load a show with one broken patch and discover it during a performance — but it means the UI needs to surface "show has issues, here they are" rather than "show loaded, patch X disabled."
- Show files will be larger than individual patch files (one show with N patches ≈ N patch files concatenated). JSON, gzip-compressible if it ever matters. ADR-0003 already deferred binary formats.

**New obligations:**

- Maintain `stardust-show` migration chain alongside both the show TS shapes and the patch TS shapes as they evolve.
- Keep a realistic show fixture (`tests/fixtures/lsoh.stardustshow.json` or similar) tracking the current schema.
- When `stardust-patch` bumps its schema version, `stardust-show`'s validation tests need to update to embed the new graph shape.

## Alternatives considered

### Fold show types into `stardust-patch`

`stardust-patch` would expand from "patch graph" to "everything persisted". Loses crate-level cohesion — a graph validator and a show-outline data model have nothing to do with each other beyond happening to be serialized as JSON. Rejected; keep one crate per persisted document kind.

### Many-files-per-show (directory as show)

Each patch is its own `.stardustpatch` file inside a `MyShow/` directory; the directory contains a `show.json` index. Lets you edit one patch without touching the rest of the file. But forces the user to manage a directory of files (one mis-rename and the show breaks), makes "copy a show to another laptop" a directory operation not a file operation, and the engine still has to load the whole thing into memory to run the show anyway. Rejected; single-file beats directory-as-show for a live performance workflow.

### Side-table for graphs (`patches: Vec<{id,name}>, graphs: HashMap<PatchId, PatchGraph>`)

Slightly easier to lazy-load (skip parsing graphs you're not editing), but splits one logical thing into two and the lazy-load argument isn't real — patches are loaded ahead of show start, not on-demand. Rejected.

### Separate `stardust-schema` crate for the shared header

The trigger condition in ADR-0004's revisit list. Defer it: two consumers using the same struct is not enough surface area to justify a third crate. If a third document type (a per-musician config, a setlist override file) lands and the header gains content, factor at that point.

### Auto-generate Rust from TS (or vice versa)

Same trade-off as ADR-0004 rejected this for patches. The Rust shape diverges (newtypes, validation, enum tagging) so a generator either loses those or grows complex. Rejected for now.

## Revisit trigger

- **Cross-reference checks (patch uses a rig source that doesn't exist):** revisit when the engine starts binding rig sources to physical MIDI ports — at that point the binding model exists and validation can check against it.
- **Compound patches:** the `compound: bool` flag on `Patch` is a placeholder for multi-part patches (verse + chorus + bridge in one logical slot). When the React side grows actual support for compound patches, this likely becomes `parts: Vec<PatchPart>` and the flag goes away.
- **`SavedBlock` storage:** v1 keeps just metadata (`id`, `name`, `node_count`). When saved blocks become actual reusable composites the user can drop into patches, they need their own `PatchGraph` subgraph stored with them. Revisit at that point.
- **Single-file size:** if shows grow large enough that re-saving the whole file on every change feels slow, revisit incremental persistence or a separate "graphs" file alongside the index.
- **Header lives in `stardust-patch` and gets re-exported:** factor out to `stardust-schema` when a third persisted document kind lands.
