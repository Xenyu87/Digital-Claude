#!/usr/bin/env python3
"""Small HTML helpers for the local dashboard."""

from __future__ import annotations

import html
import json
from pathlib import Path


DASHBOARD_CSS = """
    :root { color-scheme: light; --ink:#182330; --muted:#5c6876; --line:#d9e0e8; --panel:#f6f8fb; --soft:#edf4f7; --ok:#1f7a4d; --bad:#b42318; --accent:#2563a8; --accent-soft:#e8f1fb; --warm:#8a5a16; --warm-soft:#fff4df; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Inter, Segoe UI, Arial, sans-serif; color:var(--ink); background:#f8fafc; }
    header { padding:26px 32px 18px; border-bottom:1px solid var(--line); background:#ffffff; }
    main { padding:24px 32px 42px; width:100%; max-width:none; }
    h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
    h2 { margin:26px 0 12px; font-size:17px; letter-spacing:0; }
    p { line-height:1.45; }
    .muted { color:var(--muted); }
    .topline { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
    .badge { display:inline-flex; align-items:center; min-height:28px; padding:5px 9px; border:1px solid var(--line); border-radius:8px; background:#fff; color:var(--muted); font-size:13px; }
    .simple-view { display:grid; grid-template-columns:minmax(0,1.5fr) minmax(280px,.8fr); gap:14px; align-items:stretch; margin:8px 0 16px; }
    .hero-card { border:1px solid #cbd8e6; border-radius:8px; background:#ffffff; padding:20px; box-shadow:0 10px 28px rgba(24,35,48,.07); }
    .hero-label { color:var(--accent); font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:0; }
    .hero-action { font-size:30px; line-height:1.12; font-weight:800; margin:8px 0 10px; letter-spacing:0; }
    .hero-reason { color:var(--muted); font-size:15px; max-width:760px; }
    .section-label { display:inline-flex; align-items:center; width:max-content; min-height:23px; padding:3px 8px; border-radius:999px; background:#eef3f7; color:#334155; font-size:12px; font-weight:800; margin-bottom:6px; }
    .home-actions { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:16px; }
    .button-link { display:inline-flex; align-items:center; min-height:35px; padding:8px 11px; border:1px solid var(--accent); border-radius:6px; background:var(--accent); color:#fff; text-decoration:none; font-weight:800; font-size:14px; }
    .button-link:hover { background:#1f4f82; }
    .button-link.secondary { background:#fff; color:var(--accent); }
    .button-link.secondary:hover { background:var(--accent-soft); }
    .dashboard-tabs { position:sticky; top:0; z-index:20; display:flex; flex-wrap:wrap; gap:8px; align-items:center; padding:10px 0 14px; background:#f8fafc; border-bottom:1px solid var(--line); margin:-8px 0 18px; }
    .tab-button { display:inline-flex; align-items:center; min-height:36px; padding:8px 12px; border:1px solid var(--line); border-radius:6px; background:#fff; color:#334155; font-weight:800; cursor:pointer; }
    .tab-button:hover { background:var(--accent-soft); border-color:#9fb2c7; }
    .tab-button.is-active { background:var(--accent); border-color:var(--accent); color:#fff; }
    .dashboard-section { display:none; }
    .dashboard-section.is-active { display:block; }
    .section-kicker { margin:0 0 14px; color:var(--muted); max-width:860px; }
    .quick-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
    .quick-card { border:1px solid var(--line); border-radius:8px; background:#fff; padding:14px; min-height:96px; }
    .quick-card strong { display:block; font-size:22px; margin-top:6px; }
    .guidance-board { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:10px; margin:14px 0 4px; }
    .issue-card { border:1px solid var(--line); border-left:5px solid var(--warm); border-radius:8px; background:#fff; padding:13px; min-height:170px; }
    .issue-card:first-child { border-left-color:var(--bad); }
    .issue-title { font-weight:800; margin:4px 0 8px; line-height:1.25; overflow-wrap:anywhere; }
    .issue-row { margin-top:7px; color:var(--muted); line-height:1.35; }
    .issue-row strong { color:var(--ink); }
    .project-switcher { border:1px solid #cbd8e6; border-radius:8px; background:#fff; padding:14px; margin:0 0 18px; box-shadow:0 6px 18px rgba(24,35,48,.05); }
    .project-switcher h2 { margin:0 0 4px; }
    .project-switcher-form { display:grid; grid-template-columns:minmax(220px,420px) minmax(280px,1fr) auto; gap:8px; align-items:center; margin:12px 0; }
    .project-switcher-form input[type=text] { flex:1; width:auto; }
    .project-menu { width:100%; }
    .project-table-wrap { max-height:260px; overflow:auto; border:1px solid var(--line); border-radius:8px; }
    .project-table-wrap table { border:0; border-radius:0; }
    .blueprint-panel { border:1px solid #cbd8e6; border-radius:8px; background:#fff; padding:16px; margin:8px 0 14px; }
    .blueprint-focus { display:grid; grid-template-columns:minmax(0,1.3fr) minmax(240px,.7fr); gap:12px; align-items:stretch; }
    .blueprint-title { font-size:22px; font-weight:800; line-height:1.15; overflow-wrap:anywhere; }
    .blueprint-command-row { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:14px; }
    .blueprint-status-card { border:1px solid var(--line); border-radius:8px; background:#fbfcfe; padding:12px; }
    .blueprint-status-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin-top:12px; }
    .blueprint-status-grid div { border:1px solid var(--line); border-radius:8px; background:#fff; padding:10px; min-height:72px; }
    .blueprint-status-grid strong { display:block; font-size:22px; line-height:1; }
    .blueprint-status-grid span { display:block; color:var(--muted); font-size:12px; line-height:1.25; margin-top:6px; }
    .blueprint-workbench { background:#fbfcfe; }
    .blueprint-lane { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:10px; margin-top:12px; }
    .blueprint-lane.is-filtered .node-card { display:none; }
    .blueprint-lane.is-filtered .node-card.is-visible { display:block; }
    .blueprint-tools { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin:12px 0 10px; }
    .blueprint-search { min-width:min(360px,100%); flex:1; }
    .blueprint-detail { border:1px solid var(--line); border-radius:8px; background:#fff; padding:12px; margin:10px 0; min-height:86px; }
    .blueprint-detail-title { font-weight:800; margin-bottom:6px; }
    .blueprint-detail-body { color:var(--muted); line-height:1.4; }
    .blueprint-detail-links { margin:8px 0 0; padding-left:18px; color:var(--muted); }
    .domain-filter.is-active { background:var(--accent); color:#fff; }
    .screenshot-drop { border:1px dashed #9fb2c7; border-radius:8px; background:#fbfcfe; padding:14px; margin:12px 0; outline:none; }
    .screenshot-drop:focus { border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-soft); }
    .screenshot-drop strong { display:block; margin-bottom:4px; }
    .screenshot-status { color:var(--muted); margin-top:6px; }
    .blueprint-map { width:100%; height:clamp(460px, 68vh, 760px); border:1px solid var(--line); border-radius:8px; background:#fbfcfe; margin-top:14px; overflow:hidden; touch-action:none; }
    .blueprint-map svg { width:100%; height:100%; display:block; }
    .map-line { stroke:#93a4b8; stroke-width:2; fill:none; marker-end:url(#arrow); opacity:0; pointer-events:none; }
    .blueprint-graph.show-all-lines .map-line:not(.is-hidden) { opacity:.18; }
    .map-line.is-dim { opacity:0; }
    .map-line.is-strong { stroke:var(--accent); stroke-width:3; opacity:1; }
    .map-label { display:none; }
    .map-label.is-strong { display:block; fill:var(--accent); font-weight:800; }
    .map-node { cursor:grab; }
    .map-node:active { cursor:grabbing; }
    .map-node rect { fill:#fff; stroke:#cbd8e6; stroke-width:1.4; rx:8; filter:drop-shadow(0 2px 5px rgba(24,35,48,.06)); }
    .map-node.covered rect { stroke:var(--ok); }
    .map-node.partial rect { stroke:var(--warm); }
    .map-node.missing rect { stroke:var(--bad); }
    .map-node:hover .map-box { stroke:var(--accent); stroke-width:2.4; filter:drop-shadow(0 8px 16px rgba(24,35,48,.18)); }
    .map-node.is-dim { opacity:.2; }
    .map-node.is-hidden { display:none; }
    .map-node.is-selected .map-box { stroke:var(--accent); stroke-width:3; filter:drop-shadow(0 10px 18px rgba(24,35,48,.22)); }
    .map-node.is-related .map-box { stroke:#5b7c9f; stroke-width:2.2; }
    .map-title { font-size:15px; font-weight:800; fill:var(--ink); }
    .map-meta { font-size:12px; fill:var(--muted); }
    .map-popover { display:none; pointer-events:none; }
    .map-node:hover .map-popover { display:block; }
    .map-popover rect { fill:#fff; stroke:var(--accent); stroke-width:1.5; filter:drop-shadow(0 12px 24px rgba(24,35,48,.22)); }
    .map-popover-title { font-size:16px; font-weight:800; fill:var(--ink); }
    .map-popover-text { font-size:13px; fill:var(--ink); }
    .map-popover-muted { font-size:12px; fill:var(--muted); }
    .node-card { border:1px solid var(--line); border-left:5px solid var(--accent); border-radius:8px; background:#fff; padding:12px; min-height:128px; }
    .node-card.covered { border-left-color:var(--ok); }
    .node-card.partial { border-left-color:var(--warm); }
    .node-card.idea { border-left-color:var(--accent); }
    .node-card.missing { border-left-color:var(--bad); }
    .node-name { font-weight:800; margin:6px 0; overflow-wrap:anywhere; }
    .node-desc { color:var(--muted); line-height:1.35; margin:6px 0 8px; }
    .node-plain { line-height:1.4; margin:8px 0; }
    .node-links { margin:8px 0 0; padding-left:18px; color:var(--muted); line-height:1.35; }
    .node-links strong { color:var(--ink); }
    .chip-row { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
    .chip { display:inline-flex; align-items:center; min-height:24px; padding:3px 8px; border-radius:999px; background:var(--accent-soft); color:#1f4f82; font-size:12px; font-weight:700; }
    .chip.warn { background:var(--warm-soft); color:var(--warm); }
    .chip.bad { background:#fee4e2; color:var(--bad); }
    .chip.ok { background:#e7f6ee; color:var(--ok); }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; }
    .card { border:1px solid var(--line); border-radius:8px; padding:14px; background:#ffffff; }
    .metric { font-size:24px; font-weight:800; margin-top:6px; line-height:1.15; overflow-wrap:anywhere; }
    .pass { color:var(--ok); font-weight:700; }
    .fail { color:var(--bad); font-weight:700; }
    .pill { display:inline-block; padding:3px 8px; border:1px solid var(--line); border-radius:999px; margin:2px; background:#fff; }
    .task-table { margin-top:8px; }
    .button-row { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:8px; }
    table { width:100%; border-collapse:collapse; font-size:13px; background:#fff; border:1px solid var(--line); border-radius:8px; overflow:hidden; }
    th, td { border-bottom:1px solid var(--line); padding:9px; text-align:left; vertical-align:top; }
    th { background:#eef3f7; color:#334155; }
    pre { white-space:pre-wrap; border:1px solid var(--line); background:#fbfcfe; border-radius:8px; padding:12px; overflow:auto; }
    details { border:1px solid var(--line); border-radius:8px; padding:12px 14px; margin:12px 0; background:#fff; }
    details.inline-details { margin:10px 0 0; padding:10px; background:#fbfcfe; }
    summary { cursor:pointer; font-weight:800; }
    .detail-band { background:#fff; border:1px solid var(--line); border-radius:8px; padding:14px; margin-top:14px; }
    form { margin:0; display:inline; }
    input[type=text] { width:min(720px, 100%); padding:10px; border:1px solid var(--line); border-radius:6px; font:inherit; background:#fff; }
    textarea { width:100%; min-height:72px; padding:10px; border:1px solid var(--line); border-radius:6px; font:inherit; background:#fff; resize:vertical; }
    .design-form { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:10px; align-items:start; }
    .design-form label { display:block; font-weight:800; font-size:13px; margin-bottom:4px; }
    .design-form .wide { grid-column:1 / -1; }
    .design-preview { border:1px solid var(--line); border-radius:8px; background:#fbfcfe; padding:12px; margin:10px 0; }
    .design-preview h3 { margin:0 0 8px; font-size:15px; }
    .design-preview-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:8px; }
    .design-preview ul { margin:4px 0 0; padding-left:18px; color:var(--muted); }
    select { width:100%; padding:10px; border:1px solid var(--line); border-radius:6px; font:inherit; background:#fff; }
    button { padding:8px 11px; border:1px solid var(--accent); border-radius:6px; background:#fff; color:var(--accent); font-weight:700; cursor:pointer; }
    button:hover { background:var(--accent-soft); }
    @media (max-width: 820px) { body { background:#fff; } header, main { padding-left:18px; padding-right:18px; } .dashboard-tabs { position:static; } .tab-button { flex:1; justify-content:center; } .simple-view, .blueprint-focus { grid-template-columns:1fr; } .hero-action { font-size:24px; } .quick-grid { grid-template-columns:1fr; } .project-switcher-form { grid-template-columns:1fr; align-items:stretch; } .project-switcher-form input[type=text] { width:100%; } }
"""


def status_label(returncode: int) -> str:
    return "PASS" if returncode == 0 else "FAIL"


def esc(value: object) -> str:
    return html.escape(str(value))


def render_table(rows: list[dict[str, object]], columns: list[str]) -> str:
    head = "".join(f"<th>{esc(column)}</th>" for column in columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{esc(row.get(column, ''))}</td>" for column in columns) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def render_blueprint_cards(doctor: dict[str, object]) -> str:
    nodes = [item for item in doctor.get("nodes", []) if isinstance(item, dict)][:90]
    if not nodes:
        return "<div class='blueprint-panel muted'>Nessun nodo Blueprint da visualizzare. <strong>Prossimo passo:</strong> seleziona un progetto o usa Scansiona nodi.</div>"
    cards = []
    for item in nodes:
        health = str(item.get("health", "idea"))
        chip_class = {"covered": "ok", "partial": "warn", "missing": "bad"}.get(health, "")
        relations = [rel for rel in item.get("plain_relations", []) if isinstance(rel, dict)]
        if relations:
            relation_html = (
                "<ul class='node-links'>"
                + "".join(
                    f"<li><strong>{esc(rel.get('relation', 'parla con'))} {esc(rel.get('title', ''))}</strong>: {esc(rel.get('reason', ''))}</li>"
                    for rel in relations[:3]
                )
                + "</ul>"
            )
        else:
            relation_html = f"<div class='node-desc'><strong>Collegamenti:</strong> {esc(item.get('plain_connection', ''))}</div>"
        cards.append(
            f"<article class='node-card {esc(health)}' data-node-card='{esc(item.get('id', ''))}' data-domain='{esc(item.get('domain', 'n/d'))}' data-search='{esc(str(item.get('title', '')) + ' ' + str(item.get('plain_summary', '')) + ' ' + str(item.get('description', '')))}'>"
            f"<div class='chip-row'><span class='chip {chip_class}'>{esc(health)}</span><span class='chip'>{esc(item.get('domain', 'n/d'))}</span></div>"
            f"<div class='node-name'>{esc(item.get('title', ''))}</div>"
            f"<div class='node-plain'><strong>Cosa fa:</strong> {esc(item.get('plain_summary') or item.get('description', ''))}</div>"
            f"<div class='node-desc'><strong>Dettaglio rilevato:</strong> {esc(item.get('description', ''))}</div>"
            f"<div class='node-plain'><strong>Parla con:</strong></div>{relation_html}"
            f"<div class='muted'><strong>Prossimo passo:</strong> {esc(item.get('next_action', ''))}</div>"
            "</article>"
        )
    return "<div class='blueprint-lane' data-blueprint-cards>" + "".join(cards) + "</div>"


def short_text(value: object, limit: int = 52) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "..."


def wrap_text(value: object, limit: int = 46, lines: int = 4) -> list[str]:
    words = str(value or "").split()
    wrapped: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            wrapped.append(current)
        current = word
        if len(wrapped) >= lines:
            break
    if current and len(wrapped) < lines:
        wrapped.append(current)
    if len(wrapped) == lines and len(" ".join(words)) > len(" ".join(wrapped)):
        wrapped[-1] = short_text(wrapped[-1], max(12, limit - 3))
    return wrapped


def issue_kind(item: dict[str, object]) -> str:
    status = str(item.get("status") or item.get("audit_status") or "")
    problem = str(item.get("problem") or item.get("audit_problem") or "")
    if str(item.get("user_feedback") or "") == "ignored":
        return "known_noise"
    if problem in {"azione_senza_destinazione", "ui_senza_backend"} and str(item.get("title", "")).lower().startswith("button:"):
        return "known_noise"
    if status == "rotto":
        return "real_issue"
    if status in {"debole", "probabile"} or problem:
        return "scanner_hypothesis"
    return "technical_detail"


def issue_rank(item: dict[str, object]) -> int:
    status = str(item.get("status") or item.get("audit_status") or "")
    kind = issue_kind(item)
    rank = {"real_issue": 0, "scanner_hypothesis": 20, "technical_detail": 60, "known_noise": 90}.get(kind, 50)
    rank += {"rotto": 0, "debole": 8, "probabile": 16, "certo": 30}.get(status, 20)
    if str(item.get("problem") or "").endswith("test_non_chiaro"):
        rank += 10
    return rank


def build_blueprint_view_model(doctor: dict[str, object], flow_nodes: list[dict[str, object]], flow_edges: list[dict[str, object]]) -> dict[str, object]:
    audit = doctor.get("audit", {}) if isinstance(doctor.get("audit"), dict) else {}
    flows = doctor.get("flows", {}) if isinstance(doctor.get("flows"), dict) else {}
    raw_issues = [item for item in audit.get("problems", []) if isinstance(item, dict)]
    issues = []
    for item in raw_issues:
        classified = dict(item)
        classified["issue_kind"] = issue_kind(classified)
        classified["rank"] = issue_rank(classified)
        issues.append(classified)
    issues.sort(key=lambda item: (int(item.get("rank", 50)), str(item.get("title", ""))))
    visible_issues = [item for item in issues if item.get("issue_kind") != "known_noise"]
    actions = []
    for item in audit.get("fix_plan", []) if isinstance(audit.get("fix_plan"), list) else []:
        if not isinstance(item, dict):
            continue
        actions.append(
            {
                "node": item.get("node", ""),
                "problem": item.get("problem", ""),
                "action": item.get("action", ""),
                "why": item.get("why", ""),
                "check": item.get("check", ""),
                "priority": item.get("priority", 3),
                "task_prompt": "\n".join(
                    [
                        f"Goal: {item.get('action', '')}",
                        f"Nodo: {item.get('node', '')}",
                        f"Problema: {item.get('problem', '')}",
                        f"Perche conta: {item.get('why', '')}",
                        f"Check: {item.get('check', '')}",
                        "Non toccare codice non collegato a questo nodo.",
                    ]
                ),
            }
        )
    actions = actions[:3]
    focus = doctor.get("next_focus", {}) if isinstance(doctor.get("next_focus"), dict) else {}
    if visible_issues:
        focus = {
            "id": visible_issues[0].get("id", focus.get("id", "")),
            "title": visible_issues[0].get("title", focus.get("title", "")),
            "status": visible_issues[0].get("status", ""),
            "problem": visible_issues[0].get("problem", ""),
            "reason": visible_issues[0].get("reason", ""),
            "next_action": visible_issues[0].get("fix", focus.get("next_action", "")),
        }
    return {
        "schema": "blueprint-view-v1",
        "focus": focus,
        "stats": {
            "nodes_total": len(flow_nodes),
            "edges_total": len(flow_edges),
            "visible_default_limit": 20,
            "issues_total": len(visible_issues),
            "known_noise": len([item for item in issues if item.get("issue_kind") == "known_noise"]),
            "flows_total": len(flows.get("items", []) if isinstance(flows.get("items"), list) else []),
        },
        "nodes": flow_nodes,
        "edges": flow_edges,
        "flows": (flows.get("items", []) if isinstance(flows.get("items"), list) else [])[:16],
        "issues": visible_issues[:20],
        "actions": actions,
        "views": [
            {"id": "guide", "label": "Guida", "description": "Focus, problemi e prossime azioni."},
            {"id": "flows", "label": "Flussi", "description": "Catene utente, UI, API, dati e test."},
            {"id": "issues", "label": "Problemi", "description": "Problemi reali e ipotesi scanner ordinate."},
            {"id": "map", "label": "Mappa", "description": "Esplorazione tecnica completa."},
        ],
    }


def render_blueprint_graph(doctor: dict[str, object]) -> str:
    nodes = [item for item in doctor.get("nodes", []) if isinstance(item, dict)][:90]
    if not nodes:
        return "<div class='blueprint-map muted' role='img' aria-label='Blueprint graph'>Nessun collegamento Blueprint da visualizzare.</div>"

    lanes = ["product", "frontend", "backend", "data", "devops", "qa", "docs"]
    lane_index = {name: index for index, name in enumerate(lanes)}
    lane_counts = {name: 0 for name in lanes}
    positioned: list[tuple[dict[str, object], str, int, float, float]] = []
    for index, item in enumerate(nodes):
        domain = str(item.get("domain") or "product")
        lane = domain if domain in lane_index else "product"
        row = lane_counts[lane]
        lane_counts[lane] += 1
        x = 70 + lane_index[lane] * 330
        y = 70 + row * 220
        try:
            x = float(item.get("layout_x"))
            y = float(item.get("layout_y"))
        except (TypeError, ValueError):
            pass
        positioned.append((item, lane, index, x, y))

    node_ids = {str(item.get("id") or index) for item, _, index, _, _ in positioned}
    flow_nodes = []
    flow_edges = []
    drawn: set[tuple[str, str, str]] = set()
    for item, lane, index, x, y in positioned:
        node_id = str(item.get("id") or index)
        relations = [rel for rel in item.get("plain_relations", []) if isinstance(rel, dict)]
        flow_nodes.append(
            {
                "id": node_id,
                "title": str(item.get("title", "")),
                "summary": str(item.get("plain_summary") or item.get("description") or ""),
                "description": str(item.get("description") or ""),
                "domain": lane,
                "layer": str(item.get("layer") or lane),
                "kind": str(item.get("kind") or item.get("type") or "feature"),
                "origin": str(item.get("origin") or "scanner"),
                "gapStatus": str(item.get("gap_status") or "ok"),
                "gapReason": str(item.get("gap_reason") or ""),
                "auditStatus": str(item.get("audit_status") or "debole"),
                "auditProblem": str(item.get("audit_problem") or ""),
                "auditReason": str(item.get("audit_reason") or ""),
                "auditFix": str(item.get("audit_fix") or ""),
                "health": str(item.get("health") or "idea"),
                "nextAction": str(item.get("next_action") or ""),
                "uiRoute": str(item.get("ui_route") or ""),
                "apiRoute": str(item.get("api_route") or ""),
                "httpMethod": str(item.get("http_method") or ""),
                "scannerEvidence": str(item.get("scanner_evidence") or ""),
                "relatedFiles": item.get("related_files") if isinstance(item.get("related_files"), list) else [],
                "contract": item.get("contract") if isinstance(item.get("contract"), dict) else {},
                "x": x,
                "y": y,
                "relations": relations[:6],
            }
        )
        for rel_index, rel in enumerate(relations[:4]):
            related_id = str(rel.get("id") or "")
            relation = str(rel.get("relation") or "parla con")
            edge_key = (node_id, related_id, relation)
            if related_id not in node_ids or related_id == node_id or edge_key in drawn:
                continue
            drawn.add(edge_key)
            confidence = "high" if str(rel.get("confidence") or "") == "high" else "suggested"
            flow_edges.append(
                {
                    "id": f"{node_id}-{related_id}-{rel_index}",
                    "source": node_id,
                    "target": related_id,
                    "label": relation,
                    "relation": relation,
                    "reason": str(rel.get("reason") or ""),
                    "confidence": confidence,
                    "kind": str(rel.get("kind") or "calls"),
                    "evidence": str(rel.get("evidence") or ""),
                    "state": str(rel.get("state") or ("confirmed" if confidence == "high" else "proposed")),
                    "userFeedback": str(rel.get("user_feedback") or ""),
                    "contract": rel.get("contract") if isinstance(rel.get("contract"), dict) else {},
                }
            )

    project_path = str(Path(str(doctor.get("path") or "")).parent) if doctor.get("path") else ""
    payload = {
        "projectPath": project_path,
        "nodes": flow_nodes,
        "edges": flow_edges,
        "blueprintView": build_blueprint_view_model(doctor, flow_nodes, flow_edges),
        "auditPlan": (((doctor.get("audit") or {}) if isinstance(doctor.get("audit"), dict) else {}).get("fix_plan", []) or [])[:10],
        "flows": (((doctor.get("flows") or {}) if isinstance(doctor.get("flows"), dict) else {}).get("items", []) or [])[:16],
        "domains": sorted({str(item.get("domain") or "product") for item in nodes}),
        "layers": sorted({str(item.get("layer") or item.get("domain") or "product") for item in nodes}),
    }
    payload_json = (
        json.dumps(payload, ensure_ascii=True)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
    return (
        "<link rel='stylesheet' href='/reports/blueprint-flow-assets/blueprint-flow.css'>"
        "<section class='blueprint-graph' data-blueprint-flow-root>"
        f"<script type='application/json'>{payload_json}</script>"
        "<div data-blueprint-flow-app>"
        "<div class='blueprint-panel muted'>Lavagna React Flow in caricamento. Se resta cosi, esegui <code>npm run build:blueprint-flow</code>.</div>"
        "</div>"
        "</section>"
        "<script type='module' src='/reports/blueprint-flow-assets/blueprint-flow.js'></script>"
    )


def render_project_selector(projects: list[dict[str, object]], selected: str) -> str:
    rows = []
    normalized_selected = str(Path(selected).resolve()) if selected else ""
    for item in projects:
        path = str(item.get("path", ""))
        active = " si" if path == normalized_selected else ""
        rows.append(
            "<tr>"
            f"<td>{esc(item.get('name', ''))}</td>"
            f"<td>{esc(path)}</td>"
            f"<td>{esc(item.get('sessions', 0))}</td>"
            f"<td>{esc('si' if item.get('is_git') else 'no')}</td>"
            f"<td>{esc('si' if item.get('has_agents') else 'no')}</td>"
            f"<td>{esc('si' if item.get('has_ai_context') else 'no')}</td>"
            f"<td><form method='get' action='/select-project'><input type='hidden' name='path' value='{esc(path)}'><button type='submit'>Monitora{active}</button></form></td>"
            "</tr>"
        )
    body = "".join(rows) or "<tr><td colspan='7'>Nessun progetto rilevato ancora dai log Codex.</td></tr>"
    options = []
    for item in projects:
        path = str(item.get("path", ""))
        name = str(item.get("name", ""))
        selected_attr = " selected" if path == normalized_selected else ""
        label = f"{name} - {path}"
        options.append(f"<option value='{esc(path)}'{selected_attr}>{esc(label)}</option>")
    menu = (
        "<select class='project-menu' name='path'>"
        "<option value=''>Scegli da progetti rilevati...</option>"
        f"{''.join(options)}"
        "</select>"
    )
    table = (
        "<div class='project-table-wrap'><table><thead><tr><th>nome</th><th>path</th><th>sessioni</th><th>git</th><th>AGENTS</th><th>AI_CONTEXT</th><th>azione</th></tr></thead>"
        f"<tbody>{body}</tbody></table></div>"
    )
    return f"<form method='get' action='/select-project' class='project-switcher-form'>{menu}<input type='text' name='path_manual' value='' placeholder='Oppure incolla un percorso nuovo'><button type='submit'>Monitora</button></form>{table}"


def render_expert_feedback(suggested: list[dict[str, object]], feedback: dict[str, object], project: str) -> str:
    stats = {
        str(item.get("expert", "")): item
        for item in feedback.get("experts", [])
        if isinstance(item, dict) and item.get("expert")
    }
    rows = []
    for item in suggested:
        if not isinstance(item, dict):
            continue
        expert = str(item.get("expert", ""))
        current = stats.get(expert, {})
        rows.append(
            "<tr>"
            f"<td>{esc(expert)}</td>"
            f"<td>{esc(item.get('reason', ''))}</td>"
            f"<td>{esc(current.get('used', 0))}</td>"
            f"<td>{esc(current.get('ignored', 0))}</td>"
            f"<td>{esc(current.get('score', 0))}</td>"
            "<td>"
            f"<form method='get' action='/expert-feedback'><input type='hidden' name='project' value='{esc(project)}'>"
            f"<input type='hidden' name='expert' value='{esc(expert)}'><input type='hidden' name='outcome' value='used'>"
            "<button type='submit'>Usato</button></form> "
            f"<form method='get' action='/expert-feedback'><input type='hidden' name='project' value='{esc(project)}'>"
            f"<input type='hidden' name='expert' value='{esc(expert)}'><input type='hidden' name='outcome' value='ignored'>"
            "<button type='submit'>Ignorato</button></form>"
            "</td>"
            "</tr>"
        )
    body = "".join(rows) or "<tr><td colspan='6'>Nessun esperto suggerito ancora.</td></tr>"
    return (
        "<table><thead><tr><th>esperto</th><th>motivo</th><th>usato</th><th>ignorato</th><th>score</th><th>feedback</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )
