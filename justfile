# Stardust workspace task runner.
# Run `just` (no args) to see all recipes.

default:
    @just --list

# Clone all sibling repos for the first time.
bootstrap:
    @./scripts/bootstrap.sh

# Pull latest on all sibling git repos.
update:
    @./scripts/update.sh

# Show git status across all sibling repos.
status:
    @for d in */; do \
        if [ -d "$d.git" ]; then \
            printf "\n=== %s ===\n" "$d"; \
            (cd "$d" && git -c color.status=always status --short --branch); \
        fi; \
    done

# Show current branch across all sibling repos.
branches:
    @for d in */; do \
        if [ -d "$d.git" ]; then \
            printf "%-25s %s\n" "$d" "$(cd "$d" && git rev-parse --abbrev-ref HEAD)"; \
        fi; \
    done

# Open the VSCode multi-root workspace.
open:
    code stardust.code-workspace

# Run `cargo fmt` across all Rust repos.
fmt:
    @for d in stardust-core stardust-pit; do \
        if [ -f "$d/Cargo.toml" ]; then \
            printf "=== fmt: %s ===\n" "$d"; \
            (cd "$d" && cargo fmt); \
        fi; \
    done

# Run `cargo clippy` across all Rust repos.
clippy:
    @for d in stardust-core stardust-pit; do \
        if [ -f "$d/Cargo.toml" ]; then \
            printf "=== clippy: %s ===\n" "$d"; \
            (cd "$d" && cargo clippy --all-targets -- -D warnings); \
        fi; \
    done

# Run all tests across the workspace.
test:
    @for d in stardust-core stardust-pit; do \
        if [ -f "$d/Cargo.toml" ]; then \
            printf "=== test: %s ===\n" "$d"; \
            (cd "$d" && cargo test); \
        fi; \
    done

# Build the docs site locally.
docs-dev:
    cd stardustmt.github.io && bun run dev

# Build the docs site for production.
docs-build:
    cd stardustmt.github.io && bun run build
