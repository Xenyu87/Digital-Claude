"""Smoke test per scripts/validate_skill.py — funzioni puliche."""
import textwrap

import validate_skill


def test_parse_frontmatter_valid():
    text = "---\nname: my-skill\ndescription: una skill\n---\n\nbody"
    data, issues = validate_skill.parse_frontmatter(text)
    assert data["name"] == "my-skill"
    assert data["description"] == "una skill"
    assert issues == []


def test_parse_frontmatter_missing_open():
    text = "no frontmatter\nbody"
    data, issues = validate_skill.parse_frontmatter(text)
    assert any("frontmatter mancante" in m for m in issues)


def test_parse_frontmatter_missing_close():
    text = "---\nname: x\nbody senza chiusura"
    data, issues = validate_skill.parse_frontmatter(text)
    assert any("non chiuso" in m for m in issues)


def test_parse_frontmatter_name_too_long():
    name = "a" * 65
    text = f"---\nname: {name}\ndescription: x\n---\n"
    data, issues = validate_skill.parse_frontmatter(text)
    assert any("supera 64 caratteri" in m for m in issues)


def test_parse_frontmatter_name_invalid_chars():
    text = "---\nname: NomeConMaiuscole\ndescription: x\n---\n"
    data, issues = validate_skill.parse_frontmatter(text)
    assert any("non conforme" in m for m in issues)


def test_parse_frontmatter_reserved_word():
    text = "---\nname: my-claude-thing\ndescription: x\n---\n"
    data, issues = validate_skill.parse_frontmatter(text)
    assert any("reserved word" in m for m in issues)


def test_find_headings_basic():
    text = textwrap.dedent("""\
        # Titolo
        ## Sezione A
        ### Sotto
        ## Sezione B
    """)
    headings = validate_skill.find_headings(text)
    titles = [h[2] for h in headings]
    assert "Titolo" in titles
    assert "Sezione A" in titles
    assert "Sotto" in titles


def test_find_headings_skips_code_fence():
    """Heading dentro code fence non devono essere conteggiati."""
    text = textwrap.dedent("""\
        ## Vera Sezione

        ```
        ## Falsa dentro fence
        ```

        ## Altra Vera
    """)
    headings = validate_skill.find_headings(text)
    titles = [h[2] for h in headings]
    assert "Vera Sezione" in titles
    assert "Altra Vera" in titles
    assert "Falsa dentro fence" not in titles


def test_extract_reference_paths():
    text = "vedi references/foo.md e anche references/bar-baz.md"
    refs = validate_skill.extract_reference_paths(text)
    assert refs == {"foo.md", "bar-baz.md"}


def test_extract_asset_globs():
    text = "lancia assets/scripts/deploy-*.sh per deployare"
    globs = validate_skill.extract_asset_globs(text)
    assert "scripts/deploy-*.sh" in globs


def test_validator_smoke_passes_on_real_skill():
    """Il validator stesso, sul repo skill, deve passare con 0 errori."""
    import subprocess
    result = subprocess.run(
        ["python", "scripts/validate_skill.py"],
        cwd=validate_skill.ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"validator fallito:\n{result.stdout}\n{result.stderr}"
