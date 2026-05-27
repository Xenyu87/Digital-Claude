"""Test per scripts/propose_lesson.py — auto-write voci TBD."""
from pathlib import Path

import propose_lesson


def test_append_creates_file_when_missing(tmp_path):
    log = tmp_path / "AI_AGENT_LOG.md"
    assert not log.exists()
    propose_lesson.append_tbd_entry(
        log, files=["a.ts", "b.ts", "c.ts"], commit_msg="test commit", today="2026-05-15"
    )
    text = log.read_text(encoding="utf-8")
    assert "# AI_AGENT_LOG" in text
    assert "## 2026-05-15" in text
    assert "<TBD pattern_type>" in text
    assert "test commit" in text


def test_append_does_not_duplicate_header(tmp_path):
    log = tmp_path / "AI_AGENT_LOG.md"
    log.write_text(
        "# AI_AGENT_LOG\n\n> Solo errori.\n\n## 2026-05-10\n- vecchia voce\n  Lezione: x\n",
        encoding="utf-8",
    )
    propose_lesson.append_tbd_entry(
        log, files=["a.ts"] * 5, commit_msg="nuovo", today="2026-05-15"
    )
    text = log.read_text(encoding="utf-8")
    assert text.count("# AI_AGENT_LOG") == 1
    assert "## 2026-05-10" in text  # vecchia preservata
    assert "## 2026-05-15" in text  # nuova aggiunta


def test_truncates_file_list_at_10(tmp_path):
    log = tmp_path / "AI_AGENT_LOG.md"
    files = [f"file{i}.ts" for i in range(15)]
    propose_lesson.append_tbd_entry(log, files, "x", "2026-05-15")
    text = log.read_text(encoding="utf-8")
    assert "e altri 5 file" in text
    assert "file0.ts" in text
    assert "file9.ts" in text
    assert "file10.ts" not in text  # tagliato


def test_last_entry_is_tbd_true(tmp_path):
    log = tmp_path / "AI_AGENT_LOG.md"
    log.write_text(
        "# AI_AGENT_LOG\n\n## 2026-05-15\n- **<TBD pattern_type>**: bla\n",
        encoding="utf-8",
    )
    assert propose_lesson.last_entry_is_tbd(log) is True


def test_last_entry_is_tbd_false_if_compiled(tmp_path):
    log = tmp_path / "AI_AGENT_LOG.md"
    log.write_text(
        "# AI_AGENT_LOG\n\n## 2026-05-15\n- **Spreco**: bla\n  Lezione: x\n",
        encoding="utf-8",
    )
    assert propose_lesson.last_entry_is_tbd(log) is False


def test_last_entry_is_tbd_false_if_missing(tmp_path):
    log = tmp_path / "AI_AGENT_LOG.md"
    assert propose_lesson.last_entry_is_tbd(log) is False


def test_last_entry_is_tbd_only_last_counts(tmp_path):
    """Se l'ULTIMA voce e' compilata, ritorna False anche se voci precedenti hanno TBD."""
    log = tmp_path / "AI_AGENT_LOG.md"
    log.write_text(
        "# AI_AGENT_LOG\n\n"
        "## 2026-05-10\n- **<TBD pattern>**: vecchio non compilato\n\n"
        "## 2026-05-15\n- **Errore**: ultimo compilato\n  Lezione: y\n",
        encoding="utf-8",
    )
    assert propose_lesson.last_entry_is_tbd(log) is False


def test_in_git_repo_false_outside(tmp_path):
    assert propose_lesson.in_git_repo(tmp_path) is False


def test_is_skill_repo_true_with_markers(tmp_path):
    """cwd con SKILL.md + references/ e' una skill repo."""
    (tmp_path / "SKILL.md").write_text("# skill", encoding="utf-8")
    (tmp_path / "references").mkdir()
    assert propose_lesson.is_skill_repo(tmp_path) is True


def test_is_skill_repo_false_without_skill_md(tmp_path):
    (tmp_path / "references").mkdir()
    assert propose_lesson.is_skill_repo(tmp_path) is False


def test_is_skill_repo_false_without_references_dir(tmp_path):
    (tmp_path / "SKILL.md").write_text("# skill", encoding="utf-8")
    assert propose_lesson.is_skill_repo(tmp_path) is False


def test_is_skill_repo_false_on_empty_dir(tmp_path):
    assert propose_lesson.is_skill_repo(tmp_path) is False
