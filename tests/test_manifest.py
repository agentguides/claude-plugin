"""`.claude-plugin/plugin.json` manifest invariants.

Asserts shape required by Claude Code's plugin discovery + the v0.5.6
release coherence checks (version matches pyproject, license is MIT, etc.).
"""

from __future__ import annotations

import json
import re
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"


def test_manifest_exists() -> None:
    assert MANIFEST.is_file(), f"missing manifest: {MANIFEST}"


def test_manifest_parses_as_json() -> None:
    json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_declares_required_name_field() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data.get("name") == "guide", (
        "plugin name must be 'guide' — Claude Code namespaces Skills/etc as "
        "/<name>:<skill>; v0.5.6 plan locks the name."
    )


def test_manifest_version_tracks_pyproject_or_leads() -> None:
    """Drift check: the plugin's version must equal pyproject's (steady state
    between releases) OR be exactly one minor ahead (mid-milestone dev — the
    plugin leads while the runtime bump waits for the M6 release commit).
    Catches accidental version skew without forcing simultaneous bumps."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    plugin_version = data.get("version", "")
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^\s*version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    assert m, "couldn't find version in pyproject.toml"
    runtime_version = m.group(1)

    def _tuple(v: str) -> tuple[int, int, int]:
        parts = v.split(".")
        return (int(parts[0]), int(parts[1]), int(parts[2]))

    plugin_t = _tuple(plugin_version)
    runtime_t = _tuple(runtime_version)
    same = plugin_t == runtime_t
    one_minor_ahead = (
        plugin_t[0] == runtime_t[0]
        and plugin_t[1] == runtime_t[1] + 1
        and plugin_t[2] == 0
    )
    one_patch_ahead = (
        plugin_t[0] == runtime_t[0]
        and plugin_t[1] == runtime_t[1]
        and plugin_t[2] == runtime_t[2] + 1
    )
    assert same or one_minor_ahead or one_patch_ahead, (
        f"plugin version {plugin_version!r} drifted from runtime version "
        f"{runtime_version!r}; allowed: equal, or exactly one minor/patch ahead "
        f"during dev."
    )


def test_manifest_is_marketplace_ready() -> None:
    """The optional metadata fields a Claude Code marketplace publish wants."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data.get("license") == "MIT"
    assert "github.com" in (data.get("repository") or "")
    assert data.get("description"), "description is empty"


def test_manifest_has_no_unknown_top_level_keys() -> None:
    """Defensive: Claude Code's manifest schema is small; keep ours minimal
    so a future schema tightening doesn't reject the plugin."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    allowed = {
        "name",
        "displayName",
        "version",
        "description",
        "license",
        "homepage",
        "repository",
        "keywords",
        "author",
        "authors",
    }
    extras = set(data.keys()) - allowed
    assert not extras, f"unexpected manifest keys: {extras}"
