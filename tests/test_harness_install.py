"""Harness-install proof: this plugin installs into a real Claude home via the
runtime's OWN packaged installer (`agentguides.setup`), not a bespoke copy.

We point `GUIDE_CLAUDE_PLUGIN_SRC` at THIS repo root (so the installer provisions
this exact tree, no network) and `AG_CLAUDE_HOME` at a throwaway dir, then run the
runtime's `setup(HarnessState.resolve("claude-code"))`. Asserts the activation
contract holds end-to-end: the plugin tree lands under `<home>/plugins/guide/`,
`guide` is enrolled in `enabledPlugins`, and `verify_setup` reports everything OK.

Marked `requires_runtime` and gated by `importorskip("agentguides.setup")` so the
runtime-source-free core suite (`pytest -m "not requires_runtime"`) stays green.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("agentguides.setup")

from agentguides.setup import (  # noqa: E402
    HarnessState,
    InstallStatus,
    setup,
    verify_setup,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.requires_runtime
def test_plugin_installs_into_claude_home_via_runtime_installer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    claude_home = tmp_path / "claude-home"
    # Install THIS repo tree (never the network) into a throwaway Claude home.
    monkeypatch.setenv("GUIDE_CLAUDE_PLUGIN_SRC", str(REPO_ROOT))
    monkeypatch.setenv("AG_CLAUDE_HOME", str(claude_home))

    state = HarnessState.resolve("claude-code")
    report = setup(state)
    assert not report.failures, f"setup reported failures: {report.failures}"

    # 1) Plugin tree provisioned with its manifest.
    manifest = claude_home / "plugins" / "guide" / ".claude-plugin" / "plugin.json"
    assert manifest.is_file(), f"plugin manifest not installed at {manifest}"

    # 2) Enrolled in enabledPlugins.
    import json

    settings = json.loads((claude_home / "settings.json").read_text(encoding="utf-8"))
    assert "guide" in (settings.get("enabledPlugins") or [])

    # 3) The runtime's own verifier reports a clean install.
    verify = verify_setup(state)
    assert all(s.status is InstallStatus.OK for s in verify.statuses), (
        f"verify_setup not clean: {[(s.component_name, s.status) for s in verify.statuses]}"
    )
