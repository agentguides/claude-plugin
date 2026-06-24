# Changelog

All notable changes to `agentguides-claude-plugin` are recorded here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [SemVer](https://semver.org/).

## [0.1.0] — 2026-06-23 (first standalone release: repo carve + agentguides rename + release automation)

> Theme: *first release of the `guide` Claude Code plugin as a standalone repo.
> It carves out of the runtime monorepo, picks up the `guide-cli` → `agentguides`
> dist/import rename, and gains release/compat automation so a tagged tree is a
> validated artifact.*

Versioned independently of the runtime: `0.1.0` is the first ecosystem release
(the pre-split `0.5.x` monorepo numbers never shipped). Compatibility with the
runtime is declared by the `requires.version` range below and proven green by
`just verify-runtime`.

### Standalone repo carve

- The `guide` Claude Code plugin moved out of `runtime/plugins/claude-plugin/`
  into its own repo (`agentguides/claude-plugin`). The declarative plugin tree
  (`.claude-plugin/`, `hooks/`, `skills/`), its pytest suite, and the walk-Skill
  renderer came with it.
- `[tool.uv.sources] agentguides = {path="../runtime", editable=true}` resolves
  the runtime from the sibling checkout for local dev; the
  `agentguides>=0.5.9,<0.6.0` dev-group constraint is the `requires.version`
  range — the verified-against runtime a non-editable resolve would use, and
  what `tests/test_requires_version.py` asserts the runtime-under-test satisfies.

### `agentguides` rename

- The runtime dist/import is now `agentguides` (CLI `guide`); the render script
  and `test_skill_render_parity.py` import `agentguides.resources`.

### Release / compat automation

- `CHANGELOG.md` + `scripts/check_version_changelog.py` keep `[project].version`,
  the `.claude-plugin/plugin.json` manifest version, and the changelog in lockstep.
- `just` recipes (`test-core`, `verify-runtime`, `build`, `release-dryrun`, `tag`,
  `precommit`) make "validated, tagged tree" the unit of release (git-clone
  distribution — no wheel).
- `tests/test_harness_install.py` installs this plugin into a throwaway Claude
  home via the runtime's own `agentguides.setup` installer and asserts the plugin
  tree + `enabledPlugins` enrollment + `verify_setup` are clean.
- `ruff` + `[tool.ruff]`/`[tool.ruff.lint]` config (line-length 100, py310,
  select E4/E7/E9/F) mirror the runtime; `.pre-commit-config.yaml` runs ruff,
  the version/changelog check, and a render-drift guard.
