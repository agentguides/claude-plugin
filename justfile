# agentguides/claude-plugin task runner.
# `guide-cli` (the render dep) resolves from the sibling ../runtime checkout
# via [tool.uv.sources]; `uv run` provisions the dev group automatically.

# List available recipes.
default:
    @just --list

# Run the plugin test suite.
test:
    uv run pytest

# Regenerate the rendered walk Skill triple (skills/{walk,walk-observer,walk-inline}/SKILL.md).
render:
    uv run python scripts/render_plugin_skills.py
