"""Test per scripts/check_version.py — extract_version.

Regressione critica: il bug v0.9.5 ritornava sempre la prima versione
testuale (v0.1.0 in cima al file) invece della massima semver.
"""
import textwrap
from pathlib import Path

import pytest

import check_version


def _write_notes(tmp_path: Path, body: str) -> Path:
    skill_root = tmp_path / "skill"
    notes_dir = skill_root / "references"
    notes_dir.mkdir(parents=True)
    (notes_dir / "release-notes.md").write_text(body, encoding="utf-8")
    return skill_root


def test_returns_max_semver_not_first(tmp_path):
    """Bug v0.9.5: v0.1.0 in cima al file non doveva essere ritornata."""
    body = textwrap.dedent("""\
        # Release Notes

        ## v0.1.0 — 2026-04-29
        ### Aggiunto
        - prima release.

        ## v0.9.5 — 2026-05-15
        ### Cambiato
        - fix regex.

        ## v0.5.0 — 2026-05-02
        ### Aggiunto
        - feature x.
    """)
    skill_root = _write_notes(tmp_path, body)
    assert check_version.extract_version(skill_root) == "v0.9.5"


def test_returns_unknown_if_file_missing(tmp_path):
    skill_root = tmp_path / "skill"
    skill_root.mkdir()
    assert check_version.extract_version(skill_root) == "unknown"


def test_returns_unknown_if_no_versions(tmp_path):
    body = "# Release Notes\n\nNessuna versione qui.\n"
    skill_root = _write_notes(tmp_path, body)
    assert check_version.extract_version(skill_root) == "unknown"


def test_ordering_double_digits(tmp_path):
    """v0.10.0 deve essere maggiore di v0.9.5."""
    body = textwrap.dedent("""\
        # Release Notes

        ## v0.9.5 — 2026-05-15
        ## v0.10.0 — 2026-06-01
        ## v0.10.3 — 2026-06-15
        ## v0.9.9 — 2026-05-30
    """)
    skill_root = _write_notes(tmp_path, body)
    assert check_version.extract_version(skill_root) == "v0.10.3"


def test_major_versions(tmp_path):
    body = textwrap.dedent("""\
        # Release Notes

        ## v1.0.0 — 2026-07-01
        ## v0.9.5 — 2026-05-15
        ## v2.3.1 — 2026-12-01
        ## v0.1.0 — 2026-04-29
    """)
    skill_root = _write_notes(tmp_path, body)
    assert check_version.extract_version(skill_root) == "v2.3.1"


def test_single_version(tmp_path):
    body = "# Release Notes\n\n## v0.1.0 — 2026-04-29\n"
    skill_root = _write_notes(tmp_path, body)
    assert check_version.extract_version(skill_root) == "v0.1.0"


def test_ignores_non_version_h2(tmp_path):
    """Sezioni come '## Formato' o '## Regole' non devono essere parsate."""
    body = textwrap.dedent("""\
        # Release Notes

        ## Formato
        bla bla

        ## v0.9.5 — 2026-05-15
        - fix

        ## Regole
        - una voce per release
    """)
    skill_root = _write_notes(tmp_path, body)
    assert check_version.extract_version(skill_root) == "v0.9.5"
