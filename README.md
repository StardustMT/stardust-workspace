# Stardust workspace

This is the meta-workspace for the Stardust ecosystem — a set of cross-platform tools for musical theatre production, built around a live-performance VST host.

This repo orchestrates the polyrepo. It does not contain application code.

## Layout

```
stardust/
├── stardust-pit/       # the live-performance host (app)
├── stardust-core/      # shared Rust libraries / SDK
├── stardust-site/      # marketing site + docs (Astro + Starlight)
├── docs/adr/           # architecture decision records
├── scripts/            # bootstrap, update, helpers
├── _wiki-source/       # temporary, being migrated to stardust-site/
├── justfile            # workspace task runner
├── stardust.code-workspace  # VSCode multi-root workspace
├── CLAUDE.md           # instructions for AI coding agents
└── README.md
```

Each app is its own git repo and is versioned independently. Bootstrap clones them as siblings.

## Quickstart

```bash
# clone the workspace meta-repo, then:
just bootstrap   # clones all sibling repos
just update      # pulls latest on all sibling repos
just status      # git status across all repos
just open        # open the VSCode multi-root workspace
```

## GitHub org

Repos live at `github.com/StardustMT/*`. See [docs/adr/0001-polyrepo-meta-workspace-just.md](docs/adr/0001-polyrepo-meta-workspace-just.md) for the rationale.

## Tooling

- **Just** as the task runner (`brew install just` / `cargo install just`)
- **Bun** for the JS side (`curl -fsSL https://bun.sh/install | bash`)
- **Rust** stable, edition 2024 (`rustup`)
- **Tauri 2** for desktop apps
- **VSCode** with the multi-root workspace file

## Why a meta-workspace and not a monorepo?

Independent release cadences, independent CI, independent ownership later. The cost: more orchestration. See [docs/adr/0001-polyrepo-meta-workspace-just.md](docs/adr/0001-polyrepo-meta-workspace-just.md) for the full rationale, including the migration trigger to Moonrepo if/when CI complexity warrants it.

## Licenses

- `stardust-core` (and shared libraries): **MPL 2.0**
- Apps (`stardust-pit`, etc.): TBD — current `LICENSE` files in each repo are placeholders
