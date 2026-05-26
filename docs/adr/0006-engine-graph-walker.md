# ADR-0006: Engine graph-walker and realtime execution model

- **Status:** Proposed
- **Date:** 2026-05-22
- **Deciders:** @ChaseCondon
- **Affects:** stardust-pit, stardust-core (stardust-dsp)

## Context

Since v0.7 the engine has been "patch-driven": `engine_start_from_patch` takes a whole `Patch` from the show store but only walks its graph far enough to find the first `instrument.plugin` node, lifting that node's plugin choice into a single-plugin `StartConfig`. Everything else in the graph — additional instruments, MIDI processors (transpose, mix), audio effects (EQ, mix), composite blocks, multiple keyboard zones, the sink — is ignored at runtime even though the patch editor lets users draw it. v0.8a made the engine always-on and patch-following, which highlighted the gap: switching between patches reliably loads the *first* instrument in each but silently drops the rest of the user's wiring on the floor.

Multi-plugin chain hosting is what closes that gap. It is also the largest of the open audio-path items in HANDOFF.md — the rest (rebind glitches, plugin-GUI hosting, scan caching, on-screen-keyboard polish) sit on top of it.

The forces:

- **The patch editor's data model is already richer than the engine.** Wires, ports, composites, zone-typed keyboard outs, MIDI processors, and audio effects all exist in `stardust-patch::PatchGraph` (ADR-0004). The data is complete; only the consumer is incomplete.
- **Realtime constraint.** The audio callback runs at audio priority on the cpal thread and cannot allocate, lock, or call back into the OS. Whatever runs there has to be pre-built. A naïve "interpret the graph each block" is allocation-heavy on the wrong side of the contract.
- **`!Send` plugin instances.** clack-host's `PluginInstance<H>` is `!Send`. Today's engine thread already pins itself to keep that constraint; multi-plugin just means holding `Vec<PluginInstance>` instead of one. No new architectural problem — the existing pattern scales.
- **Composite blocks.** The data model lets composites act as wire endpoints (wires can target the composite's id and a promoted port id). The engine doesn't need to preserve that abstraction at runtime — it can pre-flatten composites into their constituent nodes once at plan-build time.
- **Audio effects need actual DSP.** `audio.eq` exists in the UI catalog but has no implementation anywhere. Multi-plugin hosting that ignores effect nodes wouldn't be useful — the seed-data patches all chain `piano → eq → mix → out`. We need real DSP for the catalog nodes the engine doesn't delegate to a plugin.
- **Hardware MIDI routing is not yet a per-source-node concept.** v0.7's UI has one MIDI-input picker on the EnginePanel feeding the (single) plugin. With multiple source nodes in the graph, "where does the hardware controller plug in?" becomes ambiguous. We need a simple, defensible default that doesn't paint us into a corner.

The naïve alternative — keep growing `engine.rs` to special-case more node kinds — leaves the audio callback doing graph traversal at audio rate and gets messier with every node kind we add. Instead, factor the traversal out of the realtime path: build an executable plan from the graph once at engine-start (or patch-switch), then run that plan in the callback with zero allocation.

## Decision

**Introduce an `engine_graph` module in `stardust-pit/src-tauri/src/` that transforms a `PatchGraph` into an executable `Plan` at engine-start time. The audio callback executes the plan; the plan owns all pre-allocated buffers, plugin instances, native DSP nodes, and routing tables. `engine.rs` becomes a thin shell over `Plan`: it accepts a `PatchGraph` plus routing config, hands it to the plan builder, and on success runs the plan inside the existing audio callback.**

Concretely:

### 1. Module location

`stardust-pit/src-tauri/src/engine_graph.rs`. Lives alongside `engine.rs` rather than as a new core crate. The graph-walker has one consumer today (Pit) and depends on Pit-internal concerns (cpal `AudioSpec`, the same `StardustHost` from `stardust-core::plugin::clap`). CLAUDE.md is explicit that we build only what Pit needs in the current iteration; if Sheets or another app gains a graph engine later, extract at that point. Until then, the module is internal.

The module re-exports nothing public to the React UI directly — the Tauri command surface continues to be `engine_start_from_patch` / `engine_stop` / `engine_status` / `engine_send_midi`, with `EngineStartError` growing additional structured variants for plan-build failures (see §6).

### 2. Plan-builder pipeline

The transform runs sequentially at engine-start. Each step is fallible; failures collect into a `PlanBuildError` set so the UI can show every problem at once (mirroring `stardust-patch`'s collect-all validation style per ADR-0004):

1. **Flatten composites.** Walk `graph.composites`; for each `CompositeBlock`, rewrite every wire whose `from_node` or `to_node` is the composite id into a wire targeting the corresponding `internalNode` / `internalPort` from the matching `PromotedPort`. Composites disappear from the working graph entirely after this step. Locked status is informational for the UI only and is irrelevant to execution.
2. **Resolve nodes to `NodeKind` runtime variants.** Each `GraphNode` becomes one `PlannedNode` based on its kind. `instrument.plugin` nodes with missing/empty plugin config become a `Silent` placeholder rather than a hard failure (the UI already shows "no plugin picked" badges; failing the whole plan to load would be too strict).
3. **Topological sort the audio-data dependencies.** Build a DAG from audio-typed wires only (MIDI wires don't form ordering constraints — they're event-routed, not buffer-routed). Detect cycles; a cycle is a fatal `PlanBuildError::AudioCycle`. The resulting order is what the audio callback iterates.
4. **Pre-allocate per-edge audio buffers.** Each audio wire gets a `[f32; MAX_FRAMES]` L/R pair stored in a `Vec<StereoBuffer>` indexed by `BufferId`. Each `PlannedNode` records the `BufferId`s for its inputs and outputs. Allocation happens once here; the callback only borrows.
5. **Build MIDI fan-out / fan-in tables.** For each node with MIDI inputs, record the list of upstream MIDI source nodes (after MIDI processor transforms). For each node with MIDI outputs (keyboards, sources, MIDI processors), record downstream MIDI consumers. Zone-typed outs carry their `fromNote..toNote` range so filtering is a single integer compare per event.
6. **Instantiate plugins and native DSP nodes.** Each `instrument.plugin` is loaded + activated via the same clack-host path the v0.7 engine used. Each `instrument.sine` / `audio.eq` / `audio.mix` gets its native runtime state. Failures here (plugin won't load, plugin won't activate) are reported per-node; the plan can still partially load and run with silenced failed nodes — same philosophy as missing-config nodes.

The output is a `Plan` struct held in the engine thread's `Running` bundle.

### 3. Plan runtime shape

```rust
pub struct Plan {
    nodes: Vec<PlannedNode>,      // in topological order
    edges: Vec<StereoBuffer>,     // pre-allocated audio buffers
    midi_routes: MidiRouting,     // source-node → consumer-node fan-out, with zone filters
    sinks: Vec<SinkBinding>,      // which edge(s) feed cpal output
    hw_midi_target: Option<NodeIndex>, // first source.keyboard node, or None
}

enum PlannedNode {
    Source { kind: SourceKind /* keyboard | sustain-pedal | … */ },
    MidiTranspose { semitones: i32 },
    MidiMix,
    Plugin { instance: PluginInstance<StardustHost>, started: StartedAudioProcessor, in_events: EventBuffer, out_events: EventBuffer, in_l: …, in_r: …, out_buffer_id: BufferId, /* … */ },
    Sine { state: SineSynthState, out_buffer_id: BufferId },
    Eq { state: EqState, in_buffer_id: BufferId, out_buffer_id: BufferId },
    AudioMix { in_buffer_ids: Vec<BufferId>, out_buffer_id: BufferId },
    SinkMainOut { in_buffer_id: BufferId },
    Silent, // placeholder for missing-config / failed-to-load nodes
}
```

Per audio block the callback:

1. Drains hardware-MIDI ring + UI-MIDI ring into a scratch event list.
2. Pushes those events into the `hw_midi_target` source node's outbound queue (when present).
3. Runs MIDI routing: for each source/processor node, fan its outbound events through `midi_routes` to consumer nodes' inbound event buffers, applying zone filters and transposes inline. MIDI processors execute here, not as separate audio-rate steps.
4. Iterates `nodes` in topological order. For each node, runs its audio process step (plugin process, sine render, EQ process, mix sum). Outputs land in the node's output `BufferId`s.
5. Sums the sink's input buffers into the cpal interleaved output.

Zero allocation, no locks. All buffers, event buffers, route tables, plugin handles are pre-built.

### 4. Native DSP — what `stardust-dsp` gains

This ADR includes shipping the missing DSP, not just the graph walker. Per the scope decision above v0.8b is the everything-in-the-catalog version:

- **`instrument.sine`** reuses the existing polyphonic sine + ADSR from `stardust-dsp` (the v0.5 POC `stardust-poc-play` already proves it works end-to-end). Wrap it in a `SineSynthState` that consumes MIDI events and writes stereo audio per block.
- **`audio.eq`** gets a new 3-band stereo EQ in `stardust-dsp` (low / mid / high gain in dB, fixed crossover frequencies for v1). Biquad-based; allocation-free per block. Config keys (`low`, `mid`, `high`) match the catalog default `{ low: 0, mid: 0, high: 0 }` and are parsed at plan-build time.
- **`audio.mix`** is a straight summation of N stereo input pairs into one stereo output — no DSP crate needed beyond the runtime in `engine_graph`.
- **`midi.transpose`** and **`midi.mix`** are MIDI-routing transformations applied in step 3 of the per-block callback, not standalone DSP. `transpose` shifts note-on / note-off note numbers; `mix` merges streams.

Crossover frequencies and Q values for the EQ are constants for v1. Per-band frequency / Q editing is a follow-up — the UI doesn't expose them either.

### 5. MIDI routing model

The single hardware MIDI input picker on EnginePanel keeps its current semantics, but the engine now interprets it as **"feed all hardware MIDI events into the first `source.keyboard` node in the patch graph."** The on-screen keyboard / `engine_send_midi` UI source goes through the same entry point, so both controllers see the same downstream routing. If the patch graph has no `source.keyboard` node, hardware MIDI is silently dropped and the on-screen keyboard is silenced; this is consistent with how the current engine behaves when no instrument is configured.

Source nodes that aren't `source.keyboard` (sustain pedal, mod wheel, pitch wheel, etc.) do not receive hardware events in v0.8b. Their wires still exist; they just produce no events because no controller drives them yet. Per-source-node controller assignment is a v0.9 concern — out of scope.

CC / pitch-bend / channel-pressure passing through the hardware-MIDI ring fan out to consumers the same way notes do: a plugin's `midi-in` port subscribes to its upstream source's full event stream. Filtering (e.g. CC 64 only to sustain-pedal nodes) is not in scope for v0.8b.

### 6. Error surface

`EngineStartError` (in `commands.rs`) grows new structured variants:

```rust
pub enum EngineStartError {
    NoInstrumentNode,          // already exists; kept for compatibility but the
                               // semantics shift — see Consequences
    MissingPluginConfig { node: String },  // already exists; per-node, may report multiple
    PlanBuild { errors: Vec<PlanBuildError> },  // new — collects every plan-build issue
    Engine { message: String },  // already exists
}

pub enum PlanBuildError {
    AudioCycle { involved_nodes: Vec<String> },
    UnknownWireEndpoint { wire: String, side: &'static str },  // "from" | "to"
    DanglingCompositePort { composite: String, port: String },
    PluginLoadFailed { node: String, message: String },
    PluginActivationFailed { node: String, message: String },
    EqConfigInvalid { node: String, message: String },
    TransposeConfigInvalid { node: String, message: String },
}
```

Dangling wires and silenced nodes are *not* errors — they're acceptable patch states. Hard errors are reserved for things that prevent the plan from being executable: cycles in the audio DAG, plugin failures, malformed config on a node that's actually in the active dataflow.

### 7. Status surface

`EngineStatus::Running` grows to carry the list of hosted plugins and the count of audio effects instead of singular `plugin_name` / `plugin_id`:

```rust
EngineStatus::Running {
    plugins: Vec<HostedPluginStatus>,  // name, id, vendor per loaded plugin
    native_nodes: NativeNodeCounts,    // { sine, eq, audio_mix, midi_transpose, midi_mix }
    midi_input: Option<String>,
    audio_output: String,
    sample_rate: u32,
    channels: u16,
    dropped_events: usize,
    sample_rate_mismatch: bool,
}
```

The UI's `EnginePanel` renders the plugin list as chips and the native-node counts as a summary. Single-plugin patches look indistinguishable from v0.7 except the panel uses the plural surface.

## Consequences

**Easier:**

- Every node the patch editor can draw now executes (or is a defensible no-op like silenced unconfigured plugins). The "single-plugin still" loose end from HANDOFF closes completely.
- The audio callback's per-block work is a linear iteration over a pre-sorted node list with pre-allocated buffers. Adding a new node kind in the future is one variant on `PlannedNode` + one match arm in the callback — no surgery on the realtime path.
- Composites stop being a runtime concern. Pre-flattening means the realtime path never sees a `CompositeBlock`, which removes a whole category of cycle / lookup bugs.
- Native DSP additions (sine, EQ) ship inside `stardust-dsp` where the existing sine+ADSR already lives. No new crate.
- Per-node error reporting means a half-broken patch (one plugin failed, the rest is fine) still starts; the UI surfaces which node failed without losing the whole performance.

**Harder:**

- Plugin instantiation time scales with the number of `instrument.plugin` nodes in a patch. v0.8a's rebind glitch (HANDOFF's "rebind glitches audio briefly") gets worse: each patch switch now serially loads N plugins. The smarter strategies (warm-pool, preload across patches in the same song) become more attractive but stay out of scope here. Patch-switch latency on graphs with 3+ plugins is something to measure and revisit.
- Activation memory grows: each `PluginInstance` holds its own audio buffers, parameter state, etc. For 4–6 plugins in a single patch this is fine; for 20+ in a future "load the whole show" model, less fine. Per-show pre-load strategy revisits at that point.
- The EQ frequencies / Q values being constants for v1 means power users may want to tweak them and can't. Acceptable for v0.8b — the patch editor doesn't expose those controls either, so there's no UI gap.
- The "hardware MIDI → first source.keyboard" rule is a defensible default but is invisible to the user. A patch with two `source.keyboard` nodes will silently feed only the first; the second's wiring is dead until per-source-node controller assignment exists. The UI should eventually badge this; v0.8b lives with it.
- `EngineStartError::NoInstrumentNode` becomes slightly less load-bearing: a patch with no instruments isn't an error anymore (it just produces silence), so this variant gets demoted to a warning the UI can ignore. Kept in the enum for serialization compatibility with v0.7's UI, marked deprecated, removed once the UI updates.

**New obligations:**

- The plan-builder's topological sort needs a test suite covering: cycle detection, multi-instrument fan-in to one mix, composite flattening preserving the same edges, zone-typed keyboard outs routing only in-range notes. Tests live in `engine_graph.rs` and use small `PatchGraph` fixtures (no clack-host required — most tests don't instantiate plugins).
- The realtime contract — "the plan, once built, allocates nothing per block" — needs to be enforced by code review and the existing `tracing` warnings on plugin process failures. No automated check today.
- Every new node kind in the catalog requires a matching `PlannedNode` variant + plan-builder arm + callback dispatch. Three places. Same pattern `stardust-patch`'s `NodeKind` enum already imposes; the per-place ergonomics are similar.

## Alternatives considered

### Push the graph walker into `stardust-core` as a new `stardust-engine` crate

Cleanest long-term home: a shared engine surface that Pit, a future Sheets-with-playback, and any other app could consume. Adds a new crate now for a single consumer; the abstractions would be drawn around what Pit happens to need, which is the recipe for the kind of speculative shape CLAUDE.md warns about. The graph-walker is small enough (~600–800 lines including DSP wrappers) that extracting it later when a second consumer materializes is a few hours of work. Rejected for now; revisit when a second consumer exists.

### Interpret the graph each audio block (no pre-built plan)

Smallest code delta — keep `engine.rs`'s shape, just walk the graph in the audio callback. Fails the realtime contract immediately: graph traversal allocates (lookup hashmaps, route fan-out vectors), and per-block traversal also pays the cost of revalidating topological order N times per second. Rejected.

### Audio rate MIDI routing (treat MIDI processors as full nodes in the topo sort)

Conceptually clean — every node is just "process events + audio per block". Loses the optimization of letting MIDI processors execute in the routing pass without buffer allocation; gains nothing because MIDI events aren't sample-locked in v0.8b (we don't carry per-sample timestamps through the routing). Revisit when MIDI timing precision matters (probably tied to per-sample MIDI scheduling, which is a much later concern).

### Reuse `stardust-core::ipc` for inter-node communication

ADR-0002 spec'd shared-memory IPC for out-of-process plugin sandboxing. The graph walker is in-process — every node runs on the engine thread or the audio callback. IPC adds latency and complexity for no benefit here. Out-of-process plugins are a separate ADR; this one is in-process. Rejected.

### Per-source-node controller assignment in the UI (skip the "first keyboard" heuristic)

Cleanest user model — every source node knows which physical controller feeds it. Requires UI work (per-node settings field, MIDI port list scoped per node, persisting the binding into the patch graph), Rust validation, and a migration for existing patches. Big surface for v0.8b; not load-bearing on the core graph-walker work. Defer to a follow-up (probably v0.9 or a "Rig binding" ADR).

### Real-EQ-as-a-CLAP-plugin

Skip writing native EQ DSP — make `audio.eq` a stub that instantiates a bundled CLAP EQ. Avoids the DSP work; but adds a "we ship a bundled plugin" dependency, complicates packaging (which CLAP? license? cross-platform builds?), and the seed-data patches reference `audio.eq` as a first-class node kind. Native DSP for the catalog's listed effects is the right contract. Rejected.

## Revisit trigger

- **Second app needs the graph walker.** Extract `engine_graph` into `stardust-core/crates/stardust-engine` at that point. The internal shapes (`Plan`, `PlannedNode`) should be largely portable; the cpal/clack-host integration probably wraps in a trait the crate doesn't own.
- **Patch-switch latency on N-plugin graphs becomes a complaint.** Trigger work on warm-pool / preload-from-next-patch strategies. Likely a separate ADR for the lifecycle model.
- **Per-sample MIDI timing matters.** Audio-rate routing for MIDI processors becomes necessary; the routing pass moves from per-block to per-sample. Probably tied to MPE or tight tempo-sync work.
- **Plugin chain depth grows past the activation-memory budget.** Per-show pre-load + LRU-eviction strategy revisits.
- **Per-source-node controller assignment ships.** The hardware-MIDI-to-first-keyboard rule retires; the binding becomes a per-node config field and the engine consults it.
- **`EngineStartError::NoInstrumentNode` is a load-bearing UI surface.** If the React side still renders "this patch has no instrument" as a meaningful state, keep the variant. Otherwise demote / remove on the next breaking change to `EngineStartError`.
