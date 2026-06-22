# `guide` — Claude Code plugin

> **Status:** prototype in the `agent-guides` monorepo (`plugins/claude-plugin/`).
> Once verified against a real Claude Code session, this tree extracts cleanly into
> its own repo at `agentguides/claude-plugin`.

User-scoped install of the [`guide-cli`](https://github.com/briancripe/agent-guides)
runtime under Claude Code:

- registers the `guide` MCP server (`mcpServers.guide` via declarative `.mcp.json`);
- surfaces the walk Skill triple (`walk`, `walk-observer`, `walk-inline`) namespaced
  as `/guide:walk` etc.;
- wires walk-observer audit hooks (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`,
  `Stop`) — they're no-ops when `GUIDE_AUDIT_MODE != observer`, safe to leave
  installed across all sessions;
- tags every walk record with `harness: claude-code` + `scope: <basename of
  $CLAUDE_PROJECT_DIR>` so the centralized state backend at `$GUIDE_HOME/state/`
  filters by project.

No per-project setup. No symlink farm. No `.local/` bubble. One user-scope install,
available across every Claude Code session.

## Install

```bash
claude /plugin install <local-path-or-git-url>
# during prototyping in this monorepo:
claude /plugin install ./plugins/claude-plugin
```

Then enable the plugin (one-time, in `~/.claude/settings.json`):

```json
{
  "enabledPlugins": ["guide"]
}
```

Next Claude session loads the plugin's hooks + MCP + Skills automatically.

Prereq: `guide` on PATH. If missing:

```bash
uv tool install guide-cli   # or: pipx install guide-cli
```

## Uninstall

```bash
claude /plugin remove guide
# then remove "guide" from `enabledPlugins` in ~/.claude/settings.json
```

The centralized library + state at `$GUIDE_HOME/` is preserved — uninstalling the
plugin doesn't touch your walk history or installed content. To purge those, use:

```bash
rm -rf ~/.guide/         # nuke everything
rm -rf ~/.guide/state/   # walks only
rm -rf ~/.guide/library/ # library only
```

## On-disk layout

```
~/.claude/                                       Claude Code home (operator)
├── settings.json                                "enabledPlugins": ["guide"]
└── plugins/
    └── guide/                                   THIS plugin (git-managed)
        ├── .claude-plugin/plugin.json
        ├── .mcp.json
        ├── hooks/hooks.json
        ├── skills/{walk,walk-observer,walk-inline}/SKILL.md
        ├── README.md, LICENSE, .gitignore

$GUIDE_HOME (default ~/.guide/)                  runtime home — SHARED with Hermes etc.
├── library/{books,guides}/<id>/
├── state/<run_id>.md                            walk records tagged harness=claude-code + scope=<project>
├── sources.toml
└── cache/                                       content-addressed bundle cache
```

## How it differs from the Hermes plugin

The [Hermes plugin](../hermes-plugin/) is bigger because Hermes has multiple
profiles + a built-in cron. Claude Code has neither, so v0.5.6 deliberately drops
three v0.5.5 surfaces:

- **No symlink-farm view.** Single user-scope install means there's nothing
  per-something to filter. The MCP server reads `$GUIDE_HOME/library/` directly.
- **No `profile.toml`.** No per-profile policy.
- **No cron template.** No Claude-Code-side scheduler. Operator runs `guide sync`
  manually or via their own launchd/systemd entry.

## See also

- [`docs/cli/library.md`](../../docs/cli/library.md) — central library shape.
- [`docs/cli/sources.md`](../../docs/cli/sources.md) — pull sources.
- [`.planning/plans/v0.5.6-claude-plugin.md`](../../.planning/plans/v0.5.6-claude-plugin.md) — design.
