#!/usr/bin/env python3
"""Validator leggero per la skill cost-aware-app-coordinator.

Esegui dalla root della skill:
    python scripts/validate_skill.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_FILE = ROOT / "SKILL.md"
REFERENCES_DIR = ROOT / "references"
ASSETS_DIR = ROOT / "assets"
RECIPES_DIR = ROOT / "recipes"
TEMPLATES_DIR = ASSETS_DIR / "templates"
SCRIPTS_ASSETS_DIR = ASSETS_DIR / "scripts"

# SKILL.md cap: la doc ufficiale Anthropic (best-practices) impone <500 righe.
# 450 lascia margine di sicurezza senza essere arbitrariamente restrittivo.
SKILL_MAX_LINES = 450
# Reference cap: garantisce che ogni reference sia leggibile in un colpo
# d'occhio e che oltre questa soglia la sezione vada spostata o splittata
# (raccomandazione: TOC se >100 righe).
REFERENCE_MAX_LINES = 120
# Limite ufficiale Anthropic per il campo description del frontmatter.
DESCRIPTION_MAX_CHARS = 1024

REQUIRED_FRONTMATTER_KEYS = {"name", "description"}
# Support both Italian and English section names (v1.1.0: bilingual SKILL)
REQUIRED_SECTIONS = [
    ("Lingua", "Language"),
    ("Fast path",),  # Same in both
    ("Classificazione del task", "Task classification"),
    ("Budget mode",),  # Same in both
    ("Selezione del modello", "Model selection"),
    ("Lettura iniziale del contesto", "Initial context reading"),
    ("Progressive loading",),  # Same in both
    ("Working loop",),  # Same in both
    ("Output economy",),  # Same in both
    ("Gate decisionali e rischio", "Decision gates and risk"),
    ("Specialisti", "Specialists"),
    ("Handoff tra agenti", "Handoff between agents"),
    ("Definition of Done",),  # Same in both
    ("Creazione di una nuova app", "Creating a new app"),
    ("Modifica di app esistente", "Modifying existing app"),
    ("Audit",),  # Same in both
    ("Bug rescue",),  # Same in both
    ("Miglioramento skill", "Skill improvement"),
    ("Manutenzione", "Maintenance"),
    ("Sicurezza del coordinatore", "Coordinator safety"),
    ("Validator",),  # Same in both
]


def err(messages: list[str], msg: str) -> None:
    messages.append(f"ERRORE: {msg}")


def warn(messages: list[str], msg: str) -> None:
    messages.append(f"WARN:   {msg}")


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    issues: list[str] = []
    if not text.startswith("---\n"):
        err(issues, "frontmatter mancante (deve aprire con ---)")
        return {}, issues
    end = text.find("\n---", 4)
    if end == -1:
        err(issues, "frontmatter non chiuso (--- finale mancante)")
        return {}, issues
    raw = text[4:end]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            err(issues, f"riga frontmatter non valida: {line!r}")
            continue
        k, v = line.split(":", 1)
        data[k.strip()] = v.strip()
    missing = REQUIRED_FRONTMATTER_KEYS - data.keys()
    if missing:
        err(issues, f"frontmatter manca le chiavi: {sorted(missing)}")

    name = data.get("name", "")
    if name:
        if len(name) > 64:
            err(issues, f"frontmatter name supera 64 caratteri: {len(name)}")
        if not re.fullmatch(r"[a-z0-9-]+", name):
            err(issues, f"frontmatter name non conforme (solo a-z, 0-9, hyphens): {name!r}")
        if "anthropic" in name or "claude" in name:
            err(issues, f"frontmatter name contiene una reserved word: {name!r}")

    description = data.get("description", "")
    if description and len(description) > DESCRIPTION_MAX_CHARS:
        err(issues, f"frontmatter description supera {DESCRIPTION_MAX_CHARS} caratteri: {len(description)}")

    return data, issues


def find_headings(text: str) -> list[tuple[int, str, str]]:
    headings = []
    in_fence = False
    fence_marker = ""
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            headings.append((i, m.group(1), m.group(2)))
    return headings


def extract_reference_paths(text: str) -> set[str]:
    pattern = re.compile(r"references/([A-Za-z0-9_\-]+\.md)")
    return set(pattern.findall(text))


def extract_asset_paths(text: str) -> set[str]:
    pattern = re.compile(r"assets/([A-Za-z0-9_\-/]+\.[A-Za-z0-9]+)")
    return set(pattern.findall(text))


def extract_asset_globs(text: str) -> set[str]:
    pattern = re.compile(r"assets/([A-Za-z0-9_\-/]*\*[A-Za-z0-9_\-/*]*\.[A-Za-z0-9]+)")
    return set(pattern.findall(text))


def check_assets(messages: list[str], skill_text: str) -> None:
    cited = extract_asset_paths(skill_text)
    cited_globs = extract_asset_globs(skill_text)
    cited -= cited_globs
    if not ASSETS_DIR.exists():
        if cited or cited_globs:
            err(messages, f"SKILL.md cita assets/ ma la cartella non esiste: {sorted(cited | cited_globs)}")
        return
    on_disk: set[str] = set()
    for p in ASSETS_DIR.rglob("*"):
        if p.is_file():
            on_disk.add(str(p.relative_to(ASSETS_DIR)).replace("\\", "/"))
    missing = sorted(cited - on_disk)
    if missing:
        err(messages, f"asset citati da SKILL.md ma assenti: {missing}")
    unmatched_globs = sorted(g for g in cited_globs if not any(Path(f).match(g) for f in on_disk))
    if unmatched_globs:
        err(messages, f"glob asset citati da SKILL.md senza alcun file corrispondente: {unmatched_globs}")
    if (cited or cited_globs) and not missing and not unmatched_globs:
        messages.append(f"OK:     {len(cited) + len(cited_globs)} asset (file+glob) citati risolti in assets/")


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def check_skill(messages: list[str]) -> tuple[str, set[str]]:
    if not SKILL_FILE.exists():
        err(messages, f"SKILL.md non trovato in {SKILL_FILE}")
        return "", set()
    text = SKILL_FILE.read_text(encoding="utf-8")
    lines = line_count(SKILL_FILE)
    if lines > SKILL_MAX_LINES:
        err(messages, f"SKILL.md ha {lines} righe (max {SKILL_MAX_LINES})")
    else:
        messages.append(f"OK:     SKILL.md {lines} righe (<= {SKILL_MAX_LINES})")

    _, fm_issues = parse_frontmatter(text)
    messages.extend(fm_issues)
    if not fm_issues:
        messages.append("OK:     frontmatter valido")

    headings = find_headings(text)
    titles = [h[2].lower() for h in headings]
    seen: dict[str, int] = {}
    for _, _, title in headings:
        key = title.lower()
        seen[key] = seen.get(key, 0) + 1
    duplicates = [t for t, c in seen.items() if c > 1]
    if duplicates:
        err(messages, f"heading duplicati in SKILL.md: {duplicates}")
    else:
        messages.append("OK:     nessun heading duplicato in SKILL.md")

    missing_sections = []
    for section_variants in REQUIRED_SECTIONS:
        # section_variants is a tuple of alternative names (e.g., ("Lingua", "Language"))
        found = False
        for variant in section_variants:
            if any(variant.lower() in t for t in titles):
                found = True
                break
        if not found:
            missing_sections.append(section_variants[0])  # Report first variant
    if missing_sections:
        err(messages, f"sezioni obbligatorie mancanti: {missing_sections}")
    else:
        messages.append("OK:     sezioni obbligatorie presenti")

    cited = extract_reference_paths(text)
    return text, cited


def check_references(messages: list[str], cited: set[str]) -> None:
    if not REFERENCES_DIR.exists():
        err(messages, f"cartella references/ non trovata in {REFERENCES_DIR}")
        return
    on_disk = {p.name for p in REFERENCES_DIR.glob("*.md")}

    missing_files = sorted(cited - on_disk)
    if missing_files:
        err(messages, f"reference citate da SKILL.md ma assenti: {missing_files}")

    orphan_files = sorted(on_disk - cited)
    if orphan_files:
        err(
            messages,
            f"reference presenti ma non citate da SKILL.md: {orphan_files}",
        )

    if not missing_files and not orphan_files:
        messages.append(
            f"OK:     {len(on_disk)} reference allineate con SKILL.md"
        )

    for ref in sorted(on_disk):
        path = REFERENCES_DIR / ref
        n = line_count(path)
        # release-notes.md cresce per natura (una voce per release): soglia piu' alta
        max_lines = 200 if ref == "release-notes.md" else REFERENCE_MAX_LINES
        if n > max_lines:
            err(messages, f"references/{ref} ha {n} righe (max {max_lines})")
        ref_text = path.read_text(encoding="utf-8")
        ref_headings = find_headings(ref_text)
        seen: dict[str, int] = {}
        for _, level, title in ref_headings:
            if len(level) > 2:
                continue
            key = title.lower()
            seen[key] = seen.get(key, 0) + 1
        dupes = [t for t, c in seen.items() if c > 1]
        if dupes:
            err(messages, f"heading duplicati in references/{ref}: {dupes}")


def collect_corpus_text() -> str:
    parts: list[str] = []
    if SKILL_FILE.exists():
        parts.append(SKILL_FILE.read_text(encoding="utf-8"))
    for p in REFERENCES_DIR.glob("*.md") if REFERENCES_DIR.exists() else []:
        parts.append(p.read_text(encoding="utf-8"))
    if RECIPES_DIR.exists():
        for p in RECIPES_DIR.glob("*.md"):
            parts.append(p.read_text(encoding="utf-8"))
    return "\n".join(parts)


def check_recipes(messages: list[str]) -> None:
    if not RECIPES_DIR.exists():
        return
    recipes = {p.name for p in RECIPES_DIR.glob("*.md") if p.name != "README.md"}
    if not recipes:
        return
    readme = RECIPES_DIR / "README.md"
    if not readme.exists():
        err(messages, "recipes/ esiste ma manca README.md indice")
        return
    text = readme.read_text(encoding="utf-8")
    cited = {m for m in re.findall(r"([a-z0-9\-]+\.md)", text) if m != "README.md"}
    missing = sorted(recipes - cited)
    if missing:
        err(messages, f"ricette presenti ma non citate da recipes/README.md: {missing}")
    else:
        messages.append(f"OK:     {len(recipes)} ricette allineate con recipes/README.md")


def check_scripts(messages: list[str], corpus: str) -> None:
    if not SCRIPTS_ASSETS_DIR.exists():
        return
    scripts = {p.name for p in SCRIPTS_ASSETS_DIR.iterdir() if p.is_file()}
    if not scripts:
        return
    orphan = sorted(s for s in scripts if s not in corpus)
    if orphan:
        err(messages, f"script in assets/scripts/ non citati da skill/reference/recipes: {orphan}")
    else:
        messages.append(f"OK:     {len(scripts)} script in assets/scripts/ citati nel corpus")


def check_templates(messages: list[str], corpus: str) -> None:
    if not TEMPLATES_DIR.exists():
        return
    templates = {p.name for p in TEMPLATES_DIR.glob("*.md")}
    if not templates:
        return
    orphan = sorted(t for t in templates if t not in corpus)
    if orphan:
        err(messages, f"template in assets/templates/ non citati da skill/reference/recipes: {orphan}")
    else:
        messages.append(f"OK:     {len(templates)} template in assets/templates/ citati nel corpus")


def check_progressive_loading(messages: list[str], skill_text: str) -> None:
    pl_match = re.search(
        r"Progressive loading[\s\S]+?(?=\n## )",
        skill_text,
        re.IGNORECASE,
    )
    if not pl_match:
        err(messages, "sezione 'Progressive loading' non trovata in SKILL.md")
        return
    pl_block = pl_match.group(0)
    pl_refs = extract_reference_paths(pl_block)
    on_disk = {p.name for p in REFERENCES_DIR.glob("*.md")} if REFERENCES_DIR.exists() else set()
    missing = sorted(on_disk - pl_refs)
    if missing:
        err(
            messages,
            f"progressive loading non cita: {missing}",
        )
    else:
        messages.append("OK:     progressive loading copre tutte le reference")


def main() -> int:
    messages: list[str] = []
    skill_text, cited = check_skill(messages)
    if skill_text:
        check_progressive_loading(messages, skill_text)
        check_assets(messages, skill_text)
    check_references(messages, cited)
    corpus = collect_corpus_text()
    check_recipes(messages)
    check_scripts(messages, corpus)
    check_templates(messages, corpus)

    errors = [m for m in messages if m.startswith("ERRORE:")]
    warns = [m for m in messages if m.startswith("WARN:")]
    oks = [m for m in messages if m.startswith("OK:")]

    for m in oks:
        print(m)
    for m in warns:
        print(m)
    for m in errors:
        print(m)

    print()
    print(f"Risultato: {len(oks)} ok, {len(warns)} warn, {len(errors)} errori")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
