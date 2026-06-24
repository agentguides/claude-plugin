"""Harness-install proof: this plugin installs into a real Claude home via the
runtime's OWN packaged installer (`agentguides.setup`), fully offline.

We point `GUIDE_CLAUDE_PLUGIN_SRC` at THIS repo root and `AG_CLAUDE_HOME` at a
throwaway dir, then run the runtime's `setup(HarnessState.resolve("claude-code"))`.
Because a local plugin checkout is given, the runtime synthesizes a local
marketplace and drives the real `claude plugin marketplace add` + `install`
against it — **no network / no public repos** (the hermetic path). Asserts the
activation contract end-to-end: `guide@agentguides` is registered + enabled and
the runtime's own `verify_setup` reports OK.

Marked `requires_runtime` (needs `agentguides.setup`) and skipped when the
`claude` CLI is absent, since the install shells out to it.
"""

from __future__ import annotations

import json
import shutil
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

pytestmark = pytest.mark.skipif(
    shutil.which("claude") is None,
    reason="`claude` CLI not on PATH; the runtime installer shells out to it",
)


@pytest.mark.requires_runtime
def test_plugin_installs_into_claude_home_via_runtime_installer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    claude_home = tmp_path / "claude-home"
    # Install THIS repo tree offline (runtime synthesizes a local marketplace).
    monkeypatch.setenv("GUIDE_CLAUDE_PLUGIN_SRC", str(REPO_ROOT))
    monkeypatch.setenv("AG_CLAUDE_HOME", str(claude_home))

    state = HarnessState.resolve("claude-code")
    report = setup(state)
    assert not report.failures, f"setup reported failures: {report.failures}"

    # 1) `claude` registered the plugin under its marketplace key.
    installed = json.loads(
        (claude_home / "plugins" / "installed_plugins.json").read_text(encoding="utf-8")
    )
    assert "guide@agentguides" in (installed.get("plugins") or {})

    # 2) Enrolled + enabled in settings (claude's object form).
    settings = json.loads((claude_home / "settings.json").read_text(encoding="utf-8"))
    assert (settings.get("enabledPlugins") or {}).get("guide@agentguides") is True

    # 3) The runtime's own verifier reports a clean install.
    verify = verify_setup(state)
    assert all(s.status is InstallStatus.OK for s in verify.statuses), (
        f"verify_setup not clean: {[(s.component_name, s.status) for s in verify.statuses]}"
    )
