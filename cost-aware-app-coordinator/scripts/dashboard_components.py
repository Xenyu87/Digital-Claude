#!/usr/bin/env python3
"""Small HTML helpers for the local dashboard."""

from __future__ import annotations

import html
from pathlib import Path


DASHBOARD_CSS = """
    :root { color-scheme: light; --ink:#182330; --muted:#5c6876; --line:#d9e0e8; --panel:#f6f8fb; --soft:#edf4f7; --ok:#1f7a4d; --bad:#b42318; --accent:#2563a8; --accent-soft:#e8f1fb; --warm:#8a5a16; --warm-soft:#fff4df; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Inter, Segoe UI, Arial, sans-serif; color:var(--ink); background:#f8fafc; }
    header { padding:26px 32px 18px; border-bottom:1px solid var(--line); background:#ffffff; }
    main { padding:24px 32px 42px; max-width:1220px; }
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
    .quick-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
    .quick-card { border:1px solid var(--line); border-radius:8px; background:#fff; padding:14px; min-height:96px; }
    .quick-card strong { display:block; font-size:22px; margin-top:6px; }
    .blueprint-panel { border:1px solid #cbd8e6; border-radius:8px; background:#fff; padding:16px; margin:8px 0 14px; }
    .blueprint-focus { display:grid; grid-template-columns:minmax(0,1.3fr) minmax(240px,.7fr); gap:12px; align-items:stretch; }
    .blueprint-title { font-size:22px; font-weight:800; line-height:1.15; overflow-wrap:anywhere; }
    .blueprint-lane { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:10px; margin-top:12px; }
    .blueprint-map { width:100%; min-height:420px; border:1px solid var(--line); border-radius:8px; background:#fbfcfe; margin-top:14px; overflow:auto; }
    .blueprint-map svg { min-width:920px; display:block; }
    .map-line { stroke:#93a4b8; stroke-width:2; fill:none; marker-end:url(#arrow); }
    .map-node rect { fill:#fff; stroke:#cbd8e6; stroke-width:1.4; rx:8; }
    .map-node.covered rect { stroke:var(--ok); }
    .map-node.partial rect { stroke:var(--warm); }
    .map-node.missing rect { stroke:var(--bad); }
    .map-title { font-size:13px; font-weight:800; fill:var(--ink); }
    .map-meta { font-size:11px; fill:var(--muted); }
    .node-card { border:1px solid var(--line); border-left:5px solid var(--accent); border-radius:8px; background:#fff; padding:12px; min-height:128px; }
    .node-card.covered { border-left-color:var(--ok); }
    .node-card.partial { border-left-color:var(--warm); }
    .node-card.idea { border-left-color:var(--accent); }
    .node-card.missing { border-left-color:var(--bad); }
    .node-name { font-weight:800; margin:6px 0; overflow-wrap:anywhere; }
    .node-desc { color:var(--muted); line-height:1.35; margin:6px 0 8px; }
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
    table { width:100%; border-collapse:collapse; font-size:13px; background:#fff; border:1px solid var(--line); border-radius:8px; overflow:hidden; }
    th, td { border-bottom:1px solid var(--line); padding:9px; text-align:left; vertical-align:top; }
    th { background:#eef3f7; color:#334155; }
    pre { white-space:pre-wrap; border:1px solid var(--line); background:#fbfcfe; border-radius:8px; padding:12px; overflow:auto; }
    details { border:1px solid var(--line); border-radius:8px; padding:12px 14px; margin:12px 0; background:#fff; }
    summary { cursor:pointer; font-weight:800; }
    .detail-band { background:#fff; border:1px solid var(--line); border-radius:8px; padding:14px; margin-top:14px; }
    form { margin:0; display:inline; }
    input[type=text] { width:min(720px, 100%); padding:10px; border:1px solid var(--line); border-radius:6px; font:inherit; background:#fff; }
    button { padding:8px 11px; border:1px solid var(--accent); border-radius:6px; background:#fff; color:var(--accent); font-weight:700; cursor:pointer; }
    button:hover { background:var(--accent-soft); }
    @media (max-width: 820px) { body { background:#fff; } header, main { padding-left:18px; padding-right:18px; } .simple-view, .blueprint-focus { grid-template-columns:1fr; } .hero-action { font-size:24px; } .quick-grid { grid-template-columns:1fr; } }
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
    nodes = [item for item in doctor.get("nodes", []) if isinstance(item, dict)][:24]
    if not nodes:
        return "<div class='blueprint-panel muted'>Nessun nodo Blueprint da visualizzare. <strong>Prossimo passo:</strong> seleziona un progetto o usa Scansiona nodi.</div>"
    cards = []
    for item in nodes:
        health = str(item.get("health", "idea"))
        chip_class = {"covered": "ok", "partial": "warn", "missing": "bad"}.get(health, "")
        cards.append(
            f"<article class='node-card {esc(health)}'>"
            f"<div class='chip-row'><span class='chip {chip_class}'>{esc(health)}</span><span class='chip'>{esc(item.get('domain', 'n/d'))}</span></div>"
            f"<div class='node-name'>{esc(item.get('title', ''))}</div>"
            f"<div class='node-desc'>{esc(item.get('description', ''))}</div>"
            f"<div class='muted'><strong>Prossimo passo:</strong> {esc(item.get('next_action', ''))}</div>"
            "</article>"
        )
    return "<div class='blueprint-lane'>" + "".join(cards) + "</div>"


def short_text(value: object, limit: int = 52) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "..."


def render_blueprint_graph(doctor: dict[str, object]) -> str:
    nodes = [item for item in doctor.get("nodes", []) if isinstance(item, dict)][:24]
    if not nodes:
        return "<div class='blueprint-map muted' role='img' aria-label='Blueprint graph'>Nessun collegamento Blueprint da visualizzare.</div>"
    lanes = ["product", "frontend", "backend", "data", "devops", "qa", "docs"]
    lane_index = {name: index for index, name in enumerate(lanes)}
    positioned = []
    lane_counts = {name: 0 for name in lanes}
    for index, item in enumerate(nodes):
        domain = str(item.get("domain") or "product")
        lane = domain if domain in lane_index else "product"
        row = lane_counts[lane]
        lane_counts[lane] += 1
        positioned.append((item, lane, lane_index[lane], row, index))
    width = 1180
    height = max(420, 110 + max((row for _, _, _, row, _ in positioned), default=0) * 112)
    box_w = 150
    box_h = 78
    gap_x = 160
    start_x = 28
    start_y = 72
    coords = {}
    lane_labels = []
    for lane in lanes:
        x = start_x + lane_index[lane] * gap_x
        lane_labels.append(f"<text x='{x}' y='28' class='map-meta'>{esc(lane)}</text>")
    boxes = []
    for item, lane, col, row, index in positioned:
        x = start_x + col * gap_x
        y = start_y + row * 112
        node_id = str(item.get("id") or index)
        coords[node_id] = (x, y)
        health = str(item.get("health") or "idea")
        boxes.append(
            f"<g class='map-node {esc(health)}'>"
            f"<rect x='{x}' y='{y}' width='{box_w}' height='{box_h}' />"
            f"<text x='{x + 10}' y='{y + 20}' class='map-title'>{esc(short_text(item.get('title'), 22))}</text>"
            f"<text x='{x + 10}' y='{y + 40}' class='map-meta'>{esc(health)} / {esc(lane)}</text>"
            f"<text x='{x + 10}' y='{y + 60}' class='map-meta'>{esc(short_text(item.get('description'), 26))}</text>"
            "</g>"
        )
    lines = []
    for item, lane, col, row, index in positioned:
        if index == 0:
            continue
        target_id = str(item.get("id") or index)
        parent_id = str(item.get("parent_id") or "")
        source = coords.get(parent_id)
        if source is None:
            previous_same_lane = None
            for prev_item, prev_lane, _, _, prev_index in positioned:
                if prev_index >= index:
                    break
                if prev_lane == lane:
                    previous_same_lane = str(prev_item.get("id") or prev_index)
            source = coords.get(previous_same_lane or str(positioned[0][0].get("id") or 0))
        target = coords.get(target_id)
        if source and target:
            sx, sy = source
            tx, ty = target
            lines.append(f"<path class='map-line' d='M {sx + box_w} {sy + box_h / 2} C {sx + box_w + 35} {sy + box_h / 2}, {tx - 35} {ty + box_h / 2}, {tx} {ty + box_h / 2}' />")
    return (
        "<div class='blueprint-map'>"
        f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='Blueprint graph'>"
        "<defs><marker id='arrow' markerWidth='8' markerHeight='8' refX='6' refY='3' orient='auto'><path d='M0,0 L0,6 L7,3 z' fill='#93a4b8'/></marker></defs>"
        + "".join(lane_labels)
        + "".join(lines)
        + "".join(boxes)
        + "</svg></div>"
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
    return (
        "<table><thead><tr><th>nome</th><th>path</th><th>sessioni</th><th>git</th><th>AGENTS</th><th>AI_CONTEXT</th><th>azione</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


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
