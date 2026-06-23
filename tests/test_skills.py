"""Walk Skill triple invariants.

The plugin ships three pre-rendered `SKILL.md` files:

- `walk/SKILL.md` — router (default_mode=observer)
- `walk-observer/SKILL.md` — observer-mode walk surface (capability=full)
- `walk-inline/SKILL.md` — inline-mode walk surface (capability=low)

Rendered from `guide_cli.resources.render_walk_skill` + `render_router_skill`
at plugin-pack time. These tests pin the load-bearing frontmatter so a future
template refactor doesn't silently break the plugin's Skill surface.
"""

from __future__ import annotations

from pathlib import Path

import frontmatter


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PLUGIN_ROOT / "skills"

WALK = SKILLS_ROOT / "walk" / "SKILL.md"
WALK_OBSERVER = SKILLS_ROOT / "walk-observer" / "SKILL.md"
WALK_INLINE = SKILLS_ROOT / "walk-inline" / "SKILL.md"


def _meta(path: Path) -> dict:
    return frontmatter.loads(path.read_text(encoding="utf-8")).metadata


def test_all_three_skills_present() -> None:
    for path in (WALK, WALK_OBSERVER, WALK_INLINE):
        assert path.is_file(), f"missing Skill: {path}"


def test_all_three_skills_have_yaml_frontmatter() -> None:
    for path in (WALK, WALK_OBSERVER, WALK_INLINE):
        meta = _meta(path)
        assert meta, f"Skill {path.name} has no frontmatter"
        assert meta.get("name"), f"Skill {path.name} missing `name`"


def test_walk_router_declares_default_mode_observer() -> None:
    meta = _meta(WALK)
    assert meta["name"] == "walk"
    block = meta.get("guide", {}).get("runtime", {})
    assert block.get("router") is True, "walk router must declare router: true"
    assert block.get("default_mode") == "observer", (
        f"router default_mode must be 'observer', got {block.get('default_mode')!r}"
    )


def test_walk_observer_skill_carries_observer_full_tuple() -> None:
    meta = _meta(WALK_OBSERVER)
    assert meta["name"] == "walk-observer"
    block = meta.get("guide", {}).get("runtime", {})
    assert block["mode"] == "observer"
    assert block["capability"] == "full"


def test_walk_inline_skill_carries_inline_low_tuple() -> None:
    meta = _meta(WALK_INLINE)
    assert meta["name"] == "walk-inline"
    block = meta.get("guide", {}).get("runtime", {})
    assert block["mode"] == "inline"
    assert block["capability"] == "low"


def test_features_block_present_on_concrete_skills() -> None:
    """The feature list in frontmatter is what Guides use to gate
    `agent-guides.requires:` checks at runtime. Must survive render."""
    for skill in (WALK_OBSERVER, WALK_INLINE):
        block = _meta(skill).get("guide", {}).get("runtime", {})
        features = block.get("features")
        assert isinstance(features, list) and features, (
            f"{skill.name}: guide.runtime.features missing or empty"
        )


def test_skills_carry_no_install_method() -> None:
    """For plugin-shipped Skills, install_method is null (vs. claude-code's
    legacy `skills-dir` / `plugin-dir`). v0.5.6 only ships the plugin path."""
    for skill in (WALK_OBSERVER, WALK_INLINE):
        block = _meta(skill).get("guide", {}).get("runtime", {})
        assert block.get("install_method") is None, (
            f"{skill.name}: install_method must be null in plugin Skills; "
            f"got {block.get('install_method')!r}"
        )
