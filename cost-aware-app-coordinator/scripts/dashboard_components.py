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


def render_blueprint_graph(doctor: dict[str, object]) -> str:
    nodes = [item for item in doctor.get("nodes", []) if isinstance(item, dict)][:90]
    if not nodes:
        return "<div class='blueprint-map muted' role='img' aria-label='Blueprint graph'>Nessun collegamento Blueprint da visualizzare.</div>"
    lanes = ["frontend", "product", "backend", "data", "qa", "devops", "docs"]
    lane_index = {name: index for index, name in enumerate(lanes)}
    positioned = []
    lane_counts = {name: 0 for name in lanes}
    for index, item in enumerate(nodes):
        lane_value = str(item.get("layer") or item.get("domain") or "product")
        lane = lane_value if lane_value in lane_index else "product"
        row = lane_counts[lane]
        lane_counts[lane] += 1
        positioned.append((item, lane, lane_index[lane], row, index))
    width = 1540
    max_row = max((row for _, _, _, row, _ in positioned), default=0)
    height = max(480, 120 + max_row * 140)
    box_w = 210
    box_h = 104
    gap_x = 215
    start_x = 28
    start_y = 78
    coords = {}
    lane_labels = []
    for lane in lanes:
        x = start_x + lane_index[lane] * gap_x
        lane_labels.append(f"<text x='{x}' y='28' class='map-meta'>{esc(lane)}</text>")
    boxes = []
    for item, lane, col, row, index in positioned:
        x = start_x + col * gap_x
        y = start_y + row * 140
        try:
            x = float(item.get("layout_x"))
            y = float(item.get("layout_y"))
        except (TypeError, ValueError):
            pass
        node_id = str(item.get("id") or index)
        coords[node_id] = (x, y)
        health = str(item.get("health") or "idea")
        full_lines = wrap_text(item.get("plain_summary") or item.get("description"), 50, 4)
        relation_lines = [
            f"{rel.get('relation', 'parla con')} {rel.get('title', '')}: {rel.get('reason', '')}"
            for rel in item.get("plain_relations", [])
            if isinstance(rel, dict)
        ][:2]
        relation_ids = [
            str(rel.get("id") or "")
            for rel in item.get("plain_relations", [])
            if isinstance(rel, dict) and rel.get("id")
        ][:6]
        popover_lines = full_lines + wrap_text(" ".join(relation_lines), 54, 3)
        pop_w = 360
        pop_h = 54 + len(popover_lines) * 18
        pop_x = max(8, min(x, width - pop_w - 8))
        pop_y = y + box_h + 10 if y < 180 else max(42, y - pop_h - 10)
        boxes.append(
            f"<g class='map-node {esc(health)}' tabindex='0' data-node-id='{esc(node_id)}' data-node-title='{esc(item.get('title', ''))}' data-domain='{esc(lane)}' data-base-x='{x}' data-base-y='{y}' data-x='{x}' data-y='{y}' data-search='{esc(str(item.get('title', '')) + ' ' + str(item.get('plain_summary', '')) + ' ' + str(item.get('description', '')))}' data-summary='{esc(item.get('plain_summary') or item.get('description', ''))}' data-relations='{esc('|'.join(relation_ids))}'>"
            f"<title>{esc(item.get('plain_summary') or item.get('description', ''))}</title>"
            f"<rect class='map-box' x='{x}' y='{y}' width='{box_w}' height='{box_h}' />"
            f"<text x='{x + 12}' y='{y + 24}' class='map-title'>{esc(short_text(item.get('title'), 28))}</text>"
            f"<text x='{x + 12}' y='{y + 46}' class='map-meta'>{esc(health)} / {esc(lane)}</text>"
            f"<text x='{x + 12}' y='{y + 68}' class='map-meta'>{esc(short_text(item.get('plain_summary') or item.get('description'), 34))}</text>"
            f"<text x='{x + 12}' y='{y + 88}' class='map-meta'>Passa sopra per leggere tutto</text>"
            f"<g class='map-popover'>"
            f"<rect x='{pop_x}' y='{pop_y}' width='{pop_w}' height='{pop_h}' />"
            f"<text x='{pop_x + 14}' y='{pop_y + 24}' class='map-popover-title'>{esc(short_text(item.get('title'), 38))}</text>"
            f"<text x='{pop_x + 14}' y='{pop_y + 44}' class='map-popover-muted'>{esc(health)} / {esc(lane)}</text>"
            + "".join(
                f"<text x='{pop_x + 14}' y='{pop_y + 68 + line_index * 18}' class='map-popover-text'>{esc(line)}</text>"
                for line_index, line in enumerate(popover_lines)
            )
            + "</g>"
            "</g>"
        )
    lines = []
    relation_labels = []
    drawn: set[tuple[str, str]] = set()
    for item, lane, col, row, index in positioned:
        target_id = str(item.get("id") or index)
        relations = [rel for rel in item.get("plain_relations", []) if isinstance(rel, dict)]
        for rel in relations[:2]:
            related_id = str(rel.get("id") or "")
            source = coords.get(target_id)
            target = coords.get(related_id)
            if not source or not target or related_id == target_id or (target_id, related_id) in drawn:
                continue
            drawn.add((target_id, related_id))
            sx, sy = source
            tx, ty = target
            lines.append(f"<path class='map-line' data-source='{esc(target_id)}' data-target='{esc(related_id)}' d='M {sx + box_w} {sy + box_h / 2} C {sx + box_w + 35} {sy + box_h / 2}, {tx - 35} {ty + box_h / 2}, {tx} {ty + box_h / 2}' />")
            label_x = int((sx + tx + box_w) / 2)
            label_y = int((sy + ty + box_h) / 2) - 8
            relation_labels.append(f"<text x='{label_x}' y='{label_y}' class='map-meta map-label' data-source='{esc(target_id)}' data-target='{esc(related_id)}'>{esc(short_text(rel.get('relation', 'parla con'), 16))}</text>")
    domains = sorted({str(item.get("domain") or "product") for item in nodes})
    filters = "".join(f"<button type='button' class='domain-filter' data-domain-filter='{esc(domain)}'>{esc(domain)}</button>" for domain in domains)
    project_path = str(Path(str(doctor.get("path") or "")).parent) if doctor.get("path") else ""
    script = """
<script>
(function () {
  const root = document.currentScript.previousElementSibling;
  if (!root) return;
  const projectPath = __PROJECT_PATH__;
  const search = root.querySelector('[data-blueprint-search]');
  const detail = root.querySelector('[data-blueprint-detail]');
  const buttons = Array.from(root.querySelectorAll('[data-domain-filter]'));
  const lineToggle = root.querySelector('[data-toggle-lines]');
  const saveLayout = root.querySelector('[data-save-layout]');
  const zoomIn = root.querySelector('[data-zoom-in]');
  const zoomOut = root.querySelector('[data-zoom-out]');
  const zoomReset = root.querySelector('[data-zoom-reset]');
  const map = root.querySelector('.blueprint-map');
  const svg = root.querySelector('svg');
  const nodes = Array.from(root.querySelectorAll('.map-node'));
  const lines = Array.from(root.querySelectorAll('.map-line'));
  const labels = Array.from(root.querySelectorAll('.map-label'));
  const cards = Array.from(document.querySelectorAll('[data-node-card]'));
  let activeDomain = '';
  const baseView = svg.viewBox.baseVal;
  const viewBox = {
    x: baseView.x || 0,
    y: baseView.y || 0,
    w: baseView.width || 1540,
    h: baseView.height || 480
  };
  const originalViewBox = { ...viewBox };
  let scale = 1;
  let drag = null;
  const pointers = new Map();

  function html(value) {
    return String(value || '').replace(/[&<>"']/g, char => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    })[char]);
  }

  function relationIds(node) {
    return String(node.dataset.relations || '').split('|').filter(Boolean);
  }

  function svgPoint(event) {
    const point = svg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;
    const ctm = svg.getScreenCTM();
    return ctm ? point.matrixTransform(ctm.inverse()) : { x: 0, y: 0 };
  }

  function applyViewport() {
    svg.setAttribute('viewBox', `${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`);
  }

  function setNodePosition(node, x, y) {
    const baseX = Number(node.dataset.baseX || 0);
    const baseY = Number(node.dataset.baseY || 0);
    node.dataset.x = String(Math.round(x * 100) / 100);
    node.dataset.y = String(Math.round(y * 100) / 100);
    node.setAttribute('transform', `translate(${x - baseX},${y - baseY})`);
  }

  function nodeCenter(id) {
    const node = root.querySelector(`[data-node-id="${CSS.escape(id)}"]`);
    if (!node) return null;
    return { x: Number(node.dataset.x || 0) + 105, y: Number(node.dataset.y || 0) + 52 };
  }

  function updateLines() {
    lines.forEach(line => {
      const source = nodeCenter(line.dataset.source || '');
      const target = nodeCenter(line.dataset.target || '');
      if (!source || !target) return;
      line.setAttribute('d', `M ${source.x} ${source.y} C ${source.x + 45} ${source.y}, ${target.x - 45} ${target.y}, ${target.x} ${target.y}`);
    });
    labels.forEach(label => {
      const source = nodeCenter(label.dataset.source || '');
      const target = nodeCenter(label.dataset.target || '');
      if (!source || !target) return;
      label.setAttribute('x', String(Math.round((source.x + target.x) / 2)));
      label.setAttribute('y', String(Math.round((source.y + target.y) / 2 - 8)));
    });
  }

  function setDetail(node) {
    const related = relationIds(node);
    const relatedTitles = related.map(id => {
      const item = root.querySelector(`[data-node-id="${CSS.escape(id)}"]`);
      return item ? item.dataset.nodeTitle : id;
    });
    detail.innerHTML = `<div class="blueprint-detail-title">${html(node.dataset.nodeTitle || 'Nodo')}</div>` +
      `<div class="blueprint-detail-body">${html(node.dataset.summary || '')}</div>` +
      (relatedTitles.length ? `<ul class="blueprint-detail-links">${relatedTitles.map(title => `<li>${html(title)}</li>`).join('')}</ul>` : '');
  }

  function highlightNode(node, filterCards) {
    const id = node.dataset.nodeId;
    const related = new Set(relationIds(node));
    nodes.forEach(item => {
      const itemId = item.dataset.nodeId;
      item.classList.toggle('is-selected', item === node);
      item.classList.toggle('is-related', related.has(itemId));
      item.classList.toggle('is-dim', item !== node && !related.has(itemId));
    });
    [...lines, ...labels].forEach(item => {
      const strong = item.dataset.source === id || item.dataset.target === id;
      item.classList.toggle('is-strong', strong);
      item.classList.toggle('is-dim', !strong);
    });
    if (filterCards) {
      cards.forEach(card => card.classList.toggle('is-visible', card.dataset.nodeCard === id || related.has(card.dataset.nodeCard)));
      const cardRoot = document.querySelector('[data-blueprint-cards]');
      if (cardRoot) cardRoot.classList.add('is-filtered');
    }
    setDetail(node);
  }

  function clearHighlight() {
    nodes.forEach(item => item.classList.remove('is-selected', 'is-related', 'is-dim'));
    [...lines, ...labels].forEach(item => item.classList.remove('is-strong', 'is-dim'));
  }

  function applyFilter() {
    const term = (search ? search.value : '').trim().toLowerCase();
    let visible = 0;
    nodes.forEach(node => {
      const text = String(node.dataset.search || '').toLowerCase();
      const matches = (!term || text.includes(term)) && (!activeDomain || node.dataset.domain === activeDomain);
      node.classList.toggle('is-hidden', !matches);
      if (matches) visible += 1;
    });
    lines.forEach(line => {
      const source = root.querySelector(`[data-node-id="${CSS.escape(line.dataset.source || '')}"]`);
      const target = root.querySelector(`[data-node-id="${CSS.escape(line.dataset.target || '')}"]`);
      line.classList.toggle('is-hidden', !source || !target || source.classList.contains('is-hidden') || target.classList.contains('is-hidden'));
    });
    labels.forEach(label => {
      const source = root.querySelector(`[data-node-id="${CSS.escape(label.dataset.source || '')}"]`);
      const target = root.querySelector(`[data-node-id="${CSS.escape(label.dataset.target || '')}"]`);
      label.classList.toggle('is-hidden', !source || !target || source.classList.contains('is-hidden') || target.classList.contains('is-hidden'));
    });
    const cardRoot = document.querySelector('[data-blueprint-cards]');
    cards.forEach(card => {
      const text = String(card.dataset.search || '').toLowerCase();
      const matches = (!term || text.includes(term)) && (!activeDomain || card.dataset.domain === activeDomain);
      card.classList.toggle('is-visible', matches);
    });
    if (cardRoot) cardRoot.classList.toggle('is-filtered', Boolean(term || activeDomain));
    detail.innerHTML = `<div class="blueprint-detail-title">${visible} nodi visibili</div><div class="blueprint-detail-body">Seleziona un nodo per vedere descrizione completa e collegamenti.</div>`;
  }

  nodes.forEach(node => {
    node.addEventListener('mouseenter', () => highlightNode(node, false));
    node.addEventListener('mouseleave', clearHighlight);
    node.addEventListener('click', () => highlightNode(node, true));
    node.addEventListener('pointerdown', event => {
      event.preventDefault();
      event.stopPropagation();
      pointers.set(event.pointerId, { clientX: event.clientX, clientY: event.clientY });
      node.setPointerCapture(event.pointerId);
      const point = svgPoint(event);
      drag = {
        mode: 'node',
        node,
        offsetX: point.x - Number(node.dataset.x || 0),
        offsetY: point.y - Number(node.dataset.y || 0)
      };
    });
    node.addEventListener('pointerup', event => { pointers.delete(event.pointerId); drag = null; });
    node.addEventListener('pointercancel', event => { pointers.delete(event.pointerId); drag = null; });
    node.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        highlightNode(node, true);
      }
    });
  });
  if (map) {
    map.addEventListener('pointerdown', event => {
      pointers.set(event.pointerId, { clientX: event.clientX, clientY: event.clientY });
      if (pointers.size >= 2) {
        const info = pinchInfo();
        if (info) drag = { mode: 'pinch', startDistance: info.distance, startScale: scale, centerX: info.centerX, centerY: info.centerY };
        return;
      }
      if (event.target.closest && event.target.closest('.map-node')) return;
      drag = { mode: 'pan', startClientX: event.clientX, startClientY: event.clientY, startX: viewBox.x, startY: viewBox.y };
      map.setPointerCapture(event.pointerId);
    });
    map.addEventListener('pointermove', event => {
      if (pointers.has(event.pointerId)) pointers.set(event.pointerId, { clientX: event.clientX, clientY: event.clientY });
      if (!drag) return;
      if (drag.mode === 'node') {
        const point = svgPoint(event);
        setNodePosition(drag.node, point.x - drag.offsetX, point.y - drag.offsetY);
        updateLines();
      } else if (drag.mode === 'pan') {
        const rect = svg.getBoundingClientRect();
        viewBox.x = drag.startX - ((event.clientX - drag.startClientX) * viewBox.w / rect.width);
        viewBox.y = drag.startY - ((event.clientY - drag.startClientY) * viewBox.h / rect.height);
        applyViewport();
      } else if (drag.mode === 'pinch') {
        const info = pinchInfo();
        if (info) zoomAtClient(drag.startScale * (info.distance / drag.startDistance), info.centerX, info.centerY);
      }
    });
    map.addEventListener('pointerup', event => { pointers.delete(event.pointerId); drag = null; });
    map.addEventListener('pointercancel', event => { pointers.delete(event.pointerId); drag = null; });
  }
  if (search) search.addEventListener('input', applyFilter);
  function setZoom(next, anchor) {
    const before = anchor || { x: viewBox.x + viewBox.w / 2, y: viewBox.y + viewBox.h / 2 };
    scale = Math.max(0.35, Math.min(3, next));
    viewBox.w = originalViewBox.w / scale;
    viewBox.h = originalViewBox.h / scale;
    viewBox.x = before.x - viewBox.w / 2;
    viewBox.y = before.y - viewBox.h / 2;
    applyViewport();
  }

  function pinchInfo() {
    const values = Array.from(pointers.values());
    if (values.length < 2) return null;
    const a = values[0];
    const b = values[1];
    const dx = b.clientX - a.clientX;
    const dy = b.clientY - a.clientY;
    return {
      distance: Math.max(1, Math.hypot(dx, dy)),
      centerX: (a.clientX + b.clientX) / 2,
      centerY: (a.clientY + b.clientY) / 2
    };
  }

  function zoomAtClient(next, clientX, clientY) {
    setZoom(next, svgPoint({ clientX, clientY }));
  }
  if (zoomIn) zoomIn.addEventListener('click', () => setZoom(scale + 0.15));
  if (zoomOut) zoomOut.addEventListener('click', () => setZoom(scale - 0.15));
  if (zoomReset) zoomReset.addEventListener('click', () => {
    scale = 1;
    viewBox.x = originalViewBox.x;
    viewBox.y = originalViewBox.y;
    viewBox.w = originalViewBox.w;
    viewBox.h = originalViewBox.h;
    applyViewport();
  });
  if (map) map.addEventListener('wheel', event => {
    event.preventDefault();
    const anchor = svgPoint(event);
    const next = scale + (event.deltaY < 0 ? 0.15 : -0.15);
    setZoom(next, anchor);
  }, { passive: false });
  if (saveLayout) saveLayout.addEventListener('click', async () => {
    const positions = {};
    nodes.forEach(node => {
      positions[node.dataset.nodeId] = { x: Number(node.dataset.x || 0), y: Number(node.dataset.y || 0) };
    });
    saveLayout.textContent = 'Salvo...';
    try {
      const response = await fetch('/blueprint-layout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project: projectPath, positions })
      });
      const payload = await response.json();
      saveLayout.textContent = payload.ok ? `Salvato (${payload.saved})` : 'Errore salvataggio';
    } catch (error) {
      saveLayout.textContent = 'Errore salvataggio';
    }
    setTimeout(() => { saveLayout.textContent = 'Salva layout'; }, 1800);
  });
  if (lineToggle) lineToggle.addEventListener('click', () => {
    const enabled = !root.classList.contains('show-all-lines');
    root.classList.toggle('show-all-lines', enabled);
    lineToggle.textContent = enabled ? 'Nascondi linee' : 'Mostra linee';
  });
  buttons.forEach(button => button.addEventListener('click', () => {
    activeDomain = activeDomain === button.dataset.domainFilter ? '' : button.dataset.domainFilter;
    buttons.forEach(item => item.classList.toggle('is-active', item.dataset.domainFilter === activeDomain));
    applyFilter();
  }));
  updateLines();
  applyViewport();
  applyFilter();
})();
</script>
""".replace("__PROJECT_PATH__", json.dumps(project_path))
    graph = (
        "<section class='blueprint-graph' data-blueprint-graph>"
        "<div class='blueprint-tools'>"
        "<input class='blueprint-search' data-blueprint-search type='text' placeholder='Cerca nodo, file o funzione'>"
        "<button type='button' data-zoom-in>Zoom +</button>"
        "<button type='button' data-zoom-out>Zoom -</button>"
        "<button type='button' data-zoom-reset>Reset vista</button>"
        "<button type='button' data-toggle-lines>Mostra linee</button>"
        "<button type='button' data-save-layout>Salva layout</button>"
        + filters
        + "</div>"
        "<div class='blueprint-detail' data-blueprint-detail></div>"
        "<div class='blueprint-map'>"
        f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='Blueprint graph'>"
        "<defs><marker id='arrow' markerWidth='8' markerHeight='8' refX='6' refY='3' orient='auto'><path d='M0,0 L0,6 L7,3 z' fill='#93a4b8'/></marker></defs>"
        "<g data-map-viewport>"
        + "".join(lane_labels)
        + "".join(lines)
        + "".join(relation_labels)
        + "".join(boxes)
        + "</g></svg></div></section>"
    )
    return graph + script


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
