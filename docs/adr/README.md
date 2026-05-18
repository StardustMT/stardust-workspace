# Architecture Decision Records

ADRs capture significant architectural decisions across the Stardust ecosystem and why they were made. Each ADR is immutable once accepted — supersede it with a new ADR rather than editing.

## Index

| #    | Title                                                                          | Status   |
| ---- | ------------------------------------------------------------------------------ | -------- |
| 0001 | [Polyrepo with meta-workspace and `just`](0001-polyrepo-meta-workspace-just.md)| Accepted |
| 0002 | [Out-of-process plugin sandboxing](0002-out-of-process-plugin-sandboxing.md)   | Accepted |
| 0003 | [Schema versioning for persisted formats](0003-schema-versioning.md)           | Accepted |

## When to write an ADR

- A change to repo layout, language choice, runtime architecture, or process model
- Adoption (or rejection) of a major dependency, framework, or build tool
- A persistence format change, schema migration, or protocol versioning decision
- Cross-app interface design (Pit ↔ Sheets ↔ Galaxy)
- A reliability or security boundary decision
- Any decision where someone six months later would reasonably ask "why did we do it this way?"

A bug fix, refactor, or feature implementation does **not** need an ADR. Trust commits and code for those.

## Format

Use [`_template.md`](_template.md) as the starting point. Number sequentially with four digits. Statuses:

- **Proposed** — under discussion, not yet committed to
- **Accepted** — current direction
- **Deprecated** — no longer the direction, but not replaced
- **Superseded by ADR-XXXX** — replaced by a later ADR
