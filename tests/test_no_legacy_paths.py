"""Guard the v0.5.6 deprecation contract.

v0.5.6 deletes `adapters/claude-code/` and the manual-merge settings flow;
this file asserts neither comes back by accident. The deeper setup-framework
+ harness teardown is pending (M2 followup), so we don't yet assert
`setup/plugin.py` or `setup/plugin_enrollment.py` are gone — that flag
flips once the full teardown lands.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_adapters_claude_code_directory_is_gone() -> None:
    legacy = REPO_ROOT / "adapters" / "claude-code"
    assert not legacy.exists(), (
        f"v0.5.6 deleted {legacy}; if you're restoring it, remove this "
        f"assertion and the deprecation notice in plugins/claude-plugin/README.md."
    )


def test_adapter_settings_json_is_not_referenced_in_runtime_code() -> None:
    """The manual `adapters/claude-code/settings.json` merge flow is gone;
    no runtime module should be telling operators to set it up."""
    runtime = REPO_ROOT / "src" / "guide_cli"
    bad_files: list[str] = []
    for py in runtime.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        if "adapters/claude-code/settings.json" in text and "removed" not in text:
            bad_files.append(str(py.relative_to(REPO_ROOT)))
    assert not bad_files, (
        "runtime modules still tell operators to merge adapters/claude-code/settings.json: "
        f"{bad_files}"
    )
