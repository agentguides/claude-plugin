"""Guard the v0.5.6 deprecation contract.

v0.5.6 deleted `adapters/claude-code/` and the manual-merge settings flow.
This file asserts neither comes back by accident within the plugin repo.

Originally (in the agent-guides monorepo) the second check scanned the
sibling `src/guide_cli/` runtime for stale references to the removed
`adapters/claude-code/settings.json` merge flow. After the standalone
carve, the runtime lives in a separate repo, so this file scopes its
guard to THIS repo's tree: no resurrected `adapters/claude-code/`
directory, and no config/doc here points operators back at the dead
manual-merge settings file.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_adapters_claude_code_directory_is_gone() -> None:
    legacy = REPO_ROOT / "adapters" / "claude-code"
    assert not legacy.exists(), (
        f"v0.5.6 deleted {legacy}; if you're restoring it, remove this "
        f"assertion and the deprecation notice in README.md."
    )


def test_adapter_settings_json_is_not_referenced_in_repo() -> None:
    """The manual `adapters/claude-code/settings.json` merge flow is gone;
    nothing in this repo should tell operators to set it up."""
    bad_files: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git/" in str(path) or "/.venv/" in str(path):
            continue
        if path.suffix not in {".md", ".py", ".json", ".toml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "adapters/claude-code/settings.json" in text and "removed" not in text:
            bad_files.append(str(path.relative_to(REPO_ROOT)))
    # This very test file names the path in prose; exclude it.
    bad_files = [f for f in bad_files if f != "tests/test_no_legacy_paths.py"]
    assert not bad_files, (
        "files still reference the removed adapters/claude-code/settings.json "
        f"merge flow: {bad_files}"
    )
