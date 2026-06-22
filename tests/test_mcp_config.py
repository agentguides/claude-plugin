"""`.mcp.json` declarative MCP server registration.

The plugin's MCP entry tells Claude Code how to spawn `guide mcp` and
which env to pass through. The runtime uses `GUIDE_HARNESS=claude-code`
to tag walk records and to trigger the scope-derivation fallback from
`$CLAUDE_PROJECT_DIR`.
"""

from __future__ import annotations

import json
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MCP_JSON = PLUGIN_ROOT / ".mcp.json"


def _load() -> dict:
    return json.loads(MCP_JSON.read_text(encoding="utf-8"))


def test_mcp_config_exists_and_parses() -> None:
    assert MCP_JSON.is_file()
    _load()


def test_declares_one_server_named_guide() -> None:
    servers = _load().get("mcpServers", {})
    assert list(servers.keys()) == ["guide"], (
        f"expected exactly one server `guide`, got {list(servers.keys())}"
    )


def test_command_is_guide_mcp() -> None:
    """The command must invoke `guide mcp` (binary on PATH; the runtime
    owns the MCP server). No wrapper script — the v0.5.5 wrapper-script
    drift risk is sidestepped by going declarative."""
    server = _load()["mcpServers"]["guide"]
    assert server["command"] == "guide"
    assert server["args"] == ["mcp"]


def test_env_block_tags_harness_as_claude_code() -> None:
    """`GUIDE_HARNESS=claude-code` is the load-bearing tag — every walk
    record gets it, and the runtime's scope-derivation fallback keys off it."""
    env = _load()["mcpServers"]["guide"].get("env", {})
    assert env.get("GUIDE_HARNESS") == "claude-code", (
        f"GUIDE_HARNESS must be 'claude-code', got {env.get('GUIDE_HARNESS')!r}"
    )


def test_env_block_does_not_hardcode_scope() -> None:
    """`GUIDE_SCOPE` is derived by the runtime from `$CLAUDE_PROJECT_DIR`
    when unset; hardcoding it in the plugin would collapse every project's
    walks under one tag. See `MarkdownBackend.start_run` (v0.5.6 fallback)."""
    env = _load()["mcpServers"]["guide"].get("env", {})
    assert "GUIDE_SCOPE" not in env, (
        "GUIDE_SCOPE must NOT be set in .mcp.json — let the runtime derive "
        "it per-project from $CLAUDE_PROJECT_DIR."
    )


def test_env_block_does_not_hardcode_home_paths() -> None:
    """`GUIDE_HOME` / `GUIDE_LIBRARY_PATH` / `GUIDE_STATE_PATH` are intentionally
    omitted so the runtime defaults under `~/.guide/` apply (overridable via
    the operator's shell env). Hardcoding any of them would prevent
    operator overrides from taking effect."""
    env = _load()["mcpServers"]["guide"].get("env", {})
    for forbidden in ("GUIDE_HOME", "GUIDE_LIBRARY_PATH", "GUIDE_STATE_PATH"):
        assert forbidden not in env, (
            f"{forbidden} must NOT be set in .mcp.json — let the runtime "
            "default to ~/.guide/ subdirs (overridable via shell env)."
        )
