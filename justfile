# agentguides/claude-plugin task runner.
# `agentguides` (the render dep) resolves from the sibling ../runtime checkout
# via [tool.uv.sources]; `uv run` provisions the dev group automatically.

# List available recipes.
default:
    @just --list

# Run the full plugin test suite (includes requires_runtime against the editable runtime).
test:
    uv run python -m pytest

# Run only the runtime-source-free core (proves the tree needs no runtime source).
test-core:
    uv run python -m pytest -m "not requires_runtime"

# Regenerate the rendered walk Skill triple (skills/{walk,walk-observer,walk-inline}/SKILL.md).
render:
    uv run python scripts/render_plugin_skills.py

# Run ruff lint over the tree.
lint:
    uv run ruff check .

# Run all pre-commit hooks over the whole tree.
precommit:
    uvx pre-commit run --all-files

# Run the requires_runtime suite against the BUILT runtime wheel (not the editable path).
# Green == this plugin tree is compatible with that runtime version.
[group('release')]
verify-runtime:
    #!/usr/bin/env bash
    set -euo pipefail
    ( cd ../runtime && rm -rf dist && uv build -q )
    wheel=$(ls ../runtime/dist/agentguides-*.whl | head -1)
    uv sync -q
    uv pip install -q --force-reinstall "$wheel"
    uv run --no-sync python -m pytest -m requires_runtime -q
    uv sync -q   # restore the editable runtime for local dev
    echo "verify-runtime OK against $(basename "$wheel")"

# Validate-for-release (git-clone distribution — no wheel): render is parity-clean,
# version/changelog consistent, full suite green. Echoes "ready to tag".
[group('release')]
build:
    #!/usr/bin/env bash
    set -euo pipefail
    just render
    git diff --exit-code -- skills
    uv run python scripts/check_version_changelog.py
    just test
    echo "ready to tag"

# Dry-run a release: clean tree + version gate (incl. free tag) + build + verify-runtime.
# Prints the tag command but does NOT tag.
[group('release')]
release-dryrun VERSION:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -n "$(git status --porcelain)" ]; then
        echo "release-dryrun: working tree is dirty; commit or stash first" >&2
        git status --porcelain >&2
        exit 1
    fi
    uv run python scripts/check_version_changelog.py {{VERSION}}
    just build
    just verify-runtime
    echo "release-dryrun OK — to tag: git tag -a v{{VERSION}} -m 'release v{{VERSION}}'"

# Preview the next version computed from conventional commits (no writes).
[group('release')]
bump-dry:
    uvx --from commitizen cz bump --dry-run

# Compute the next version from conventional commits and write it into
# .cz.toml + plugin.json + pyproject.toml (no commit, no tag). Follow-ups:
# add the CHANGELOG `## [x.y.z]` entry, commit, `just tag <version>`, and
# bump the guide ref in agentguides/agentguides .claude-plugin/marketplace.json.
[group('release')]
bump:
    uvx --from commitizen cz bump --files-only
    @echo "next: CHANGELOG heading -> commit -> just tag <version> -> bump marketplace ref (agentguides/agentguides)"

# Create the annotated release tag after the version gate passes.
[group('release')]
tag VERSION:
    #!/usr/bin/env bash
    set -euo pipefail
    uv run python scripts/check_version_changelog.py {{VERSION}}
    git tag -a v{{VERSION}} -m "release v{{VERSION}}"
    echo "tagged v{{VERSION}}"
