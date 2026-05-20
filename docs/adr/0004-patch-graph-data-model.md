# ADR-0004: Patch graph data model

- **Status:** Proposed
- **Date:** 2026-05-20
- **Deciders:** @ChaseCondon
- **Affects:** stardust-core, stardust-pit

## Context

The patch editor in `stardust-pit` operates on an in-memory TypeScript shape ([`patch-graph/_types.ts`](../../stardust-pit/src/src/components/patch-graph/_types.ts)) that describes a Patch as a directed graph of nodes connected by typed wires. As of v0.4, that graph lives only in React state — it is never persisted, never sent to the audio engine, never validated outside the UI.

The next step of the roadmap (per `HANDOFF.md`) is to give the engine real patches to consume instead of the diagnostic "pick one plugin, hear it" surface that `engine_start` currently takes. That requires:

1. A canonical Rust representation of the patch graph.
2. A persistence format (JSON, per ADR-0003) with schema versioning.
3. A wire format that the existing React UI can produce and consume unchanged via the Tauri bridge.
4. A validation pass that catches structural problems before the engine sees them.

A musician's career depends on patches loading mid-show — file-format mistakes here are expensive to undo, so this lands as an ADR before code.

## Decision

**Introduce a new crate `stardust-patch` inside the `stardust-core` workspace that owns the patch-graph data model, its persistence format, and its validation rules. The Rust types are a faithful mirror of the existing TypeScript shape, serialized as camelCase JSON so the Tauri bridge round-trips with no adapter layer.**

Concretely:

### 1. New crate: `stardust-patch`

Lives at `stardust-core/crates/stardust-patch/`. Pure data model — depends only on `serde`, `serde_json`, `thiserror`. No audio, IPC, or UI deps. Mirrors how `stardust-dsp` / `stardust-midi` / `stardust-audio` are separated by concern.

Rejected the alternative of folding into `stardust-core` itself — that crate is a thin facade today, and giving it real surface area would conflate "ecosystem entry point" with "domain types."

### 2. Schema versioning per ADR-0003

The persisted form is a two-level structure:

```rust
pub struct PatchDocument {
    pub header: Header,        // kind, schema_version, stardust_version, saved_at
    pub graph: PatchGraph,     // nodes, wires, composites
}
```

- `kind = "stardust.patch"`
- `schema_version = 1` initially
- The `Header` struct is defined inside `stardust-patch` for now. If a second persisted format lands (show, song, rig), the header gets factored into a `stardust-schema` crate at that point — not before.

The bare `PatchGraph` is the in-memory shape used by everything that doesn't care about persistence (the engine, validation, future query helpers). The wrapped `PatchDocument` is the on-disk and over-the-wire shape.

### 3. camelCase JSON, no adapter layer

Every struct uses `#[serde(rename_all = "camelCase")]`. Field names match the TS source 1:1. The Tauri bridge will deserialize JSON straight into `PatchDocument` and serialize back without a translation layer.

### 4. ID newtypes

```rust
#[serde(transparent)] pub struct NodeId(pub String);
#[serde(transparent)] pub struct PortId(pub String);
#[serde(transparent)] pub struct WireId(pub String);
#[serde(transparent)] pub struct CompositeId(pub String);
```

Serialize as plain strings (the TS shape uses `string`); give Rust call sites type safety so a `WireId` can't be passed where a `NodeId` is expected. Cheap to add now, expensive to retrofit.

### 5. `PortConfig` is a tagged enum

The TS `PortConfig` is a discriminated union keyed by `kind`. The Rust mirror is `#[serde(tag = "kind", rename_all = "kebab-case")] enum PortConfig` with variants `Zone { fromNote, toNote, colorHue?, wireFollowsColor? }`, `Pad { padIndex, note? }`, `Channel { midiChannel }`, `Stereo { channel: "L" | "R" }`, `Mono`. Clean, strict, mirrors the TS structure exactly.

### 6. `GraphNode.config` is `serde_json::Value`

The TS shape carries node-kind-specific config as `Record<string, unknown>`. The Rust mirror keeps that as `Option<serde_json::Value>` — a passthrough.

**Reasoning:** strong typing per-`NodeKind` belongs at the engine boundary, where the consumer actually needs to know that `instrument.plugin` carries a `uri` and `midi.transpose` carries `semitones`. Doing it here would mean every new node kind requires a coordinated Rust+TS change, and would push schema migration work into the data-model crate for changes the data model doesn't care about.

This decision is the most likely thing in this ADR to be revised. Revisit trigger noted below.

### 7. Validation is separate from deserialization, and collects all errors

```rust
impl PatchGraph {
    pub fn validate(&self) -> Result<(), Vec<ValidationError>>;
}
```

Returns the full set of problems, not just the first. The patch editor will eventually surface these inline, and a "fix-one-error-at-a-time" UX is worse than "show me everything wrong with this patch."

v1 validation rules:

- No duplicate `NodeId`, `WireId`, or `CompositeId`.
- Every wire endpoint references an existing node and an existing port on that node.
- Wire signal kinds match (a `midi` out can only connect to a `midi` in; same for `audio`).
- Wire direction sanity: source endpoint must be a port with `direction: "out"`, destination must be `"in"`.
- Every composite's `contains` list references existing nodes.
- Every composite's `promotedPorts[].internalNode` / `internalPort` references a real node+port in `contains`.
- Each composite's member set forms a connected subgraph (treating wires as undirected).

Deferred to a future ADR:

- Cycle detection. v1 declares "graphs are DAGs" but does not enforce it — there is no engine consumer yet to break.
- Reachability from a source / to a sink. The engine will define what "runnable" means; the data model doesn't need an opinion yet.

### 8. No mutation API in v1

`stardust-patch` exposes types, parsers, serializers, and a validator. It does not expose a builder API for incremental graph editing. The React patch editor owns mutation in TypeScript; the Rust side receives complete graphs.

This is the minimum surface for the engine-consumes-patches feature. A builder API can be added later when there is a second consumer that needs it (CLI tooling, scripted patch generation, etc.).

## Consequences

**Easier:**

- The engine gets a single canonical type to consume — no ad-hoc JSON parsing scattered across `engine.rs`.
- Validation errors surface in one place with one error vocabulary; the UI can render them uniformly.
- The TS / Rust contract is enforced by the serde derive — drift gets caught at compile/test time, not at runtime in the audio thread.
- ADR-0003 migrations have a clean home: each new schema version of `stardust.patch` adds a `migrate_v{N}_to_v{N+1}` in `stardust-patch`.
- Fixture-based round-trip tests give us a regression safety net for the wire format from day one.

**Harder:**

- Every change to the TS `_types.ts` now has to be paired with a Rust change. Mitigated by the fact that the TS source is the authority and the Rust types are a mechanical mirror — divergence is a bug, not a feature.
- `serde_json::Value` inside `GraphNode.config` is escape-valve typing. The engine will need its own per-`NodeKind` config types and a conversion step. This is intentional, but it does mean the type safety stops at the node boundary in this crate.
- The composite "connected subgraph" check is `O(nodes + wires)` per composite and runs on every validation — fine for hand-built patches, worth profiling if generated patches get large.

**New obligations:**

- Maintain `stardust-patch` migration chain alongside the TS shape as both evolve.
- Keep `tests/fixtures/` populated with realistic patch-graph JSON files, including at least one per prior schema version once migrations exist.
- When adding a new `NodeKind`, decide whether the engine's understanding of its config belongs in this crate or in the engine crate. Default answer: engine crate, unless the data model itself needs to reason about it (e.g. for validation).

## Alternatives considered

### Fold into `stardust-core`

Smaller workspace, but `stardust-core` becomes a grab-bag — today it's a thin facade, and the patch graph is a substantial chunk of surface area. Easier to split clean later if it's separate now. Rejected.

### Strongly-type `GraphNode.config` as a tagged enum keyed by `NodeKind`

Catches bad config early and gives engine code a typed view from day one. But it forces every TS-side `NodeKind` addition to land in lockstep with Rust, pushes per-kind config decisions into the data-model crate that doesn't otherwise need them, and means a new schema migration per node-kind addition. The engine will need per-kind types anyway; doing it here would duplicate that work without paying for itself. Rejected for v1; revisit when the engine consumer's needs are concrete.

### Generate the Rust types from the TS source (or vice versa)

Eliminates the manual-mirror obligation. But the TS and Rust shapes aren't actually identical — Rust gets newtypes, enum tagging conventions, and validation that have no TS analog. The translation layer would either lose those, or be complex enough to be its own maintenance burden. Rejected for v1; revisit if drift becomes a recurring source of bugs.

### Binary format (postcard, msgpack) instead of JSON

ADR-0003 already chose JSON for persisted formats with a "revisit when profiling shows it matters" trigger. Patches load once per show-open; not the bottleneck. Rejected.

### Mutation API in v1

Would let Rust-side tooling build patches programmatically. No consumer exists today; the UI owns mutation. YAGNI. Rejected.

## Revisit trigger

- **`serde_json::Value` for node config:** revisit when the engine starts consuming `PatchGraph` and per-kind config typing becomes load-bearing. If the engine's per-kind types end up being a thin wrapper around what could have been in the data model, fold them back in.
- **Connected-subgraph validation cost:** revisit if patch generation tooling (scripted setlists, library imports) produces graphs large enough that validation becomes noticeable.
- **No cycle detection:** revisit when the engine defines what "runnable" means for a graph. Cycle handling (forbidden, allowed-with-delay-node, allowed-with-feedback-attenuator) is an engine-semantics decision, not a data-model decision.
- **Manual TS / Rust mirror:** revisit if drift between the two shapes causes more than one bug per quarter.
- **Header lives in `stardust-patch`:** factor out to `stardust-schema` when the second persisted format (show, song, rig) lands.
