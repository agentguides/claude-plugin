"""`hooks/hooks.json` declarative hook registration.

The plugin must wire walk-observer audit reconstruction on every relevant
Claude Code lifecycle event. The hook command goes through the portable
`guide hook walk-observer` CLI subcommand (binary on PATH) rather than an
absolute path or `${CLAUDE_PLUGIN_ROOT}/scripts/...` — the runtime owns
the implementation.
"""

from __future__ import annotations

import json
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HOOKS_JSON = PLUGIN_ROOT / "hooks" / "hooks.json"

EXPECTED_EVENTS = ("PreToolUse", "PostToolUse", "UserPromptSubmit", "Stop")
EXPECTED_COMMAND = "guide hook walk-observer"


def _load() -> dict:
    return json.loads(HOOKS_JSON.read_text(encoding="utf-8"))


def test_hooks_json_exists_and_parses() -> None:
    assert HOOKS_JSON.is_file()
    _load()


def test_all_four_events_wired() -> None:
    hooks = _load().get("hooks", {})
    for event in EXPECTED_EVENTS:
        assert event in hooks, f"hook event {event!r} missing"
        assert hooks[event], f"hook event {event!r} has no entries"


def test_every_hook_invokes_guide_hook_walk_observer() -> None:
    """Load-bearing portability claim: hook commands point at `guide hook
    walk-observer`, NOT an absolute path. Plugin survives moving its tree
    anywhere `guide` is on PATH."""
    hooks = _load().get("hooks", {})
    for event, entries in hooks.items():
        if event not in EXPECTED_EVENTS:
            continue
        for entry in entries:
            for hook in entry.get("hooks", []):
                assert hook["type"] == "command", (
                    f"{event} hook type must be 'command', got {hook['type']!r}"
                )
                assert hook["command"] == EXPECTED_COMMAND, (
                    f"{event} command must be {EXPECTED_COMMAND!r}, "
                    f"not {hook['command']!r}"
                )


def test_no_claude_plugin_root_substitution_in_commands() -> None:
    """`${CLAUDE_PLUGIN_ROOT}` substitution would couple the hook command
    to the plugin install path; the runtime owns the hook script via
    `guide hook walk-observer`, so no substitution is needed (or wanted)."""
    raw = HOOKS_JSON.read_text(encoding="utf-8")
    assert "${CLAUDE_PLUGIN_ROOT}" not in raw, (
        "hook commands must not embed ${CLAUDE_PLUGIN_ROOT}; route through "
        "`guide hook walk-observer` on PATH instead."
    )


def test_pretooluse_and_posttooluse_have_match_all_matcher() -> None:
    """`.*` matcher = fire on every tool. Walk-observer needs visibility into
    all tool calls to reconstruct the audit log."""
    hooks = _load()["hooks"]
    for event in ("PreToolUse", "PostToolUse"):
        for entry in hooks[event]:
            assert entry.get("matcher") == ".*", (
                f"{event} entry should match all tools (.*); got "
                f"{entry.get('matcher')!r}"
            )
