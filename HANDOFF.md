# Stardust — work in progress handoff

**Last updated:** 2026-05-28 (post realignment: full kanban backlog + completed-work back-creation + decisions ledger moved to docs)
**Purpose:** Lightweight pointer for whoever (or whichever chat) picks up Stardust work next. Current state + next task + how to bootstrap. Everything else lives in the canonical sources below.

> ## Source of truth (read in this order)
>
> 1. **GitHub Project board** — https://github.com/orgs/StardustMT/projects/1 — every feature, tech-debt item, and shipped work item as a milestone-tagged issue. Source of truth for *progress + scope*.
> 2. **Docs site** — https://stardustmt.github.io/docs/pit/ — what each feature is and why. Roadmap, per-feature pages, concept docs, widget catalog, screens, architecture, reliability, ecosystem, and the [locked-decisions reference](https://stardustmt.github.io/docs/pit/decisions/).
> 3. **ADRs** — `docs/adr/` — fully-argued decision records with revisit triggers.
> 4. **CLAUDE.md** — durable conventions + SDLC rules (three living docs, issue hygiene, refinement + review sessions, Storybook-first, accessibility, etc.).
> 5. **This file (HANDOFF.md)** — what's in flight + how to start the next chat. Nothing more.

---

## Current state

- **Shipping**: v0.5.0 (multi-plugin chain hosting via `engine_graph` Plan)
- **Board**: 121 issues. v0.1.0–v0.5.0 back-filled and ✅ Done; v0.6.0–v1.0.0 milestoned with acceptance criteria; Estimate + Priority set on the v0.6.0/v0.7.0 horizon. Later versions get those at refinement.
- **Next chunk**: v0.6.0 engine completeness — see issues filtered by milestone v0.6.0 on the board

## What's in flight right now

**Nothing.** Doc rewrite + kanban backlog + field policy realignment are done. The next chunk is the v0.6.0 pre-feature refinement session per CLAUDE.md, then implementation.

---

## Next chat — bootstrap prompt

Paste this into a fresh `/clear`-ed session:

> Resuming Stardust work — **v0.6.0 engine completeness**. Read `HANDOFF.md` + `CLAUDE.md` first. Then the [Pit roadmap v0.6.0 entry](https://stardustmt.github.io/docs/pit/roadmap/#v060--engine-completeness) and the v0.6.0 issues on the [project board](https://github.com/orgs/StardustMT/projects/1) (filter milestone v0.6.0). Docs site + board are the source of truth. Walk through the **pre-feature refinement session** per CLAUDE.md: go issue-by-issue (#1–#11 + #18), surface ambiguities, write refined acceptance criteria + a "Refinement notes" section into each issue, set Estimate + Priority, flip Status 🔍 Under refinement → 📋 Planned as you lock each. Spawn cross-linked sub-issues for anything new. Don't write code until the refinement pass is done.

---

## Resuming on a different machine

```bash
# 1. Pull every repo
cd ~/projects/stardust && git pull
cd stardust-pit && git pull --tags
cd ../stardust-core && git pull --tags
cd ../stardustmt.github.io && git pull

# 2. JS deps (once per machine / after package.json changes)
cd ../stardust-pit && bun install
cd ../stardustmt.github.io && bun install

# 3. Verify
bun ui:build-storybook
cd ../stardust-core && cargo check --workspace

# 4. Run
cd ../stardust-pit && bun dev
```

Then open a fresh Claude Code chat in the meta-workspace and use the bootstrap prompt above.

---

## Working efficiently with Claude on this project

- **Start a fresh chat per chunk of work** — long threads dominate cost
- **End a chat by asking me to update HANDOFF** before `/clear` — keep HANDOFF lightweight, push everything else into issues + docs
- **CLAUDE.md's terseness directives** keep prose minimal — don't remove them
- **Be specific** — "Refine v0.6.0 issue #5" is cheaper than "what should we do next?"
- **Refinement sessions are explicit** per CLAUDE.md — at the start of each version, walk through the issues + roadmap and lock in details before code
