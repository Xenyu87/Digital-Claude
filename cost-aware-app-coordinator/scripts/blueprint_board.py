#!/usr/bin/env python3
"""Blueprint Board Core: intent graph for app/software/game work."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from event_log import read_events


BLUEPRINT_FILE = "app-blueprint.json"
SCHEMA_VERSION = "1.0"
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".next", ".venv", "venv", "__pycache__", "coverage", "reports"}
DESIGN_TEMPLATES = {
    "custom": {
        "goal": "",
        "users": "",
        "screens": "",
        "actions": "",
        "data": "",
        "auth": "",
        "tests": "",
    },
    "gestionale": {
        "goal": "Gestionale operativo con login, dashboard e gestione dati principali.",
        "users": "Admin\nOperatore",
        "screens": "Login\nDashboard\nClienti\nOrdini\nImpostazioni",
        "actions": "fare login\ncreare cliente\ncreare ordine\ncercare ordine\naggiornare stato ordine",
        "data": "Utente\nCliente\nOrdine\nRiga ordine",
        "auth": "Admin gestisce tutto; operatore vede e modifica solo le aree operative.",
        "tests": "login valido\ncreazione ordine\npermessi admin",
    },
    "ecommerce": {
        "goal": "Ecommerce con catalogo, carrello, checkout e gestione ordini.",
        "users": "Cliente\nAdmin",
        "screens": "Home\nCatalogo\nDettaglio prodotto\nCarrello\nCheckout\nArea admin",
        "actions": "cercare prodotto\naggiungere al carrello\nfare checkout\npagare ordine\ngestire prodotti",
        "data": "Utente\nProdotto\nCarrello\nOrdine\nPagamento",
        "auth": "Cliente compra e vede i propri ordini; admin gestisce catalogo e ordini.",
        "tests": "aggiunta al carrello\ncheckout riuscito\npermessi admin",
    },
    "dashboard": {
        "goal": "Dashboard/report per monitorare metriche, filtri e stato operativo.",
        "users": "Admin\nAnalista\nOperatore",
        "screens": "Dashboard\nReport\nDettaglio metrica\nFiltri\nEsportazione",
        "actions": "filtrare report\naprire dettaglio\nesportare dati\naggiornare dashboard",
        "data": "Metrica\nReport\nFiltro\nEvento",
        "auth": "Admin vede tutto; altri ruoli vedono solo report autorizzati.",
        "tests": "filtri corretti\nexport dati\ncaricamento dashboard",
    },
    "booking": {
        "goal": "App prenotazioni con disponibilita, calendario e gestione appuntamenti.",
        "users": "Cliente\nStaff\nAdmin",
        "screens": "Home\nCalendario\nPrenotazione\nLe mie prenotazioni\nAdmin",
        "actions": "vedere disponibilita\ncreare prenotazione\nannullare prenotazione\nconfermare appuntamento",
        "data": "Utente\nDisponibilita\nPrenotazione\nServizio",
        "auth": "Cliente gestisce le proprie prenotazioni; staff conferma appuntamenti.",
        "tests": "creazione prenotazione\nannullamento\nconflitto orario",
    },
    "community": {
        "goal": "Community con profili, post, commenti e moderazione.",
        "users": "Utente\nModeratore\nAdmin",
        "screens": "Feed\nProfilo\nPost\nNotifiche\nModerazione",
        "actions": "creare post\ncommentare\nseguire utente\nsegnalare contenuto\nmoderare post",
        "data": "Utente\nPost\nCommento\nSegnalazione\nNotifica",
        "auth": "Utente gestisce i propri contenuti; moderatore rimuove contenuti segnalati.",
        "tests": "creazione post\ncommento\npermessi moderatore",
    },
    "game": {
        "goal": "Gioco con menu, partita, progressi e punteggi.",
        "users": "Giocatore\nAdmin",
        "screens": "Menu\nPartita\nClassifica\nProfilo\nImpostazioni",
        "actions": "iniziare partita\nsalvare punteggio\nvedere classifica\naggiornare profilo",
        "data": "Giocatore\nPartita\nPunteggio\nLivello",
        "auth": "Giocatore vede i propri progressi; admin gestisce configurazioni.",
        "tests": "inizio partita\nsalvataggio punteggio\nclassifica",
    },
}
TEXT_EXTENSIONS = {
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte",
    ".py", ".go", ".rs", ".java", ".cs", ".php", ".rb",
    ".md", ".json", ".yml", ".yaml", ".html", ".css", ".scss", ".sql", ".sh", ".ps1",
}
ROUTE_RE = re.compile(r"""(?:fetch|axios\.(?:get|post|put|patch|delete)|href|to|action|router\.(?:get|post|put|patch|delete)|app\.(?:get|post|put|patch|delete))\s*(?:=|\()?\s*["']([^"']+)["']""")
CLIENT_FETCH_RE = re.compile(r"""fetch\(\s*["']([^"']+)["']\s*(?:,\s*\{(?P<options>[\s\S]{0,520}?)\})?""")
CLIENT_AXIOS_RE = re.compile(r"""axios\.(get|post|put|patch|delete)\(\s*["']([^"']+)["'](?P<args>[\s\S]{0,360}?)\)""", re.IGNORECASE)
NAVIGATION_RE = re.compile(r"""(?:href|to)\s*=\s*["']([^"']+)["']|router\.(?:push|replace)\(\s*["']([^"']+)["']""")
BACKEND_ROUTE_RE = re.compile(r"""(?:app|router)\.(get|post|put|patch|delete)\(\s*["']([^"']+)["']""", re.IGNORECASE)
PY_DECORATOR_ROUTE_RE = re.compile(r"""@(?:app|router)\.(get|post|put|patch|delete|route)\(\s*["']([^"']+)["'](?P<args>[\s\S]{0,240}?)\)""", re.IGNORECASE)
FORM_ACTION_RE = re.compile(r"""<form[^>]*action=["']([^"']+)["'][\s\S]{0,360}?<button[^>]*>([\s\S]{1,120}?)</button>""", re.IGNORECASE)
BUTTON_RE = re.compile(r"""<button[^>]*>([\s\S]{1,90}?)</button>""", re.IGNORECASE)
ENDPOINT_RE = re.compile(r"""["'](/[a-zA-Z0-9_./{}:-]+)["']""")
COMPONENT_RE = re.compile(r"""(?:export\s+default\s+function|export\s+function|function|const)\s+([A-Z][A-Za-z0-9_]*)""")
MODEL_RE = re.compile(r"""(?:model|interface|type|class)\s+([A-Z][A-Za-z0-9_]*)|CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?([A-Za-z_][A-Za-z0-9_]*)""", re.IGNORECASE)
HTTP_METHOD_RE = re.compile(r"""method\s*:\s*["']([A-Z]+)["']""", re.IGNORECASE)
JSON_BODY_KEYS_RE = re.compile(r"""JSON\.stringify\(\s*\{([^}]{1,360})\}""")
INTERNAL_UI_LABELS = {
    "monitora",
    "mostra linee",
    "nascondi linee",
    "reset vista",
    "salva layout",
    "zoom +",
    "zoom -",
    "usato",
    "sbagliato",
    "non capisco",
    "conferma",
    "ignora",
    "ignorato",
    "home",
    "lavagna",
    "azioni",
    "automazione",
    "diagnostica",
}
INTERNAL_ENDPOINTS = {
    "/api",
    "/android",
    "/backend",
    "/build",
    "/coverage",
    "/dist",
    "/expert-feedback",
    "/frontend",
    "/ios",
    "/reports",
    "/scripts",
    "/server",
    "/background-mode",
    "/background-scan",
    "/blueprint-design",
    "/blueprint-import",
    "/blueprint-layout",
    "/blueprint-scan",
    "/learning-feedback",
    "/runner-config",
    "/runner-enqueue",
    "/runner-pause",
    "/runner-run-once",
    "/runner-start",
    "/runner-stop",
    "/select-project",
    "/upload-screenshot",
}
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


def has_marker(lower_text: str, marker: str) -> bool:
    if len(marker) <= 2:
        return re.search(rf"\b{re.escape(marker)}\b", lower_text) is not None
    return marker in lower_text


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


def split_design_items(text: str) -> list[str]:
    normalized = text.replace(";", "\n").replace(",", "\n")
    items = []
    for raw in normalized.splitlines():
        value = raw.strip(" -\t")
        if value:
            items.append(value[:80])
    return items[:16]


def design_node(title: str, description: str, *, layer: str, kind: str, node_type: str = "feature", route: str = "") -> dict[str, object]:
    node = make_node(title, description, source="design", status="planned")
    node.update(
        {
            "origin": "design",
            "layer": layer,
            "kind": kind,
            "inferred_type": node_type,
            "domain": "frontend" if layer == "frontend" else ("backend" if layer == "backend" else layer),
            "confidence": "high",
        }
    )
    if route:
        if kind == "api":
            node["api_route"] = route
        else:
            node["ui_route"] = route
    return node


def route_from_action(action: str) -> str:
    value = slug(action).replace("-", "_")
    return f"/{value[:40] or 'action'}"


def apply_design_wizard(project: Path, payload: dict[str, str], write: bool = True) -> dict[str, object]:
    data = load_blueprint(project)
    template_name = str(payload.get("template") or "custom")
    template = DESIGN_TEMPLATES.get(template_name, DESIGN_TEMPLATES["custom"])
    merged_payload = {key: str(payload.get(key) or template.get(key) or "") for key in ["goal", "users", "screens", "actions", "data", "auth", "tests"]}
    data["design_template"] = template_name
    data["project_description"] = merged_payload.get("goal", "").strip() or data.get("project_description", "")
    existing_titles = {str(item.get("title", "")).lower() for item in data.get("nodes", []) if isinstance(item, dict)}
    added: list[dict[str, object]] = []

    def add_design(node: dict[str, object]) -> dict[str, object] | None:
        title = str(node.get("title", ""))
        if title.lower() in existing_titles:
            return None
        existing_titles.add(title.lower())
        added_node = add_node(data, node)
        added.append(added_node)
        return added_node

    goal = merged_payload.get("goal", "").strip()
    users = split_design_items(merged_payload.get("users", ""))
    screens = split_design_items(merged_payload.get("screens", ""))
    actions = split_design_items(merged_payload.get("actions", ""))
    data_items = split_design_items(merged_payload.get("data", ""))
    auth = merged_payload.get("auth", "").strip()
    tests = split_design_items(merged_payload.get("tests", ""))

    overview = add_design(design_node("Design: Obiettivo app", goal or "Obiettivo da chiarire.", layer="product", kind="feature"))
    for user in users:
        add_design(design_node(f"Utente: {user}", f"Persona o ruolo che usa l'app: {user}.", layer="product", kind="user"))
    for screen in screens:
        add_design(design_node(f"Schermata: {screen}", f"Schermata prevista nel design: {screen}.", layer="frontend", kind="screen", node_type="page"))
    action_nodes = []
    for action in actions:
        route = route_from_action(action)
        action_node = add_design(design_node(f"Azione: {action}", f"L'utente puo fare questa azione: {action}.", layer="frontend", kind="action", node_type="page", route=route))
        api_node = add_design(design_node(f"API: {route}", f"Endpoint previsto per supportare l'azione `{action}`.", layer="backend", kind="api", node_type="api", route=route))
        if action_node and api_node:
            action_node["depends_on"] = list(dict.fromkeys([*(action_node.get("depends_on", []) if isinstance(action_node.get("depends_on"), list) else []), api_node["id"]]))
            action_node["contract"] = {"route": route, "input": [], "output": [], "writes": []}
        if action_node:
            action_nodes.append(action_node)
    for item in data_items:
        add_design(design_node(f"Dato: {item}", f"Dato che l'app deve leggere o salvare: {item}.", layer="data", kind="model", node_type="data"))
    if auth:
        add_design(design_node("Regola: accesso e ruoli", auth, layer="backend", kind="rule", node_type="auth"))
    for test in tests:
        add_design(design_node(f"Test: {test}", f"Controllo atteso: {test}.", layer="qa", kind="test", node_type="test"))
    if overview and action_nodes:
        overview["depends_on"] = [node["id"] for node in action_nodes[:6]]

    if write:
        save_blueprint(project, data)
    return {"path": str(blueprint_path(project)), "write": write, "added": added, "blueprint": data}


def infer_confidence(text: str, inferred_type: str) -> str:
    if inferred_type == "feature":
        return "low" if len(text.split()) < 4 else "medium"
    return "high"


def infer_domain(text: str, inferred_type: str) -> str:
    lower = text.lower()
    scores = {name: sum(1 for marker in markers if has_marker(lower, marker)) for name, markers in DOMAIN_MARKERS.items()}
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
    found.extend(skill_candidates(project))
    found.extend(scanner_candidates(project))
    found.extend(feature_candidates(project))
    return found


def skill_candidates(project: Path) -> list[dict[str, object]]:
    if not (project / "SKILL.md").exists():
        return []
    definitions = [
        ("Skill Operating Rules", "Regole principali della skill: come decide, quando pianifica, quando chiede conferma e come lavora sui progetti.", ["SKILL.md"], "docs"),
        ("Progressive References", "Documenti richiamati solo quando servono: budget, routing, QA, handoff, sync e manutenzione.", ["references"], "docs"),
        ("Dashboard Runtime", "Genera e serve la dashboard, sceglie il progetto monitorato, gestisce cache e pannelli operativi.", ["scripts/generate_dashboard.py", "scripts/serve_dashboard.py"], "infra"),
        ("Blueprint Board", "Importa i nodi del progetto, li controlla, propone il prossimo passo e li mostra come lavagna.", ["scripts/blueprint_board.py", "scripts/blueprint_board_test.py"], "feature"),
        ("Verification Suite", "Raccoglie validazione, self-test, test fixture e comando unico per controllare la skill.", ["scripts/validate_skill.py", "scripts/self_test.py", "scripts/test_all.py"], "test"),
    ]
    candidates = []
    for title, description, files, expected_type in definitions:
        existing = [path for path in files if (project / path).exists()]
        if not existing:
            continue
        node = make_node(title, description, source="imported-skill", status="suggested")
        node["files"] = existing
        node["inferred_type"] = expected_type
        node["domain"] = infer_domain(f"{title} {description}", expected_type)
        node["tags"] = infer_tags(f"{title} {description}", str(node["inferred_type"]), str(node["domain"]))
        node["children_suggested"] = suggested_children(title, str(node["inferred_type"]))
        node["implementation_steps"] = implementation_steps(title, str(node["inferred_type"]), str(node["domain"]))
        candidates.append(node)
    return candidates


def clean_label(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\{[^}]+\}", " ", text)
    text = " ".join(text.split())
    if any(marker in text for marker in ["\\", "[", "]", "(", ")", "?", "*", "+"]):
        return ""
    return text[:64].strip()


def is_internal_ui_control(label: str, route: str = "") -> bool:
    normalized = " ".join(label.lower().split())
    if normalized in INTERNAL_UI_LABELS:
        return True
    if route in INTERNAL_ENDPOINTS:
        return True
    if normalized.startswith(("zoom", "reset ", "mostra ", "nascondi ", "monitora", "accoda ", "salva contratto", "scansiona ", "conferma e salva", "crea design", "trasforma ")):
        return True
    if normalized in {"manuale", "automatico sicuro", "proposte assistite", "avvia runner", "ferma", "pausa", "esegui un ciclo"}:
        return True
    return False


def is_known_noise_node(item: dict[str, object]) -> bool:
    title = str(item.get("title") or "")
    label = title.replace("Button:", "").replace("Action:", "").strip()
    route = str(item.get("ui_route") or item.get("api_route") or "")
    return is_internal_ui_control(label, route)


def clean_route(value: str) -> str:
    route = value.strip().split("?")[0].rstrip("/") or "/"
    if not route.startswith("/"):
        return ""
    if Path(route).suffix.lower() in {".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".ico", ".map"}:
        return ""
    return route[:120]


def infer_http_method(options: str, default: str = "GET") -> str:
    match = HTTP_METHOD_RE.search(options or "")
    return (match.group(1) if match else default).upper()


def body_keys(options: str) -> list[str]:
    match = JSON_BODY_KEYS_RE.search(options or "")
    if not match:
        return []
    keys = []
    for raw in match.group(1).split(","):
        key = raw.split(":", 1)[0].strip(" \n\t'\"")
        if key and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            keys.append(key)
    return keys[:12]


def route_name(route: str) -> str:
    clean = route.strip("/") or "home"
    return " ".join(part for part in re.split(r"[/_-]+", clean) if part).title() or route


def node_contract(route: str, method: str = "", *, input_keys: list[str] | None = None, writes: list[str] | None = None) -> dict[str, object]:
    return {
        "route": route,
        "method": method.upper() if method else "",
        "input": input_keys or [],
        "output": [],
        "writes": writes or [],
    }


def scanner_files(project: Path, limit: int = 240) -> list[Path]:
    found = []
    for path in project.rglob("*"):
        if len(found) >= limit:
            break
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if "test" in path.name.lower() or path.name.lower().endswith(".spec.js"):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
            found.append(path)
    return sorted(found, key=scanner_file_priority)


def scanner_file_priority(path: Path) -> tuple[int, str]:
    rel = path.as_posix()
    if rel.endswith("scripts/serve_dashboard.py"):
        return (0, rel)
    if "/backend/" in rel or "/server/" in rel or "/api/" in rel:
        return (1, rel)
    if "/scripts/" in rel and path.suffix.lower() == ".py":
        return (2, rel)
    if "/frontend/" in rel or path.suffix.lower() in {".jsx", ".tsx", ".html"}:
        return (3, rel)
    if "/reports/" in rel:
        return (8, rel)
    return (5, rel)


def scanner_candidates(project: Path, limit: int = 44) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for path in scanner_files(project):
        if len(candidates) >= limit:
            break
        rel = path.relative_to(project).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:140000]
        except OSError:
            continue

        for route, label in FORM_ACTION_RE.findall(text):
            if len(candidates) >= limit:
                break
            label = clean_label(label)
            route = clean_route(route)
            if is_internal_ui_control(label, route):
                continue
            key = ("action", f"{label}:{route}")
            if key in seen or not route:
                continue
            seen.add(key)
            node = make_node(f"Action: {label}", f"Quando l'utente clicca `{label}`, la UI invia o apre `{route}`.", source="scanner-ui-action", status="suggested")
            node.update({"files": [rel], "inferred_type": "page", "domain": "frontend", "layer": "frontend", "kind": "action", "ui_route": route, "http_method": "POST", "contract": node_contract(route, "POST"), "scanner_evidence": f"{rel}: form action {route}"})
            candidates.append(node)

        for match in CLIENT_FETCH_RE.finditer(text):
            if len(candidates) >= limit:
                break
            route = clean_route(match.group(1))
            if not route or route in INTERNAL_ENDPOINTS:
                continue
            call_text = text[match.start(): match.start() + 700]
            options = match.group("options") or call_text
            method = infer_http_method(options, "GET")
            keys = body_keys(call_text)
            key = ("fetch", f"{method}:{route}:{rel}")
            if key in seen:
                continue
            seen.add(key)
            title = f"Action: {method} {route}"
            description = f"La UI chiama `{route}` con metodo {method}."
            if keys:
                description += f" Campi inviati: {', '.join(keys)}."
            node = make_node(title, description, source="scanner-ui-fetch", status="suggested")
            node.update({"files": [rel], "inferred_type": "page", "domain": "frontend", "layer": "frontend", "kind": "action", "ui_route": route, "http_method": method, "contract": node_contract(route, method, input_keys=keys), "scanner_evidence": f"{rel}: fetch {method} {route}"})
            candidates.append(node)

        for method, route_value, args in CLIENT_AXIOS_RE.findall(text):
            if len(candidates) >= limit:
                break
            route = clean_route(route_value)
            if not route or route in INTERNAL_ENDPOINTS:
                continue
            method = method.upper()
            keys = body_keys(args)
            key = ("axios", f"{method}:{route}:{rel}")
            if key in seen:
                continue
            seen.add(key)
            node = make_node(f"Action: {method} {route}", f"La UI chiama `{route}` con axios usando metodo {method}.", source="scanner-ui-axios", status="suggested")
            node.update({"files": [rel], "inferred_type": "page", "domain": "frontend", "layer": "frontend", "kind": "action", "ui_route": route, "http_method": method, "contract": node_contract(route, method, input_keys=keys), "scanner_evidence": f"{rel}: axios {method} {route}"})
            candidates.append(node)

        for href, router_target in NAVIGATION_RE.findall(text):
            if len(candidates) >= limit:
                break
            route = clean_route(href or router_target)
            if not route:
                continue
            key = ("navigation", f"{route}:{rel}")
            if key in seen:
                continue
            seen.add(key)
            node = make_node(f"Navigation: {route_name(route)}", f"La UI naviga verso `{route}`.", source="scanner-ui-navigation", status="suggested")
            node.update({"files": [rel], "inferred_type": "page", "domain": "frontend", "layer": "frontend", "kind": "navigation", "ui_route": route, "http_method": "GET", "scanner_evidence": f"{rel}: navigazione {route}"})
            candidates.append(node)

        for route in sorted({match.group(1).strip() for match in ROUTE_RE.finditer(text) if match.group(1).strip().startswith("/")}):
            if len(candidates) >= limit:
                break
            route = clean_route(route)
            if not route or route in INTERNAL_ENDPOINTS:
                continue
            key = ("route-action", f"{route}:{rel}")
            if key in seen:
                continue
            if any(marker in text for marker in ["fetch(", "axios."]):
                continue
            if not any(marker in text for marker in ["action=", "action=\"", "action='", "href=", "to="]):
                continue
            seen.add(key)
            node = make_node(f"Action: chiama {route}", f"Azione UI o chiamata client rilevata verso `{route}`.", source="scanner-ui-route", status="suggested")
            node.update({"files": [rel], "inferred_type": "page", "domain": "frontend", "layer": "frontend", "kind": "action", "ui_route": route, "scanner_evidence": f"{rel}: route {route}"})
            candidates.append(node)

        for component in sorted(set(COMPONENT_RE.findall(text))):
            if len(candidates) >= limit:
                break
            if not component or len(component) <= 2 or component in {"React", "Promise"} or component.isupper():
                continue
            key = ("component", f"{component}:{rel}")
            if key in seen:
                continue
            seen.add(key)
            node = make_node(f"Screen/Component: {component}", f"Componente UI rilevato nel file `{rel}`.", source="scanner-ui-component", status="suggested")
            node.update({"files": [rel], "inferred_type": "page", "domain": "frontend", "layer": "frontend", "kind": "screen" if any(marker in rel.lower() for marker in ["page", "pages", "app/"]) else "component", "scanner_evidence": f"{rel}: componente {component}"})
            candidates.append(node)

        for label in BUTTON_RE.findall(text):
            if len(candidates) >= limit:
                break
            label = clean_label(label)
            if not label or len(label) < 3 or label.lower() in {"submit", "button"}:
                continue
            if is_internal_ui_control(label):
                continue
            key = ("button", f"{label}:{rel}")
            if key in seen:
                continue
            seen.add(key)
            node = make_node(f"Button: {label}", f"Bottone o comando visibile nella UI: `{label}`.", source="scanner-ui-button", status="suggested")
            node.update({"files": [rel], "inferred_type": "page", "domain": "frontend", "layer": "frontend", "kind": "action", "scanner_evidence": f"{rel}: bottone {label}"})
            candidates.append(node)

        for method, route_value in BACKEND_ROUTE_RE.findall(text):
            if len(candidates) >= limit:
                break
            route = clean_route(route_value)
            if not route:
                continue
            key = ("endpoint-method", f"{method.upper()}:{route}")
            if key in seen:
                continue
            seen.add(key)
            node = make_node(f"API: {method.upper()} {route}", f"Endpoint backend rilevato: `{method.upper()} {route}`.", source="scanner-backend-endpoint", status="suggested")
            node.update({"files": [rel], "inferred_type": "api", "domain": "backend", "layer": "backend", "kind": "api", "api_route": route, "http_method": method.upper(), "contract": node_contract(route, method), "scanner_evidence": f"{rel}: endpoint {method.upper()} {route}"})
            candidates.append(node)

        for match in PY_DECORATOR_ROUTE_RE.finditer(text):
            if len(candidates) >= limit:
                break
            method = match.group(1).upper()
            route = clean_route(match.group(2))
            if not route:
                continue
            args = match.group("args") or ""
            if method == "ROUTE":
                method_match = re.search(r"""methods\s*=\s*\[?\s*["']([A-Z]+)["']""", args, re.IGNORECASE)
                method = method_match.group(1).upper() if method_match else "GET"
            key = ("py-endpoint", f"{method}:{route}")
            if key in seen:
                continue
            seen.add(key)
            node = make_node(f"API: {method} {route}", f"Endpoint backend Python rilevato: `{method} {route}`.", source="scanner-backend-endpoint", status="suggested")
            node.update({"files": [rel], "inferred_type": "api", "domain": "backend", "layer": "backend", "kind": "api", "api_route": route, "http_method": method, "contract": node_contract(route, method), "scanner_evidence": f"{rel}: endpoint {method} {route}"})
            candidates.append(node)

        if any(marker in text for marker in ["parsed.path", "do_GET", "do_POST", "router.", "app."]):
            for route in sorted(set(ENDPOINT_RE.findall(text))):
                if len(candidates) >= limit:
                    break
                route = clean_route(route)
                if route in {"", "/", "/reports/skill-dashboard.html"} or route in INTERNAL_ENDPOINTS:
                    continue
                key = ("endpoint", route)
                if key in seen:
                    continue
                seen.add(key)
                node = make_node(f"API: {route}", f"Endpoint backend rilevato: `{route}`.", source="scanner-backend-endpoint", status="suggested")
                method = "POST" if "do_POST" in text and "do_GET" not in text else ""
                node.update({"files": [rel], "inferred_type": "api", "domain": "backend", "layer": "backend", "kind": "api", "api_route": route, "http_method": method, "contract": node_contract(route, method), "scanner_evidence": f"{rel}: endpoint {route}"})
                candidates.append(node)

        for model_match in MODEL_RE.findall(text):
            if len(candidates) >= limit:
                break
            model = next((item for item in model_match if item), "")
            if not model or model.lower() in {"props", "state", "selection", "choice", "label", "labels", "name", "names", "override", "unless", "was", "fallback", "config", "context", "policy", "and", "for", "from", "with", "in", "node", "only", "or", "html"}:
                continue
            if model.endswith(("Handler", "Controller", "View", "Component")):
                continue
            key = ("model", f"{model}:{rel}")
            if key in seen:
                continue
            seen.add(key)
            node = make_node(f"Data Model: {model}", f"Modello o tabella dati rilevata nel file `{rel}`.", source="scanner-data-model", status="suggested")
            node.update({"files": [rel], "inferred_type": "data", "domain": "data", "layer": "data", "kind": "model", "data_model": model, "scanner_evidence": f"{rel}: modello {model}"})
            candidates.append(node)
    return candidates


def feature_candidates(project: Path, limit: int = 90) -> list[dict[str, object]]:
    patterns = [
        ("Page", "Schermata/pagina rilevata", "page", ["frontend/src/pages/**/*", "frontend/src/app/**/*", "src/pages/**/*", "app/**/*", "pages/**/*"]),
        ("Component", "Componente UI rilevato", "page", ["frontend/src/components/**/*", "src/components/**/*", "components/**/*"]),
        ("API", "Endpoint/route rilevata", "api", ["backend/src/routes/**/*", "src/routes/**/*", "server/routes/**/*", "api/**/*", "app/api/**/*"]),
        ("Controller", "Controller backend rilevato", "api", ["backend/src/controllers/**/*", "src/controllers/**/*", "server/controllers/**/*"]),
        ("Service", "Servizio/logica applicativa rilevata", "api", ["backend/src/services/**/*", "src/services/**/*", "server/services/**/*", "services/**/*"]),
        ("Model", "Modello/schema dati rilevato", "data", ["backend/src/models/**/*", "src/models/**/*", "models/**/*", "prisma/schema.*", "migrations/**/*"]),
        ("Hook", "Hook o logica UI riusabile rilevata", "page", ["frontend/src/hooks/**/*", "src/hooks/**/*", "hooks/**/*"]),
        ("Utility", "Utility o helper rilevato", "feature", ["frontend/src/lib/**/*", "src/lib/**/*", "lib/**/*", "utils/**/*"]),
        ("Script", "Script operativo rilevato", "infra", ["scripts/**/*"]),
        ("Config", "Configurazione runtime/build rilevata", "infra", ["*.config.*", "docker-compose.*", "Dockerfile", ".github/workflows/*"]),
        ("Doc", "Documento operativo rilevato", "docs", ["docs/**/*.md", "references/**/*.md", "*.md"]),
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


def nodes_with_import_preview(project: Path, data: dict[str, object], limit: int = 90) -> list[dict[str, object]]:
    nodes = [item for item in data.get("nodes", []) if isinstance(item, dict)]
    layout = data.get("layout", {})
    positions = layout.get("positions", {}) if isinstance(layout, dict) else {}

    def attach_position(node: dict[str, object]) -> dict[str, object]:
        node_id = str(node.get("id", ""))
        position = positions.get(node_id) if isinstance(positions, dict) else None
        if isinstance(position, dict):
            node = dict(node)
            node["layout_x"] = position.get("x")
            node["layout_y"] = position.get("y")
        return node

    nodes = [attach_position(item) for item in nodes]
    existing_titles = {str(item.get("title", "")).lower() for item in nodes}
    existing_ids = {str(item.get("id", "")) for item in nodes}
    merged = list(nodes)
    for candidate in import_candidates(project):
        if len(merged) >= limit:
            break
        title = str(candidate.get("title", "")).lower()
        candidate_id = str(candidate.get("id", ""))
        if title in existing_titles or candidate_id in existing_ids:
            continue
        preview = dict(candidate)
        preview["preview_only"] = True
        preview = attach_position(preview)
        merged.append(preview)
        existing_titles.add(title)
        existing_ids.add(candidate_id)
    return merged[:limit]


def project_files(project: Path, limit: int = 2000) -> list[Path]:
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


def type_action(inferred_type: str) -> str:
    actions = {
        "auth": "gestisce accesso, sessioni e permessi",
        "infra": "fa funzionare l'app in modo stabile, veloce o osservabile",
        "api": "riceve richieste e restituisce dati o azioni al resto dell'app",
        "page": "mostra una schermata o un pezzo di interfaccia all'utente",
        "data": "conserva, organizza o legge i dati usati dall'app",
        "integration": "collega l'app a un servizio esterno",
        "test": "controlla che una parte continui a funzionare",
        "deploy": "prepara o pubblica l'app nell'ambiente dove gira",
        "bug": "rappresenta un problema da riprodurre e correggere",
        "docs": "spiega regole, decisioni o comandi utili a chi lavora sul progetto",
    }
    return actions.get(inferred_type, "rappresenta una funzionalita o una parte del prodotto")


def domain_place(domain: str) -> str:
    places = {
        "frontend": "nella parte visibile all'utente",
        "backend": "nel lato server",
        "data": "nei dati",
        "devops": "nel runtime o negli strumenti di avvio",
        "qa": "nei controlli e test",
        "docs": "nella documentazione",
        "product": "nel disegno generale del prodotto",
    }
    return places.get(domain, "nel progetto")


def node_layer(domain: str, node_type: str) -> str:
    if domain == "frontend" or node_type == "page":
        return "frontend"
    if domain == "backend" or node_type in {"api", "auth", "integration"}:
        return "backend"
    if domain == "data" or node_type == "data":
        return "data"
    if domain in {"qa", "devops", "docs"}:
        return domain
    return "product"


def node_kind(title: str, node_type: str, related: list[str]) -> str:
    lower = f"{title} {' '.join(related)}".lower()
    if node_type == "page":
        if any(marker in lower for marker in ["button", "btn", "form", "action"]):
            return "action"
        return "screen" if any(marker in lower for marker in ["page", "screen", "view", "app/"]) else "component"
    if node_type in {"api", "auth", "integration"}:
        return "api" if any(marker in lower for marker in ["route", "api", "endpoint"]) else "service"
    if node_type == "data":
        return "model"
    if node_type == "test":
        return "test"
    if node_type in {"infra", "deploy"}:
        return "runtime"
    if node_type == "docs":
        return "doc"
    return "feature"


def node_origin(node: dict[str, object]) -> str:
    explicit = str(node.get("origin") or "").strip()
    if explicit:
        return explicit
    source = str(node.get("source") or "")
    if source in {"manual", "seed", "user", "design"}:
        return "design"
    if source.startswith("scanner"):
        return "scanner"
    if source.startswith("imported"):
        return "code"
    return "scanner" if node.get("preview_only") else "design"


def normalized_terms_for_match(report: dict[str, object]) -> set[str]:
    generic = {"action", "button", "component", "page", "screen", "api", "service", "model", "test", "config", "doc", "script", "chiama", "frontend", "backend"}
    return {term for term in words(f"{report.get('id', '')} {report.get('title', '')} {report.get('description', '')}") if term not in generic}


def same_contract_surface(source: dict[str, object], target: dict[str, object]) -> bool:
    for key in ["ui_route", "api_route"]:
        source_value = str(source.get(key) or "").strip()
        target_value = str(target.get(key) or "").strip()
        if source_value and target_value and source_value == target_value:
            return True
    return False


def file_text(project: Path, rel_path: str, cache: dict[str, str]) -> str:
    if rel_path in cache:
        return cache[rel_path]
    path = project / rel_path
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:120000] if path.is_file() else ""
    except OSError:
        text = ""
    cache[rel_path] = text
    return text


def route_signals(project: Path, report: dict[str, object], cache: dict[str, str]) -> set[str]:
    signals: set[str] = set()
    for key in ["ui_route", "api_route"]:
        value = str(report.get(key) or "").strip()
        if value.startswith("/"):
            signals.add(value.split("?")[0].rstrip("/") or "/")
    if str(report.get("kind") or "") in {"action", "api"}:
        return signals
    for rel in report.get("related_files", []) if isinstance(report.get("related_files"), list) else []:
        text = file_text(project, str(rel), cache)
        for match in ROUTE_RE.finditer(text):
            value = match.group(1).strip()
            if value.startswith(("/", "http")):
                signals.add(value.split("?")[0].rstrip("/") or "/")
    return signals


def route_method_signals(project: Path, report: dict[str, object], cache: dict[str, str]) -> set[tuple[str, str]]:
    signals: set[tuple[str, str]] = set()
    explicit_method = str(report.get("http_method") or "").upper()
    for key in ["ui_route", "api_route"]:
        value = str(report.get(key) or "").strip()
        if value.startswith("/"):
            signals.add((value.split("?")[0].rstrip("/") or "/", explicit_method))
    if str(report.get("kind") or "") in {"action", "api", "navigation"}:
        return signals
    for rel in report.get("related_files", []) if isinstance(report.get("related_files"), list) else []:
        text = file_text(project, str(rel), cache)
        for match in CLIENT_FETCH_RE.finditer(text):
            route = clean_route(match.group(1))
            if route:
                signals.add((route, infer_http_method(match.group("options") or "", "GET")))
        for method, route, _args in CLIENT_AXIOS_RE.findall(text):
            route = clean_route(route)
            if route:
                signals.add((route, method.upper()))
        for method, route in BACKEND_ROUTE_RE.findall(text):
            route = clean_route(route)
            if route:
                signals.add((route, method.upper()))
    return signals


def methods_compatible(source_method: str, target_method: str) -> bool:
    source = source_method.upper()
    target = target_method.upper()
    return not source or not target or source == target


def route_method_overlap(source: set[tuple[str, str]], target: set[tuple[str, str]]) -> tuple[str, str, str] | None:
    for source_route, source_method in sorted(source):
        for target_route, target_method in sorted(target):
            if source_route == target_route and methods_compatible(source_method, target_method):
                return source_route, source_method, target_method
    return None


def title_terms(report: dict[str, object]) -> set[str]:
    generic = {"script", "component", "page", "api", "service", "model", "test", "config", "doc"}
    return {term for term in words(f"{report.get('id', '')} {report.get('title', '')}") if term not in generic}


def append_relation(
    source: dict[str, object],
    target: dict[str, object],
    relation: str,
    reason: str,
    *,
    confidence: str = "high",
    kind: str = "calls",
    evidence: str = "",
    state: str | None = None,
    contract: dict[str, object] | None = None,
) -> bool:
    relations = source.setdefault("plain_relations", [])
    if not isinstance(relations, list):
        source["plain_relations"] = relations = []
    target_id = str(target.get("id", ""))
    if not target_id or any(isinstance(rel, dict) and rel.get("id") == target_id and rel.get("kind") == kind for rel in relations):
        return False
    relations.append(
        {
            "id": target_id,
            "title": target.get("title", ""),
            "relation": relation,
            "reason": reason,
            "confidence": confidence,
            "kind": kind,
            "evidence": evidence,
            "state": state or ("confirmed" if confidence == "high" else "proposed"),
            "contract": contract or {},
        }
    )
    return True


def edge_key(source_id: str, target_id: str, kind: str) -> str:
    return f"{source_id}->{target_id}:{kind}"


def edge_feedback(project: Path) -> dict[str, str]:
    overrides: dict[str, str] = {}
    project_resolved = str(project.resolve())
    for event in read_events(1000):
        data = event.get("data", {}) if isinstance(event.get("data"), dict) else {}
        if str(event.get("event") or "") != "learning_feedback":
            continue
        try:
            if str(Path(str(event.get("project", ""))).resolve()) != project_resolved:
                continue
        except OSError:
            continue
        outcome = str(data.get("outcome") or "")
        item_id = str(data.get("item_id") or "")
        if outcome in {"confirm_edge", "ignore_edge"} and "->" in item_id:
            overrides[item_id] = outcome
    return overrides


def apply_edge_feedback(project: Path, reports: list[dict[str, object]]) -> None:
    overrides = edge_feedback(project)
    if not overrides:
        return
    for source in reports:
        source_id = str(source.get("id") or "")
        for rel in source.get("plain_relations", []) if isinstance(source.get("plain_relations"), list) else []:
            if not isinstance(rel, dict):
                continue
            key = edge_key(source_id, str(rel.get("id") or ""), str(rel.get("kind") or "calls"))
            outcome = overrides.get(key)
            if outcome == "confirm_edge":
                rel["user_feedback"] = "confirmed"
                rel["confidence"] = "high"
                rel["state"] = "confirmed"
                rel["reason"] = f"{rel.get('reason', '')} Confermato manualmente nella dashboard.".strip()
            elif outcome == "ignore_edge":
                rel["user_feedback"] = "ignored"
                rel["state"] = "ignored"
                rel["reason"] = f"{rel.get('reason', '')} Ignorato manualmente nella dashboard.".strip()


def attach_scanner_relationships(project: Path, reports: list[dict[str, object]]) -> None:
    cache: dict[str, str] = {}
    routes = {str(item.get("id", "")): route_signals(project, item, cache) for item in reports}
    route_methods = {str(item.get("id", "")): route_method_signals(project, item, cache) for item in reports}
    added_per_node: dict[str, int] = {}

    def can_add(source: dict[str, object]) -> bool:
        source_id = str(source.get("id", ""))
        added_per_node[source_id] = added_per_node.get(source_id, 0)
        return added_per_node[source_id] < 6

    def add(source: dict[str, object], target: dict[str, object], relation: str, reason: str, *, kind: str, evidence: str, confidence: str = "high", contract: dict[str, object] | None = None) -> None:
        if not can_add(source):
            return
        if append_relation(source, target, relation, reason, confidence=confidence, kind=kind, evidence=evidence, contract=contract):
            added_per_node[str(source.get("id", ""))] += 1

    for source in reports:
        source_layer = str(source.get("layer") or "")
        source_routes = routes.get(str(source.get("id", "")), set())
        source_route_methods = route_methods.get(str(source.get("id", "")), set())
        source_terms = title_terms(source)
        source_files = {str(item) for item in source.get("related_files", []) if isinstance(source.get("related_files"), list)}
        for target in reports:
            if source is target:
                continue
            target_layer = str(target.get("layer") or "")
            target_routes = routes.get(str(target.get("id", "")), set())
            target_route_methods = route_methods.get(str(target.get("id", "")), set())
            target_terms = title_terms(target)
            target_files = {str(item) for item in target.get("related_files", []) if isinstance(target.get("related_files"), list)}

            shared_routes = source_routes & target_routes
            matched_route = route_method_overlap(source_route_methods, target_route_methods)
            if source_layer == "frontend" and target_layer == "backend" and (matched_route or shared_routes):
                route, source_method, target_method = matched_route or (sorted(shared_routes)[0], str(source.get("http_method") or ""), str(target.get("http_method") or ""))
                method = source_method or target_method
                method_text = f" con metodo {method}" if method else ""
                exact_method = bool(source_method and target_method and source_method == target_method)
                add(
                    source,
                    target,
                    "chiama API",
                    f"Lo scanner ha trovato la stessa route `{route}`{method_text} nella UI e nel backend.",
                    kind="calls_api",
                    evidence=f"{method + ' ' if method else ''}{route}",
                    contract=node_contract(route, method),
                    confidence="high" if exact_method else "medium",
                )
                continue

            source_text = " ".join(file_text(project, rel, cache).lower() for rel in list(source_files)[:3])
            target_model = str(target.get("data_model") or "").lower()
            data_evidence_terms = source_terms & target_terms
            if target_model and target_model in source_text:
                data_evidence_terms.add(target_model)
            if source_layer == "backend" and target_layer == "data" and (data_evidence_terms or source_files & target_files):
                evidence = ", ".join(sorted(data_evidence_terms or (source_files & target_files))[:2])
                add(
                    source,
                    target,
                    "usa dati",
                    "Lo scanner ha trovato riferimenti concreti tra logica backend e modello dati.",
                    kind="uses_data",
                    evidence=evidence,
                    confidence="high" if data_evidence_terms else "medium",
                )
                continue

            test_text = " ".join(file_text(project, rel, cache).lower() for rel in list(source_files)[:2]) if source_layer == "qa" else ""
            test_evidence_terms = source_terms & target_terms
            for term in target_terms:
                if term in test_text:
                    test_evidence_terms.add(term)
            if source_layer == "qa" and test_evidence_terms:
                evidence = ", ".join(sorted(test_evidence_terms)[:2])
                add(
                    source,
                    target,
                    "verifica",
                    "Lo scanner test ha trovato parole chiave o riferimenti nel file di test.",
                    kind="verifies",
                    evidence=evidence,
                    confidence="high" if test_text else "medium",
                )
                continue

            if source_layer == "frontend" and target_layer == "frontend" and shared_routes:
                route = sorted(shared_routes)[0]
                add(
                    source,
                    target,
                    "naviga a",
                    f"Lo scanner UI ha trovato un collegamento di navigazione verso `{route}`.",
                    kind="navigates",
                    evidence=route,
                    confidence="suggested",
                )

    for item in reports:
        relations = [rel for rel in item.get("plain_relations", []) if isinstance(rel, dict)]
        item["plain_relations"] = sorted(relations, key=lambda rel: 0 if rel.get("confidence") == "high" else 1)[:6]
        if item["plain_relations"]:
            first = item["plain_relations"][0]
            item["plain_connection"] = f"{first.get('relation', 'Parla con')} {first.get('title', '')}: {first.get('reason', '')}"
        else:
            item["plain_connection"] = "Non ho ancora abbastanza indizi per spiegare un collegamento chiaro."


def attach_gap_status(reports: list[dict[str, object]]) -> None:
    implementation_nodes = [item for item in reports if item.get("origin") in {"code", "scanner"}]
    for item in reports:
        origin = str(item.get("origin") or "")
        if origin != "design":
            item["gap_status"] = "extra_code" if origin in {"code", "scanner"} else "ok"
            item["gap_reason"] = "Rilevato dal codice/scanner; non e' ancora un requisito design esplicito." if item["gap_status"] == "extra_code" else ""
            continue
        item_terms = normalized_terms_for_match(item)
        matched = False
        for candidate in implementation_nodes:
            if same_contract_surface(item, candidate):
                matched = True
                break
            candidate_terms = normalized_terms_for_match(candidate)
            if item_terms and len(item_terms & candidate_terms) >= min(2, len(item_terms)):
                matched = True
                break
        item["gap_status"] = "ok" if matched or item.get("health") in {"covered", "partial"} else "missing_code"
        item["gap_reason"] = "" if item["gap_status"] == "ok" else "Questo nodo e' nel design, ma lo scanner non trova ancora un pezzo di codice corrispondente."


def attach_audit_status(reports: list[dict[str, object]]) -> None:
    incoming: dict[str, list[dict[str, object]]] = {}
    for source in reports:
        for rel in source.get("plain_relations", []) if isinstance(source.get("plain_relations"), list) else []:
            if not isinstance(rel, dict):
                continue
            target_id = str(rel.get("id") or "")
            if target_id:
                incoming.setdefault(target_id, []).append({**rel, "source_id": source.get("id", ""), "source_title": source.get("title", "")})

    for item in reports:
        item_id = str(item.get("id") or "")
        layer = str(item.get("layer") or "")
        kind = str(item.get("kind") or "")
        health = str(item.get("health") or "")
        ui_route = str(item.get("ui_route") or "")
        api_route = str(item.get("api_route") or "")
        evidence = str(item.get("scanner_evidence") or "")
        outgoing = [rel for rel in item.get("plain_relations", []) if isinstance(rel, dict)]
        incoming_rels = incoming.get(item_id, [])
        all_rels = outgoing + incoming_rels
        high_rels = [rel for rel in all_rels if rel.get("confidence") == "high"]
        medium_rels = [rel for rel in all_rels if rel.get("confidence") in {"medium", "suggested"}]
        outgoing_calls = [rel for rel in outgoing if rel.get("kind") == "calls_api"]
        incoming_calls = [rel for rel in incoming_rels if rel.get("kind") == "calls_api"]
        outgoing_data = [rel for rel in outgoing if rel.get("kind") == "uses_data"]
        incoming_data = [rel for rel in incoming_rels if rel.get("kind") == "uses_data"]
        outgoing_tests = [rel for rel in outgoing if rel.get("kind") == "verifies"]
        incoming_tests = [rel for rel in incoming_rels if rel.get("kind") == "verifies"]

        status = "certo" if high_rels else ("probabile" if medium_rels else "debole")
        reason = "Collegamento confermato da route/metodo o riferimento concreto nel codice." if high_rels else "Lo scanner ha indizi, ma non abbastanza prove forti."
        problem = ""
        fix = "Nessuna azione urgente: controlla solo se il collegamento ha senso per te."

        if layer == "frontend" and kind == "action" and not ui_route and not outgoing_calls:
            status = "rotto"
            problem = "azione_senza_destinazione"
            reason = "Vedo un bottone/azione, ma non trovo una route o una API chiamata."
            fix = "Apri il file indicato e verifica cosa dovrebbe fare il bottone: navigare, chiamare API o essere solo UI."
        elif layer == "frontend" and ui_route and not outgoing_calls and kind != "navigation":
            status = "rotto"
            problem = "ui_senza_backend"
            reason = "La UI sembra chiamare una route, ma non trovo un endpoint backend corrispondente."
            fix = "Crea o collega l'endpoint backend, oppure correggi la route usata dalla UI."
        elif layer == "backend" and kind == "api" and api_route and not incoming_calls:
            status = "debole"
            problem = "api_non_chiamata"
            reason = "Endpoint trovato nel backend, ma nessuna UI sembra chiamarlo."
            fix = "Verifica se e' un endpoint interno/legacy; se serve all'app, collega una schermata o un'azione."
        elif layer == "data" and kind == "model" and not incoming_data:
            status = "debole"
            problem = "dato_non_usato"
            reason = "Modello dati trovato, ma non vedo ancora logica backend che lo usa."
            fix = "Controlla se e' un modello pronto per futuro uso o se manca il service/controller."
        elif layer not in {"qa", "docs", "devops"} and not incoming_tests and not outgoing_tests and health in {"partial", "covered"}:
            problem = "test_non_chiaro"
            reason = "Il codice esiste, ma non ho trovato un test chiaramente collegato."
            fix = "Aggiungi o collega un test sul flusso principale di questo nodo."
        elif str(item.get("gap_status") or "") == "missing_code":
            status = "rotto"
            problem = "design_senza_codice"
            reason = "Il design prevede questo nodo, ma lo scanner non trova codice corrispondente."
            fix = "Implementa una slice minima o correggi il nome del nodo per farlo combaciare col codice."
        elif evidence and not all_rels:
            status = "debole"
            reason = "Ho trovato il nodo nel codice, ma non ho ancora prove chiare dei collegamenti."
            fix = "Controlla se il file usa route, service, modello dati o test con nomi riconoscibili."

        item["audit_status"] = status
        item["audit_problem"] = problem
        item["audit_reason"] = reason
        item["audit_fix"] = fix
        item["audit_incoming"] = len(incoming_rels)
        item["audit_outgoing"] = len(outgoing)


def audit_summary(reports: list[dict[str, object]]) -> dict[str, object]:
    counts: dict[str, int] = {}
    problems: list[dict[str, object]] = []
    for item in reports:
        status = str(item.get("audit_status") or "debole")
        counts[status] = counts.get(status, 0) + 1
        if item.get("audit_problem") or status == "rotto":
            problems.append(
                {
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "status": status,
                    "problem": item.get("audit_problem", ""),
                    "reason": item.get("audit_reason", ""),
                    "fix": item.get("audit_fix", ""),
                    "evidence": item.get("scanner_evidence", ""),
                }
            )
    order = {"rotto": 0, "debole": 1, "probabile": 2, "certo": 3}
    problems.sort(key=lambda item: (order.get(str(item.get("status")), 9), str(item.get("title", ""))))
    return {
        "counts": [{"status": key, "nodes": value} for key, value in sorted(counts.items(), key=lambda item: (order.get(item[0], 9), item[0]))],
        "problems": problems[:18],
        "fix_plan": audit_fix_plan(problems),
    }


def audit_fix_plan(problems: list[dict[str, object]], limit: int = 10) -> list[dict[str, object]]:
    priority_by_status = {"rotto": 1, "debole": 2, "probabile": 3, "certo": 4}
    action_by_problem = {
        "azione_senza_destinazione": "Decidi cosa deve fare questo bottone o comando.",
        "ui_senza_backend": "Allinea la route chiamata dalla UI con un endpoint backend reale.",
        "api_non_chiamata": "Verifica se questa API serve ancora o se manca il collegamento dalla UI.",
        "dato_non_usato": "Collega il modello dati a un service/controller oppure segnalo come dato futuro.",
        "test_non_chiaro": "Aggiungi un test piccolo sul flusso principale del nodo.",
        "design_senza_codice": "Implementa una prima slice minima o rinomina il nodo design per farlo combaciare col codice.",
    }
    check_by_problem = {
        "azione_senza_destinazione": "Dopo il fix, lo scanner deve vedere una navigazione o una chiamata API.",
        "ui_senza_backend": "Dopo il fix, la linea UI -> backend deve diventare certa o almeno probabile.",
        "api_non_chiamata": "Dopo il fix, l'API deve avere una UI chiamante o una nota chiara di uso interno.",
        "dato_non_usato": "Dopo il fix, deve comparire un collegamento backend -> dati.",
        "test_non_chiaro": "Dopo il fix, il nodo deve avere un collegamento verifica/test.",
        "design_senza_codice": "Dopo il fix, il gap deve sparire dalla vista Problemi.",
    }
    plan = []
    for index, item in enumerate(problems[:limit], 1):
        problem = str(item.get("problem") or "")
        status = str(item.get("status") or "debole")
        plan.append(
            {
                "priority": priority_by_status.get(status, 3),
                "step": index,
                "node": item.get("title", ""),
                "problem": problem or status,
                "action": action_by_problem.get(problem, str(item.get("fix") or "Controlla il nodo e rendi esplicito il collegamento.")),
                "why": item.get("reason", ""),
                "evidence": item.get("evidence", ""),
                "check": check_by_problem.get(problem, "Rigenera la dashboard e controlla che lo stato audit migliori."),
            }
        )
    return sorted(plan, key=lambda item: (int(item.get("priority", 9)), int(item.get("step", 99))))[:limit]


def node_focus_rank(item: dict[str, object]) -> int:
    if is_known_noise_node(item):
        return 999
    rank = {
        "rotto": 0,
        "debole": 20,
        "probabile": 45,
        "certo": 80,
    }.get(str(item.get("audit_status") or ""), 50)
    rank += {
        "missing": 0,
        "idea": 10,
        "partial": 18,
        "covered": 35,
    }.get(str(item.get("health") or ""), 25)
    problem = str(item.get("audit_problem") or "")
    if problem == "test_non_chiaro":
        rank += 12
    elif problem:
        rank -= 8
    else:
        rank += 25
    if str(item.get("layer") or "") == "frontend":
        rank -= 3
    if str(item.get("layer") or "") == "devops" and str(item.get("kind") or "") == "runtime":
        rank += 20
    if item.get("plain_relations"):
        rank -= 2
    return max(0, rank)


def relation_targets(source: dict[str, object], reports_by_id: dict[str, dict[str, object]], kind: str) -> list[dict[str, object]]:
    found = []
    for rel in source.get("plain_relations", []) if isinstance(source.get("plain_relations"), list) else []:
        if not isinstance(rel, dict) or rel.get("kind") != kind:
            continue
        target = reports_by_id.get(str(rel.get("id") or ""))
        if target:
            found.append(target)
    return found


def incoming_relation_sources(target: dict[str, object], reports: list[dict[str, object]], kind: str) -> list[dict[str, object]]:
    target_id = str(target.get("id") or "")
    found = []
    for source in reports:
        for rel in source.get("plain_relations", []) if isinstance(source.get("plain_relations"), list) else []:
            if isinstance(rel, dict) and rel.get("kind") == kind and str(rel.get("id") or "") == target_id:
                found.append(source)
    return found


def build_flow_traces(reports: list[dict[str, object]], limit: int = 16) -> dict[str, object]:
    by_id = {str(item.get("id", "")): item for item in reports}
    starts = [
        item for item in reports
        if item.get("layer") == "frontend" and item.get("kind") in {"action", "navigation", "screen"} and (item.get("ui_route") or item.get("plain_relations"))
    ]
    flows = []
    for start in starts[:limit * 2]:
        api_nodes = relation_targets(start, by_id, "calls_api")
        data_nodes: list[dict[str, object]] = []
        test_nodes: list[dict[str, object]] = []
        for api in api_nodes:
            data_nodes.extend(relation_targets(api, by_id, "uses_data"))
            test_nodes.extend(incoming_relation_sources(api, reports, "verifies"))
        test_nodes.extend(incoming_relation_sources(start, reports, "verifies"))
        unique_data = list({str(item.get("id")): item for item in data_nodes}.values())
        unique_tests = list({str(item.get("id")): item for item in test_nodes}.values())

        if api_nodes and unique_data and unique_tests:
            status = "completo"
            problem = ""
            next_step = "Flusso leggibile: mantieni nomi e test allineati."
        elif api_nodes and unique_data:
            status = "parziale"
            problem = "manca_test"
            next_step = "Aggiungi o collega un test che copra questo flusso."
        elif api_nodes:
            status = "parziale"
            problem = "dati_non_chiari"
            next_step = "Collega l'API ai modelli dati o rendi piu esplicito il service usato."
        elif start.get("ui_route"):
            status = "rotto"
            problem = "backend_non_trovato"
            next_step = "Crea o collega l'endpoint backend chiamato dalla UI."
        else:
            status = "rotto"
            problem = "azione_non_tracciabile"
            next_step = "Rendi esplicita la destinazione del bottone o dell'azione."

        chain = [str(start.get("title") or "Azione UI")]
        chain.extend(str(item.get("title") or "") for item in api_nodes[:2])
        chain.extend(str(item.get("title") or "") for item in unique_data[:2])
        chain.extend(str(item.get("title") or "") for item in unique_tests[:1])
        flows.append(
            {
                "id": f"flow-{slug(str(start.get('id') or start.get('title') or len(flows)))}",
                "title": f"Flusso: {str(start.get('title') or 'azione').replace('Action: ', '').replace('Button: ', '')}",
                "status": status,
                "problem": problem,
                "start_node": start.get("id", ""),
                "start": start.get("title", ""),
                "api": ", ".join(str(item.get("title") or "") for item in api_nodes[:3]) or "n/d",
                "data": ", ".join(str(item.get("title") or "") for item in unique_data[:3]) or "n/d",
                "tests": ", ".join(str(item.get("title") or "") for item in unique_tests[:3]) or "n/d",
                "chain": " -> ".join(item for item in chain if item),
                "next_step": next_step,
                "node_ids": [str(item.get("id") or "") for item in [start, *api_nodes, *unique_data, *unique_tests] if item.get("id")],
            }
        )

    order = {"rotto": 0, "parziale": 1, "completo": 2}
    flows.sort(key=lambda item: (order.get(str(item.get("status")), 9), str(item.get("title", ""))))
    counts: dict[str, int] = {}
    for item in flows:
        status = str(item.get("status") or "parziale")
        counts[status] = counts.get(status, 0) + 1
    return {
        "counts": [{"status": key, "flows": value} for key, value in sorted(counts.items(), key=lambda item: (order.get(item[0], 9), item[0]))],
        "items": flows[:limit],
    }


def plain_node_summary(node: dict[str, object], related: list[str]) -> str:
    node_type = str(node.get("inferred_type") or "feature")
    domain = str(node.get("domain") or "product")
    title = str(node.get("title") or "Questo nodo").strip()
    free_text = str(node.get("free_text") or "").strip()
    summary = f"{title}: {type_action(node_type)} {domain_place(domain)}."
    if free_text and free_text != title:
        summary += f" In pratica: {free_text.rstrip('. ')}."
    route = str(node.get("ui_route") or node.get("api_route") or "").strip()
    method = str(node.get("http_method") or "").strip()
    if route:
        summary += f" Route rilevata: {method + ' ' if method else ''}{route}."
    if related:
        summary += f" Il primo file collegato e' {related[0]}."
    return summary


def relationship_reason(source: dict[str, object], target: dict[str, object], explicit: bool = False) -> str:
    if explicit:
        return "Collegamento dichiarato nel Blueprint."
    source_domain = str(source.get("domain") or "product")
    target_domain = str(target.get("domain") or "product")
    target_type = str(target.get("type") or "")
    if source_domain == "frontend" and target_domain == "backend":
        return "La UI di solito chiama API o servizi backend per leggere o salvare dati."
    if source_domain == "frontend" and target_domain == "data":
        return "La schermata mostra dati che arrivano dal modello o dal database."
    if source_domain == "backend" and target_domain == "data":
        return "Il backend usa dati, query o modelli per rispondere alle richieste."
    if source_domain == "qa":
        return "Questo controllo verifica che l'altro nodo non si rompa."
    if source_domain == "docs":
        return "Questa documentazione spiega come usare o mantenere l'altro nodo."
    if source_domain == "devops":
        return "Runtime, cache, config o deploy servono a far girare questo pezzo."
    if target_type == "test":
        return "Esiste o serve un test collegato a questa parte."
    return "Sono nello stesso flusso o nella stessa area del progetto."


def attach_plain_relationships(reports: list[dict[str, object]]) -> None:
    by_id = {str(item.get("id", "")): item for item in reports}

    def first_matching(source: dict[str, object], *, domain: str | None = None, node_type: str | None = None) -> dict[str, object] | None:
        for candidate in reports:
            if candidate is source:
                continue
            if domain and candidate.get("domain") != domain:
                continue
            if node_type and candidate.get("type") != node_type:
                continue
            return candidate
        return None

    for item in reports:
        relations: list[dict[str, object]] = []
        seen: set[str] = set()
        title = str(item.get("title", ""))

        def add(target: dict[str, object] | None, reason: str, relation: str = "parla con", confidence: str = "suggested") -> None:
            if not target:
                return
            target_id = str(target.get("id", ""))
            if not target_id or target_id == str(item.get("id", "")) or target_id in seen:
                return
            seen.add(target_id)
            relations.append(
                {
                    "id": target_id,
                    "title": target.get("title", ""),
                    "relation": relation,
                    "reason": reason,
                    "confidence": confidence,
                }
            )

        parent_id = str(item.get("parent_id") or "")
        add(by_id.get(parent_id), relationship_reason(item, by_id[parent_id], explicit=True) if parent_id in by_id else "", "dipende da", "high")
        for dep_id in item.get("depends_on", []) if isinstance(item.get("depends_on"), list) else []:
            dep_key = str(dep_id)
            add(by_id.get(dep_key), relationship_reason(item, by_id[dep_key], explicit=True) if dep_key in by_id else "", "dipende da", "high")

        domain = str(item.get("domain") or "product")
        node_type = str(item.get("type") or "")
        if domain == "frontend":
            add(first_matching(item, domain="backend"), relationship_reason(item, {"domain": "backend"}))
            add(first_matching(item, domain="data"), relationship_reason(item, {"domain": "data"}))
        elif domain == "backend":
            add(first_matching(item, domain="data"), relationship_reason(item, {"domain": "data"}))
            add(first_matching(item, node_type="auth"), "Usa o protegge accessi e sessioni quando il flusso richiede permessi.")
        elif domain == "qa":
            add(first_matching(item, domain="frontend"), relationship_reason(item, {"domain": "frontend"}), "verifica")
            add(first_matching(item, domain="backend"), relationship_reason(item, {"domain": "backend"}), "verifica")
            add(first_matching(item, domain="product"), "Questo controllo verifica che la funzionalita principale resti corretta.", "verifica")
        elif domain == "docs":
            add(first_matching(item, domain="product"), relationship_reason(item, {"domain": "product"}), "spiega")
            add(first_matching(item, domain="devops"), relationship_reason(item, {"domain": "devops"}), "spiega")
        elif domain == "devops":
            if not title.startswith(("Script:", "Config:")):
                add(first_matching(item, domain="frontend"), relationship_reason(item, {"domain": "frontend"}), "fa girare")
                add(first_matching(item, domain="backend"), relationship_reason(item, {"domain": "backend"}), "fa girare")
                add(first_matching(item, domain="product"), relationship_reason(item, {"domain": "product"}), "fa girare")
        elif domain == "product":
            add(first_matching(item, domain="docs"), "Le regole e i documenti spiegano come trasformare questa idea in lavoro pratico.", "e spiegato da")
            add(first_matching(item, domain="devops"), "Il runtime o la dashboard rendono visibile e usabile questa parte.", "usa")
        elif node_type == "auth":
            add(first_matching(item, domain="backend"), "Il login passa dal server per sessioni, permessi o provider.")
            add(first_matching(item, domain="frontend"), "L'utente usa una schermata o un componente per accedere.")

        item["plain_relations"] = relations[:3]
        if relations:
            first = relations[0]
            item["plain_connection"] = f"Parla con {first.get('title', '')}: {first.get('reason', '')}"
        else:
            item["plain_connection"] = "Non ho ancora abbastanza indizi per spiegare un collegamento chiaro."


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
        "plain_summary": plain_node_summary({**node, "domain": domain}, related),
        "type": node.get("inferred_type", ""),
        "origin": node_origin(node),
        "layer": node.get("layer") or node_layer(domain, str(node.get("inferred_type", ""))),
        "kind": node.get("kind") or node_kind(str(node.get("title", "")), str(node.get("inferred_type", "")), related),
        "domain": domain,
        "status": node.get("status", ""),
        "parent_id": node.get("parent_id", ""),
        "depends_on": node.get("depends_on", []),
        "layout_x": node.get("layout_x"),
        "layout_y": node.get("layout_y"),
        "health": health,
        "reason": reason,
        "test_signal": test_signal,
        "related_files": related,
        "ui_route": node.get("ui_route", ""),
        "api_route": node.get("api_route", ""),
        "http_method": node.get("http_method", ""),
        "contract": node.get("contract", {}) if isinstance(node.get("contract"), dict) else {},
        "scanner_evidence": node.get("scanner_evidence", ""),
        "data_model": node.get("data_model", ""),
        "next_action": next_action,
    }


def doctor(project: Path) -> dict[str, object]:
    data = load_blueprint(project)
    nodes = nodes_with_import_preview(project, data, 90)
    files = project_files(project)
    node_reports = [node_doctor(project, item, files) for item in nodes[:90]]
    attach_plain_relationships(node_reports)
    attach_scanner_relationships(project, node_reports)
    apply_edge_feedback(project, node_reports)
    attach_gap_status(node_reports)
    attach_audit_status(node_reports)
    flows = build_flow_traces(node_reports)
    counts: dict[str, int] = {}
    for item in node_reports:
        health = str(item.get("health", "unknown"))
        counts[health] = counts.get(health, 0) + 1
    ranked_focus = sorted(
        [item for item in node_reports if not is_known_noise_node(item)],
        key=lambda item: (node_focus_rank(item), str(item.get("title", ""))),
    )
    suggestions = [update_suggestion(item) for item in node_reports]
    return {
        "path": str(blueprint_path(project)),
        "exists": blueprint_path(project).exists(),
        "files_scanned": len(files),
        "nodes_checked": len(node_reports),
        "health_counts": [{"health": key, "nodes": value} for key, value in sorted(counts.items(), key=lambda item: (-item[1], item[0]))],
        "next_focus": ranked_focus[0] if ranked_focus else (node_reports[0] if node_reports else {}),
        "nodes": node_reports,
        "suggestions": suggestions,
        "audit": audit_summary(node_reports),
        "flows": flows,
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
    nodes = nodes_with_import_preview(project, data, 90)
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
    for item in nodes[:90]:
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
                "preview_only": item.get("preview_only", False),
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
