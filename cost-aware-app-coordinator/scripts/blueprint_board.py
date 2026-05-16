#!/usr/bin/env python3
"""Blueprint Board Core: intent graph for app/software/game work."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


BLUEPRINT_FILE = "app-blueprint.json"
SCHEMA_VERSION = "1.0"
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".next", ".venv", "venv", "__pycache__", "coverage"}
TEXT_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".py", ".md", ".json", ".yml", ".yaml", ".html", ".css", ".scss"}
NODE_TYPES = {
    "auth": ["login", "auth", "oauth", "google", "password", "session"],
    "infra": ["cache", "ttl", "runtime", "config", "env", "ci", "docker", "log", "monitor"],
    "api": ["api", "endpoint", "route", "controller", "backend", "server"],
    "page": ["page", "pagina", "admin", "screen", "view", "ui", "layout", "component"],
    "data": ["database", "schema", "model", "table", "db", "dati"],
    "integration": ["email", "stripe", "webhook", "provider", "external"],
    "test": ["test", "qa", "spec", "playwright", "controlli"],
    "deploy": ["deploy", "docker", "ci", "release", "env"],
    "bug": ["bug", "fix", "errore", "crash"],
    "docs": ["docs", "documentazione", "readme", "handoff", "guida"],
}
DOMAIN_MARKERS = {
    "frontend": ["frontend", "ui", "pagina", "page", "screen", "view", "layout", "component", "dashboard"],
    "backend": ["backend", "api", "endpoint", "route", "controller", "service", "server"],
    "data": ["database", "schema", "model", "table", "db", "dati", "migrazione"],
    "devops": ["deploy", "docker", "ci", "env", "release", "runtime", "config", "cache", "ttl", "log", "monitor"],
    "qa": ["test", "qa", "spec", "playwright", "controlli"],
    "docs": ["docs", "documentazione", "readme", "handoff", "guida"],
}
TAG_MARKERS = {
    "auth": ["login", "auth", "oauth", "google", "password", "session"],
    "observability": ["dashboard", "log", "monitor", "metric", "consumi", "costi"],
    "performance": ["cache", "ttl", "veloce", "performance", "risorse", "token"],
    "automation": ["automatic", "auto", "workflow", "sync", "sincron"],
    "ux": ["semplice", "bella", "layout", "utente", "usabil"],
    "security": ["segreti", "password", "permessi", "security", "sicurezza"],
    "game": ["gioco", "game", "level", "player"],
}


def timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def blueprint_path(project: Path) -> Path:
    return project.resolve() / BLUEPRINT_FILE


def slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:48] or "node"


def words(text: str) -> list[str]:
    return [item for item in re.findall(r"[a-z0-9]+", text.lower()) if len(item) >= 3]


def human_title(path: Path) -> str:
    stem = path.stem
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", stem)
    spaced = re.sub(r"[-_]+", " ", spaced).strip()
    return " ".join(part.capitalize() for part in spaced.split()) or stem


def infer_type(text: str) -> str:
    lower = text.lower()
    scores = {name: sum(1 for marker in markers if marker in lower) for name, markers in NODE_TYPES.items()}
    if "dashboard" in lower and any(marker in lower for marker in ["cache", "ttl", "log", "monitor", "consumi", "costi"]):
        scores["infra"] += 2
    best, score = max(scores.items(), key=lambda item: item[1])
    return best if score else "feature"


def seed_titles(description: str) -> list[tuple[str, str]]:
    lower = description.lower()
    seeds = [("Project Overview", "Obiettivo, utenti, vincoli e successo del prodotto.")]
    if any(marker in lower for marker in ["login", "auth", "accesso", "google", "email", "password"]):
        seeds.append(("Login e gestione accessi", description))
    if any(marker in lower for marker in ["dashboard", "home", "bacheca", "pannello"]):
        seeds.append(("Dashboard principale", description))
    if any(marker in lower for marker in ["admin", "gestionale", "backoffice"]):
        seeds.append(("Area admin", description))
    if any(marker in lower for marker in ["report", "statistiche", "grafici", "analytics"]):
        seeds.append(("Report e analytics", description))
    if any(marker in lower for marker in ["magazzino", "inventario", "prodotti", "ordini", "clienti", "fatture"]):
        seeds.append(("Gestione dati principali", description))
    if any(marker in lower for marker in ["pagamento", "stripe", "email", "notifiche", "webhook"]):
        seeds.append(("Integrazioni esterne", description))
    if any(marker in lower for marker in ["gioco", "game", "livelli", "punteggio", "player"]):
        seeds.append(("Gameplay core", description))
    seeds.extend(
        [
            ("API e contratti backend", "Endpoint, validazione, errori e permessi."),
            ("Test e smoke check", "Fixture minima, test critici e verifica manuale rapida."),
            ("Deploy locale e configurazione", "Env, avvio locale, build e smoke post-avvio."),
        ]
    )
    compact: list[tuple[str, str]] = []
    seen = set()
    for title, text in seeds:
        key = title.lower()
        if key not in seen:
            seen.add(key)
            compact.append((title, text))
    return compact[:12]


def seed_blueprint(project: Path, description: str, write: bool) -> dict[str, object]:
    data = load_blueprint(project)
    data["project_description"] = description
    existing_titles = {str(item.get("title", "")).lower() for item in data.get("nodes", []) if isinstance(item, dict)}
    added = []
    for title, text in seed_titles(description):
        if title.lower() in existing_titles:
            continue
        node = make_node(title, text, source="seed", status="planned")
        if title == "Project Overview":
            node["priority"] = 1
        added.append(add_node(data, node))
    if write:
        save_blueprint(project, data)
    return {
        "path": str(blueprint_path(project)),
        "write": write,
        "description": description,
        "added": added,
        "blueprint": data,
        "superplan": superplan(data),
    }


def infer_confidence(text: str, inferred_type: str) -> str:
    if inferred_type == "feature":
        return "low" if len(text.split()) < 4 else "medium"
    return "high"


def infer_domain(text: str, inferred_type: str) -> str:
    lower = text.lower()
    scores = {name: sum(1 for marker in markers if marker in lower) for name, markers in DOMAIN_MARKERS.items()}
    if inferred_type in {"auth", "api"}:
        scores["backend"] = scores.get("backend", 0) + 1
    if inferred_type == "page":
        scores["frontend"] = scores.get("frontend", 0) + 1
    if inferred_type in {"infra", "deploy"}:
        scores["devops"] = scores.get("devops", 0) + 2
    if inferred_type == "test":
        scores["qa"] = scores.get("qa", 0) + 1
    if inferred_type == "docs":
        scores["docs"] = scores.get("docs", 0) + 1
    best, score = max(scores.items(), key=lambda item: item[1])
    return best if score else "product"


def infer_tags(text: str, inferred_type: str, domain: str) -> list[str]:
    lower = text.lower()
    tags = [tag for tag, markers in TAG_MARKERS.items() if any(marker in lower for marker in markers)]
    for value in [inferred_type, domain]:
        if value not in {"feature", "product"} and value not in tags:
            tags.append(value)
    return tags[:6]


def implementation_steps(title: str, inferred_type: str, domain: str) -> list[str]:
    presets = {
        "auth": ["Leggi flusso auth esistente e permessi", "Definisci contratto sessione/API", "Implementa UI/API minime", "Aggiungi test login/logout"],
        "page": ["Trova componenti e stile esistenti", "Definisci stati vuoto/caricamento/errore", "Implementa layout responsive", "Fai smoke test visivo"],
        "api": ["Definisci request/response", "Aggiorna route/controller/service", "Gestisci validazione ed errori", "Aggiungi test endpoint"],
        "data": ["Mappa schema e dati attuali", "Prepara migrazione o modello", "Aggiorna query/seed minimi", "Verifica rollback o test dati"],
        "infra": ["Individua runtime/config coinvolti", "Applica cambio minimo e misurabile", "Esponi stato o log utile", "Verifica con smoke test"],
        "integration": ["Controlla provider/env richiesti", "Isola client e gestione errori", "Proteggi callback/webhook", "Testa caso successo/fallimento"],
        "test": ["Scegli scenario ad alto segnale", "Crea fixture piccola", "Copri regressione principale", "Rendi output leggibile"],
        "deploy": ["Controlla env/build/CI", "Prepara smoke post-deploy", "Documenta rollback", "Verifica segreti richiesti"],
        "bug": ["Riproduci il problema", "Trova root cause minima", "Correggi senza refactor largo", "Aggiungi regression test"],
        "docs": ["Trova doc fonte esistente", "Aggiorna solo se riduce ambiguita", "Aggiungi routing pratico", "Verifica link e comandi"],
    }
    return [f"{title}: {step}" for step in presets.get(inferred_type, ["Rileggi contesto mirato", "Definisci slice minima", "Implementa riusando pattern esistenti", "Verifica con test/smoke"])]


def suggested_children(title: str, inferred_type: str) -> list[str]:
    presets = {
        "auth": ["UI accesso", "API sessione", "Provider credenziali/OAuth", "Logout", "Test auth"],
        "page": ["Layout", "Stati caricamento/errore", "Dati/API usati", "Responsive", "Test UI"],
        "api": ["Contratto request/response", "Validazione input", "Errori", "Permessi", "Test endpoint"],
        "data": ["Schema", "Migrazione", "Query principali", "Seed/demo data", "Rollback"],
        "integration": ["Config/env", "Client provider", "Webhook/callback", "Error handling", "Test integrazione"],
        "deploy": ["Env", "Build", "CI", "Smoke test", "Rollback"],
        "test": ["Unit", "Integration", "E2E", "Fixture", "Criteri pass/fail"],
        "bug": ["Riproduzione", "Root cause", "Fix minimo", "Regression test"],
    }
    return [f"{title}: {item}" for item in presets.get(inferred_type, ["UI", "Backend/API", "Dati", "Test"])]


def empty_blueprint(project: Path) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project_name": project.resolve().name,
        "project_path": str(project.resolve()),
        "created_at": timestamp(),
        "updated_at": timestamp(),
        "last_sync_at": None,
        "nodes": [],
    }


def load_blueprint(project: Path) -> dict[str, object]:
    path = blueprint_path(project)
    if not path.exists():
        return empty_blueprint(project)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else empty_blueprint(project)
    except (OSError, json.JSONDecodeError):
        return empty_blueprint(project)


def save_blueprint(project: Path, data: dict[str, object]) -> None:
    data["updated_at"] = timestamp()
    blueprint_path(project).write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def make_node(title: str, free_text: str = "", source: str = "manual", status: str = "planned") -> dict[str, object]:
    text = f"{title} {free_text}".strip()
    inferred = infer_type(text)
    domain = infer_domain(text, inferred)
    return {
        "id": slug(title),
        "title": title,
        "free_text": free_text or title,
        "inferred_type": inferred,
        "domain": domain,
        "status": status,
        "confidence": infer_confidence(text, inferred),
        "parent_id": None,
        "depends_on": [],
        "tags": infer_tags(text, inferred, domain),
        "priority": 2,
        "children_suggested": suggested_children(title, inferred),
        "implementation_steps": implementation_steps(title, inferred, domain),
        "files": [],
        "files_last_synced_at": None,
        "source": source,
        "created_at": timestamp(),
        "updated_at": timestamp(),
        "completed_at": None,
        "notes": "",
    }


def add_node(data: dict[str, object], new_node: dict[str, object]) -> dict[str, object]:
    nodes = data.setdefault("nodes", [])
    if not isinstance(nodes, list):
        data["nodes"] = nodes = []
    existing = {str(item.get("id", "")) for item in nodes if isinstance(item, dict)}
    base = str(new_node["id"])
    candidate = base
    index = 2
    while candidate in existing:
        candidate = f"{base}-{index}"
        index += 1
    new_node["id"] = candidate
    nodes.append(new_node)
    data["updated_at"] = timestamp()
    return new_node


def import_candidates(project: Path) -> list[dict[str, object]]:
    markers = [
        ("Frontend", "UI/web app rilevata", project / "frontend"),
        ("Backend", "Backend/API rilevato", project / "backend"),
        ("API routes", "Cartella route/API rilevata", project / "backend" / "src" / "routes"),
        ("Controllers", "Controller backend rilevati", project / "backend" / "src" / "controllers"),
        ("Services", "Servizi/logica applicativa rilevati", project / "backend" / "src" / "services"),
        ("React components", "Componenti UI rilevati", project / "frontend" / "src" / "components"),
        ("Pages", "Pagine/schermate rilevate", project / "frontend" / "src" / "pages"),
        ("Tests", "Test rilevati", project / "backend" / "src" / "services" / "__tests__"),
        ("Deploy", "Config deploy rilevata", project / "docker-compose.yml"),
        ("Documentation", "Documentazione progetto rilevata", project / "docs"),
    ]
    found = []
    for title, description, path in markers:
        if path.exists():
            node = make_node(title, description, source="imported", status="suggested")
            node["files"] = [path.relative_to(project).as_posix()]
            found.append(node)
    found.extend(feature_candidates(project))
    return found


def feature_candidates(project: Path, limit: int = 32) -> list[dict[str, object]]:
    patterns = [
        ("Page", "Schermata/pagina rilevata", "page", ["frontend/src/pages/*", "frontend/src/app/*", "src/pages/*", "app/*"]),
        ("Component", "Componente UI rilevato", "page", ["frontend/src/components/*", "src/components/*"]),
        ("API", "Endpoint/route rilevata", "api", ["backend/src/routes/*", "src/routes/*", "server/routes/*"]),
        ("Service", "Servizio/logica applicativa rilevata", "api", ["backend/src/services/*", "src/services/*", "server/services/*"]),
        ("Test", "Test specifico rilevato", "test", ["**/__tests__/*", "**/*.test.*", "**/*.spec.*"]),
    ]
    candidates: list[dict[str, object]] = []
    seen_files: set[str] = set()
    for prefix, description, expected_type, globs in patterns:
        for pattern in globs:
            for path in sorted(project.glob(pattern)):
                if len(candidates) >= limit:
                    return candidates
                if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
                    continue
                rel = path.relative_to(project).as_posix()
                if rel in seen_files or path.suffix.lower() not in TEXT_EXTENSIONS:
                    continue
                seen_files.add(rel)
                title = f"{prefix}: {human_title(path)}"
                node = make_node(title, description, source="imported-inferred", status="suggested")
                node["files"] = [rel]
                node["inferred_type"] = expected_type
                node["domain"] = infer_domain(f"{title} {description}", expected_type)
                node["tags"] = infer_tags(f"{title} {description}", str(node["inferred_type"]), str(node["domain"]))
                node["implementation_steps"] = implementation_steps(title, str(node["inferred_type"]), str(node["domain"]))
                candidates.append(node)
    return candidates


def import_project(project: Path, write: bool) -> dict[str, object]:
    data = load_blueprint(project)
    existing_titles = {str(item.get("title", "")).lower() for item in data.get("nodes", []) if isinstance(item, dict)}
    added = []
    for candidate in import_candidates(project):
        if str(candidate["title"]).lower() in existing_titles:
            continue
        added.append(add_node(data, candidate))
    if write and added:
        data["last_sync_at"] = timestamp()
        save_blueprint(project, data)
    return {"path": str(blueprint_path(project)), "write": write, "added": added, "blueprint": data}


def project_files(project: Path, limit: int = 1200) -> list[Path]:
    found: list[Path] = []
    for path in project.rglob("*"):
        if len(found) >= limit:
            break
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
            found.append(path)
    return found


def related_files(project: Path, node: dict[str, object], files: list[Path]) -> list[str]:
    explicit = []
    for value in node.get("files", []) if isinstance(node.get("files"), list) else []:
        path = project / str(value)
        if path.exists():
            explicit.append(str(Path(value).as_posix()))
    if explicit:
        return explicit[:8]
    terms = set(words(" ".join([str(node.get("id", "")), str(node.get("title", "")), str(node.get("free_text", ""))])))
    generic = {"con", "per", "del", "della", "app", "project", "feature", "dashboard"}
    terms = {term for term in terms if term not in generic}
    matches = []
    for path in files:
        rel = path.relative_to(project).as_posix().lower()
        score = sum(1 for term in terms if term in rel)
        if score:
            matches.append((score, rel))
    matches.sort(key=lambda item: (-item[0], item[1]))
    return [item[1] for item in matches[:8]]


def has_domain_surface(project: Path, domain: str) -> bool:
    surfaces = {
        "frontend": ["frontend", "src/components", "src/pages", "app", "pages"],
        "backend": ["backend", "src/routes", "src/controllers", "src/services", "server"],
        "data": ["prisma", "migrations", "models", "schema"],
        "devops": [".github", "docker-compose.yml", "Dockerfile", ".env.example"],
        "qa": ["tests", "__tests__", "playwright.config.ts", "vitest.config.ts"],
        "docs": ["docs", "README.md", "AGENTS.md", "AI_CONTEXT.md"],
    }
    return any((project / item).exists() for item in surfaces.get(domain, []))


def has_test_signal(project: Path, node: dict[str, object], files: list[Path]) -> bool:
    terms = set(words(" ".join([str(node.get("id", "")), str(node.get("title", ""))])))
    for path in files:
        rel = path.relative_to(project).as_posix().lower()
        if any(marker in rel for marker in ["test", "spec", "__tests__", "playwright"]):
            if not terms or any(term in rel for term in terms):
                return True
    return False


def node_description(node: dict[str, object], related: list[str], reason: str) -> str:
    free_text = str(node.get("free_text") or "").strip()
    if free_text and free_text != str(node.get("title", "")).strip():
        base = free_text
    else:
        domain = str(node.get("domain") or "progetto")
        node_type = str(node.get("inferred_type") or "feature")
        base = f"Nodo {node_type} in area {domain} rilevato dalla struttura del progetto."
    if related:
        base += f" File principale: {related[0]}."
    if reason:
        base += f" Stato: {reason}"
    return base


def node_doctor(project: Path, node: dict[str, object], files: list[Path]) -> dict[str, object]:
    domain = str(node.get("domain") or infer_domain(str(node.get("title", "")), str(node.get("inferred_type", "feature"))))
    related = related_files(project, node, files)
    surface = has_domain_surface(project, domain)
    test_signal = has_test_signal(project, node, files)
    if related and test_signal:
        health = "covered"
        reason = "File collegati e segnale test trovati."
    elif related:
        health = "partial"
        reason = "File collegati trovati, ma test non evidenti."
    elif surface:
        health = "idea"
        reason = "Area tecnica presente, ma nodo non collegato a file specifici."
    else:
        health = "missing"
        reason = "Non vedo ancora superficie tecnica chiara per questo nodo."
    next_action = {
        "covered": "Valuta se marcarlo done o lasciare solo manutenzione.",
        "partial": "Aggiungi o collega un test mirato prima di espandere il nodo.",
        "idea": "Trasformalo in una slice piccola con file target prima di implementare.",
        "missing": "Crea struttura minima o chiarisci dominio prima di scrivere codice.",
    }[health]
    return {
        "id": node.get("id", ""),
        "title": node.get("title", ""),
        "description": node_description(node, related, reason),
        "type": node.get("inferred_type", ""),
        "domain": domain,
        "status": node.get("status", ""),
        "health": health,
        "reason": reason,
        "test_signal": test_signal,
        "related_files": related,
        "next_action": next_action,
    }


def doctor(project: Path) -> dict[str, object]:
    data = load_blueprint(project)
    nodes = [item for item in data.get("nodes", []) if isinstance(item, dict)]
    if not nodes and not blueprint_path(project).exists():
        nodes = import_candidates(project)[:30]
    files = project_files(project)
    node_reports = [node_doctor(project, item, files) for item in nodes[:30]]
    counts: dict[str, int] = {}
    for item in node_reports:
        health = str(item.get("health", "unknown"))
        counts[health] = counts.get(health, 0) + 1
    risky = [item for item in node_reports if item.get("health") in {"missing", "idea", "partial"}]
    suggestions = [update_suggestion(item) for item in node_reports]
    return {
        "path": str(blueprint_path(project)),
        "exists": blueprint_path(project).exists(),
        "files_scanned": len(files),
        "nodes_checked": len(node_reports),
        "health_counts": [{"health": key, "nodes": value} for key, value in sorted(counts.items(), key=lambda item: (-item[1], item[0]))],
        "next_focus": risky[0] if risky else (node_reports[0] if node_reports else {}),
        "nodes": node_reports,
        "suggestions": suggestions,
        "note": "Doctor is read-only: it detects drift signals, it does not rewrite code or blueprint nodes.",
    }


def update_suggestion(report: dict[str, object]) -> dict[str, object]:
    health = str(report.get("health", ""))
    suggested_status = {
        "covered": "done-candidate",
        "partial": "needs-test",
        "idea": "needs-slice",
        "missing": "needs-structure",
    }.get(health, "review")
    confidence = "high" if health in {"covered", "partial"} and report.get("related_files") else "medium"
    if health == "missing":
        confidence = "low"
    return {
        "id": report.get("id", ""),
        "title": report.get("title", ""),
        "suggested_status": suggested_status,
        "confidence": confidence,
        "reason": report.get("reason", ""),
        "next_action": report.get("next_action", ""),
    }


def auto_update(project: Path, write: bool) -> dict[str, object]:
    data = load_blueprint(project)
    nodes = [item for item in data.get("nodes", []) if isinstance(item, dict)]
    report = doctor(project)
    by_id = {str(item.get("id", "")): item for item in report.get("nodes", []) if isinstance(item, dict)}
    suggestions = {str(item.get("id", "")): item for item in report.get("suggestions", []) if isinstance(item, dict)}
    applied = []
    if write and blueprint_path(project).exists():
        for node in nodes:
            node_id = str(node.get("id", ""))
            node_report = by_id.get(node_id)
            suggestion = suggestions.get(node_id)
            if not node_report or not suggestion:
                continue
            node["doctor_health"] = node_report.get("health", "")
            node["doctor_reason"] = node_report.get("reason", "")
            node["doctor_next_action"] = node_report.get("next_action", "")
            node["related_files_suggested"] = node_report.get("related_files", [])
            node["suggested_status"] = suggestion.get("suggested_status", "")
            node["doctor_last_checked_at"] = timestamp()
            applied.append({"id": node_id, "suggested_status": node.get("suggested_status", ""), "doctor_health": node.get("doctor_health", "")})
        save_blueprint(project, data)
    return {
        "path": str(blueprint_path(project)),
        "write": write,
        "applied": applied,
        "suggestions": list(suggestions.values()),
        "note": "Auto-update writes only Blueprint metadata when --write is used; it does not change app code.",
    }


def board_summary(project: Path) -> dict[str, object]:
    data = load_blueprint(project)
    nodes = [item for item in data.get("nodes", []) if isinstance(item, dict)]
    if not nodes and not blueprint_path(project).exists():
        nodes = import_candidates(project)[:30]
    planned = [item for item in nodes if item.get("status") in {"planned", "suggested"}]
    blocked = [item for item in nodes if item.get("status") == "blocked"]
    domains: dict[str, int] = {}
    tags: dict[str, int] = {}
    for item in nodes:
        domain = str(item.get("domain", "n/d"))
        domains[domain] = domains.get(domain, 0) + 1
        for tag in item.get("tags", []) if isinstance(item.get("tags"), list) else []:
            tags[str(tag)] = tags.get(str(tag), 0) + 1
    preview = []
    for item in nodes[:30]:
        tags_value = item.get("tags", [])
        preview.append(
            {
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "inferred_type": item.get("inferred_type", ""),
                "domain": item.get("domain", ""),
                "status": item.get("status", ""),
                "confidence": item.get("confidence", ""),
                "tags": ", ".join(str(tag) for tag in tags_value) if isinstance(tags_value, list) else str(tags_value),
                "source": item.get("source", ""),
            }
        )
    return {
        "path": str(blueprint_path(project)),
        "exists": blueprint_path(project).exists(),
        "nodes": len(nodes),
        "planned": len(planned),
        "blocked": len(blocked),
        "domains": [{"domain": key, "nodes": value} for key, value in sorted(domains.items(), key=lambda item: (-item[1], item[0]))],
        "tags": [{"tag": key, "nodes": value} for key, value in sorted(tags.items(), key=lambda item: (-item[1], item[0]))[:10]],
        "next_node": str(planned[0].get("title", "")) if planned else "",
        "preview_nodes": preview,
        "doctor": doctor(project),
        "superplan": superplan(data if data.get("nodes") else {**data, "nodes": nodes}),
    }


def superplan(data: dict[str, object]) -> str:
    nodes = [item for item in data.get("nodes", []) if isinstance(item, dict)]
    if not nodes:
        return "Nessun nodo Blueprint ancora. Aggiungi nodi liberi o importa il progetto."
    lines = [
        "Superplan Blueprint Board",
        "",
        "Obiettivo: trasformare i nodi in milestone operative senza duplicare codice esistente.",
        "",
        "Milestone consigliate:",
    ]
    for index, item in enumerate(nodes[:8], 1):
        lines.append(
            f"{index}. {item.get('title')} [{item.get('inferred_type')}/{item.get('domain', 'product')}] - {item.get('status')}"
        )
        steps = item.get("implementation_steps", [])
        if isinstance(steps, list):
            for step in steps[:2]:
                lines.append(f"   - {step}")
    lines.extend(
        [
            "",
            "Regole: usare il Blueprint come intent layer, verificare codice/docs prima di implementare, un nodo alla volta, test minimo prima del nodo successivo.",
        ]
    )
    return "\n".join(lines)


def validate_blueprint(data: dict[str, object]) -> list[str]:
    errors = []
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version non supportata")
    seen = set()
    for item in data.get("nodes", []):
        if not isinstance(item, dict):
            errors.append("node non valido")
            continue
        node_id = str(item.get("id", ""))
        if not node_id:
            errors.append("node senza id")
        if node_id in seen:
            errors.append(f"id duplicato: {node_id}")
        seen.add(node_id)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    for command in ["init", "summary", "plan", "validate", "import-project", "doctor", "auto-update"]:
        item = sub.add_parser(command)
        item.add_argument("project")
        item.add_argument("--json", action="store_true")
        if command in {"import-project", "auto-update"}:
            item.add_argument("--write", action="store_true")
    add = sub.add_parser("add-node")
    add.add_argument("project")
    add.add_argument("title")
    add.add_argument("--description", default="")
    add.add_argument("--json", action="store_true")
    seed = sub.add_parser("seed")
    seed.add_argument("project")
    seed.add_argument("description")
    seed.add_argument("--write", action="store_true")
    seed.add_argument("--json", action="store_true")
    args = parser.parse_args()
    project = Path(args.project).resolve()
    if args.cmd == "init":
        data = load_blueprint(project)
        if not blueprint_path(project).exists():
            save_blueprint(project, data)
        result = {"path": str(blueprint_path(project)), "blueprint": data}
    elif args.cmd == "add-node":
        data = load_blueprint(project)
        added = add_node(data, make_node(args.title, args.description))
        save_blueprint(project, data)
        result = {"path": str(blueprint_path(project)), "added": added, "blueprint": data}
    elif args.cmd == "seed":
        result = seed_blueprint(project, str(args.description), write=bool(args.write))
    elif args.cmd == "import-project":
        result = import_project(project, write=bool(args.write))
    elif args.cmd == "plan":
        result = {"path": str(blueprint_path(project)), "superplan": superplan(load_blueprint(project))}
    elif args.cmd == "doctor":
        result = doctor(project)
    elif args.cmd == "auto-update":
        result = auto_update(project, write=bool(args.write))
    elif args.cmd == "validate":
        data = load_blueprint(project)
        result = {"path": str(blueprint_path(project)), "errors": validate_blueprint(data)}
    else:
        result = board_summary(project)
    if getattr(args, "json", False):
        print(json.dumps(result, indent=2))
    else:
        print(result.get("superplan") or f"Blueprint: {result['path']}")
    return 1 if isinstance(result.get("errors"), list) and result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
