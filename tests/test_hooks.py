"""`hooks/hooks.json` declarative hook registration.

The plugin must wire walk-observer audit reconstruction on every relevant
Claude Code lifecycle event. The hook command goes through the portable
`guide hook walk-observer` CLI subcommand (binary on PATH) rather than an
absolute path or `${CLAUDE_PLUGIN_ROOT}/scripts/...` — the runtime owns
the implementation.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HOOKS_JSON = PLUGIN_ROOT / "hooks" / "hooks.json"

EXPECTED_EVENTS = ("PreToolUse", "PostToolUse", "UserPromptSubmit", "Stop")
EXPECTED_COMMAND = "guide hook walk-observer"

# The walk_* auto-approve entry: pre-approves the plugin's own MCP state ops
# (they only touch guide-managed run files). Inline `echo` keeps the
# no-${CLAUDE_PLUGIN_ROOT} / no-script-path portability invariant.
APPROVE_COMMAND_PREFIX = "echo "


def _is_approve_hook(hook: dict) -> bool:
    return hook.get("command", "").startswith(APPROVE_COMMAND_PREFIX)


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
    anywhere `guide` is on PATH. The one sanctioned exception is the inline
    walk_* auto-approve `echo` (self-contained, equally path-free)."""
    hooks = _load().get("hooks", {})
    for event, entries in hooks.items():
        if event not in EXPECTED_EVENTS:
            continue
        observer_commands = []
        for entry in entries:
            for hook in entry.get("hooks", []):
                assert hook["type"] == "command", (
                    f"{event} hook type must be 'command', got {hook['type']!r}"
                )
                if _is_approve_hook(hook):
                    continue
                assert hook["command"] == EXPECTED_COMMAND, (
                    f"{event} command must be {EXPECTED_COMMAND!r}, "
                    f"not {hook['command']!r}"
                )
                observer_commands.append(hook["command"])
        assert observer_commands, f"{event} lost its walk-observer wiring"


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
    all tool calls to reconstruct the audit log; only the walk_* auto-approve
    entry is allowed a narrower matcher."""
    hooks = _load()["hooks"]
    for event in ("PreToolUse", "PostToolUse"):
        for entry in hooks[event]:
            if all(_is_approve_hook(h) for h in entry.get("hooks", [])):
                continue
            assert entry.get("matcher") == ".*", (
                f"{event} entry should match all tools (.*); got "
                f"{entry.get('matcher')!r}"
            )


def _approve_entries() -> list[dict]:
    return [
        entry
        for entry in _load()["hooks"]["PreToolUse"]
        if all(_is_approve_hook(h) for h in entry.get("hooks", []))
    ]


def test_walk_approve_entry_matches_all_install_shapes() -> None:
    """The auto-approve matcher must cover the walk_* tools under every name
    Claude Code can assign the server: plugin-scoped (any plugin name) and
    standalone — and must not leak approval to anything else."""
    entries = _approve_entries()
    assert len(entries) == 1, "expected exactly one walk_* auto-approve entry"
    matcher = re.compile(entries[0]["matcher"])
    covered = (
        "mcp__plugin_guide_guide__walk_append_event",
        "mcp__plugin_agent-guides_guide__walk_update_step",
        "mcp__guide__walk_read_step",
        "mcp__guide__walk_current",
        "mcp__guide__walk_load_run",
        "mcp__guide__walk_list_runs",
    )
    for name in covered:
        # fullmatch: robust whether the harness applies search or full-match
        # semantics to hook matchers (docs write MCP matchers with `.*`).
        assert matcher.fullmatch(name), f"matcher must cover {name}"
    not_covered = (
        "Bash",
        "mcp__guide__other_tool",
        "mcp__other__walk_read_step",
        "xmcp__guide__walk_read_step",
    )
    for name in not_covered:
        assert not matcher.search(name), f"matcher must NOT cover {name}"


def test_walk_approve_command_emits_allow_decision() -> None:
    """Run the inline command exactly as Claude Code would (via the shell) and
    assert it prints a valid PreToolUse allow decision."""
    (entry,) = _approve_entries()
    (hook,) = entry["hooks"]
    out = subprocess.run(
        hook["command"], shell=True, capture_output=True, text=True, check=True
    ).stdout
    decision = json.loads(out)["hookSpecificOutput"]
    assert decision["hookEventName"] == "PreToolUse"
    assert decision["permissionDecision"] == "allow"
    assert decision["permissionDecisionReason"]
