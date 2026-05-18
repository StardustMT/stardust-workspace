# ADR-0001: Polyrepo with meta-workspace and `just`

- **Status:** Accepted
- **Date:** 2026-05-18
- **Deciders:** @ChaseCondon

## Context

The Stardust ecosystem will eventually span multiple independently-shipped products (Pit, Sheets, possibly Rehearse / Stage / Lighting / Galaxy) plus shared infrastructure (stardust-core, a documentation site, and at some point a shared UI library). These products will:

- ship on different cadences
- target different platforms (desktop, mobile, web)
- have different stability guarantees (core libs need semver discipline; the app can iterate freely)
- potentially be developed by different contributors over time

We need a repo strategy that supports all of that without forcing every change to ripple through a monolithic build.

Two real options:

1. **Monorepo** — all code in one repo, one CI, one version, one history.
2. **Polyrepo with a meta-workspace** — each product/library in its own repo, a separate "workspace" repo that orchestrates cloning, tasks, and onboarding.

Monorepos solve real problems (cross-cutting refactors, atomic commits across packages, single CI pipeline) but at this scale and stage they would also:

- couple release cadences artificially
- make it harder to hand off individual products to other maintainers later
- bias toward heavyweight build orchestration (Bazel / Nx / Pants) before there is enough code to justify it
- complicate plugin/SDK separation (consumers of stardust-core shouldn't need to clone the whole ecosystem)

## Decision

**Use a polyrepo with a meta-workspace repo and `just` as the task runner.**

Structure:

```
stardust/                  # this meta-workspace repo
├── stardust-pit/          # app repo, separately cloned
├── stardust-core/         # shared Rust SDK, separately cloned
├── stardustmt.github.io/  # docs + marketing site (GitHub Pages org repo), separately cloned
├── docs/adr/              # cross-ecosystem ADRs live here
├── justfile               # `just bootstrap`, `just update`, `just status`, ...
├── scripts/               # bash helpers backing the justfile
└── stardust.code-workspace
```

The workspace repo orchestrates the polyrepo but **does not own application code**. Each sibling repo is a separate clone with its own `.git`. The workspace repo's `.gitignore` excludes the sibling repos so they don't accidentally get nested-tracked.

Local dev uses **`path` dependencies** between sibling repos (e.g. `stardust-pit/Cargo.toml` references `stardust-core` via `path = "../stardust-core/..."`). This means cross-repo changes can be tested locally without publishing.

The `stardust-core` workspace is published as versioned crates; `stardust-pit` is published as a desktop app (Tauri bundle). They have independent release pipelines.

## Consequences

**Easier:**
- Independent release cadences
- Independent CI per repo (failures don't block unrelated work)
- Cleaner handoff if a product gains its own maintainer
- Cleaner SDK story — external consumers clone only `stardust-core`
- Cheap onboarding via `just bootstrap` then `just open`
- Low cognitive overhead for new contributors

**Harder:**
- Cross-cutting refactors that touch multiple repos require coordinated PRs
- Cross-repo dependency updates are manual (no automatic graph-aware bumps)
- Release coordination across repos is manual
- Affected-project detection in CI is not free — we may rebuild more than necessary

**New obligations:**
- Keep `path` deps and published versions in sync during development
- Document the bootstrap flow clearly (covered in workspace README)
- Maintain the `justfile` and bootstrap scripts as the source of truth for ecosystem tasks

## Alternatives considered

### Monorepo (Bazel)

Powerful but the wrong tool for a solo dev with a few hundred commits. Would consume significant time on build-system maintenance rather than product. Revisit if Stardust ever grows past ~10 engineers with painful CI times.

### Monorepo (Nx)

Strong frontend-first orchestrator. Rust support is secondary, and the conventions are heavily web-framework-flavored. Wrong fit for a Rust-heavy native ecosystem.

### Polyrepo with git submodules / git subtree

Painful UX. New contributors get bitten by submodule state. Subtree is better but still awkward for daily workflow. Bootstrap scripts are simpler and easier to reason about.

### Polyrepo with Google `repo` (Android manifest tool)

Solid choice for large coordinated multi-repo setups, but adds tooling that mostly pays off when repo count and contributor count are high. Defer.

### Polyrepo with Moonrepo from day 1

The strongest alternative. Moonrepo is language-agnostic, Rust-friendly, and offers task graphing / affected-project detection / caching. The downsides are real for our current state:

- We are solo with very small repos — there is no dependency graph worth modeling yet
- Moonrepo's value compounds with team size and CI minutes; we have neither
- Migrating `just` → Moonrepo later is hours of work; designing around Moonrepo and then migrating away is much harder
- Lightweight scripts work better with AI coding agents currently

**See "Revisit trigger" below — Moonrepo is the planned next step when this gets painful.**

## Revisit trigger

Migrate to Moonrepo when any two of these are true:

- CI run times exceed ~10 minutes on a typical PR
- Repo count exceeds 5 actively-developed repos
- Contributor count exceeds 3 active devs
- Cross-repo coordination (releases, schema migrations) becomes a recurring source of pain

When migrating: keep repo-local `justfile`s authoritative; have Moonrepo invoke `just <task>` rather than redefining tasks. Moonrepo orchestrates the ecosystem; it does not define the architecture.
