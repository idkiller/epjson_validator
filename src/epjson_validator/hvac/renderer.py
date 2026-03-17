"""Render HVAC diagrams as text or HTML."""

from __future__ import annotations

from html import escape

from epjson_validator.hvac.models import HVACDiagram, HVACNode

_COLOR_BY_KIND = {
    "loop": "#264653",
    "side": "#2a9d8f",
    "branch": "#e9c46a",
    "zone": "#457b9d",
    "list": "#8d99ae",
    "component": "#f4a261",
}

_TYPE_BASE_COLORS = (
    "#3b82f6",
    "#14b8a6",
    "#8b5cf6",
    "#f97316",
    "#ef4444",
    "#84cc16",
    "#06b6d4",
    "#eab308",
)


def render_diagrams_text(diagrams_by_kind: dict[str, list[HVACDiagram]], selected_kind: str) -> str:
    lines: list[str] = []
    for kind in _selected_kinds(selected_kind):
        diagrams = diagrams_by_kind.get(kind, [])
        if not diagrams:
            continue
        title = {
            "air": "AIR LOOP GRAPHS",
            "plant": "PLANT LOOP GRAPHS",
            "zone": "ZONE EQUIPMENT GRAPHS",
        }[kind]
        if lines:
            lines.append("")
        lines.append(title)
        for diagram in diagrams:
            lines.append(f"- {diagram.name}")
            for path in diagram.paths:
                labels = [diagram.nodes[node_id].label for node_id in path.node_ids if node_id in diagram.nodes]
                lines.append(f"  {path.label}: {' -> '.join(labels)}")
    return "\n".join(lines)


def render_diagrams_html(diagrams_by_kind: dict[str, list[HVACDiagram]], selected_kind: str) -> str:
    diagrams = [diagram for kind in _selected_kinds(selected_kind) for diagram in diagrams_by_kind.get(kind, [])]
    type_colors = _type_color_map(diagrams)
    text = render_diagrams_text(diagrams_by_kind, selected_kind)
    graph_parts: list[str] = []
    for diagram in diagrams:
        graph_parts.append(f'<section class="diagram"><h3>{escape(_diagram_title(diagram))}</h3>')
        legend_items = _diagram_legend_items(diagram, type_colors)
        if legend_items:
            graph_parts.append('<ul class="legend">')
            for label, color in legend_items:
                graph_parts.append(
                    '<li>'
                    f'<span class="swatch" style="--node-color:{color}"></span>'
                    f'<span>{escape(_truncate(label, 60))}</span>'
                    '</li>'
                )
            graph_parts.append("</ul>")
        for path in diagram.paths:
            graph_parts.append(f'<div class="path"><div class="path-label">{escape(path.label)}</div><div class="nodes">')
            for index, node_id in enumerate(path.node_ids):
                node = diagram.nodes[node_id]
                color = type_colors.get(_node_type_key(node), _COLOR_BY_KIND.get(node.kind, "#f4a261"))
                graph_parts.append(f'<span class="node" style="--node-color:{color}">{escape(node.label)}</span>')
                if index < len(path.node_ids) - 1:
                    graph_parts.append('<span class="arrow">→</span>')
            graph_parts.append("</div></div>")
        graph_parts.append("</section>")

    return (
        "<!DOCTYPE html>"
        '<html lang="en"><head><meta charset="utf-8"/>'
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>'
        "<title>HVAC Connectivity</title>"
        "<style>"
        "body{margin:0;background:#f3efe8;color:#1f2933;font-family:Segoe UI,Arial,sans-serif;}"
        ".page{max-width:1680px;margin:0 auto;padding:24px;}"
        "h1{margin:0 0 8px;font-size:28px;}"
        "p{margin:0 0 20px;color:#52606d;}"
        ".panel{background:#fffdf9;border:1px solid #e6dfd3;border-radius:16px;padding:18px 20px;"
        "box-shadow:0 10px 30px rgba(31,41,51,.06);margin-bottom:20px;overflow:auto;}"
        "pre{margin:0;font:13px/1.5 Consolas,Monaco,monospace;white-space:pre-wrap;}"
        ".diagram{padding:14px 0;border-bottom:1px dashed #d9d2c6;}"
        ".diagram:last-child{border-bottom:none;}"
        "h3{margin:0 0 10px;font-size:18px;}"
        ".legend{list-style:none;display:flex;flex-wrap:wrap;gap:8px 16px;padding:0;margin:0 0 12px;}"
        ".legend li{display:flex;align-items:center;gap:7px;font-size:12px;color:#334e68;}"
        ".swatch{width:16px;height:16px;border-radius:4px;background:color-mix(in srgb, var(--node-color), white 65%);"
        "border:1.5px solid var(--node-color);display:inline-block;}"
        ".path{display:grid;grid-template-columns:minmax(170px,220px) 1fr;gap:10px;align-items:start;margin-bottom:12px;}"
        ".path-label{font-size:12px;font-weight:600;color:#334e68;padding-top:8px;}"
        ".nodes{display:flex;flex-wrap:wrap;gap:8px;align-items:center;}"
        ".node{border-radius:8px;padding:8px 10px;font-size:12px;font-weight:600;border:1.5px solid var(--node-color);"
        "background:color-mix(in srgb, var(--node-color), white 82%);}"
        ".arrow{color:#52606d;font-weight:700;}"
        "</style></head><body><div class=\"page\">"
        "<h1>HVAC Connectivity</h1>"
        "<p>Generated from epJSON. Includes text summary and simple diagram rendering.</p>"
        f'<section class="panel">{"".join(graph_parts)}</section>'
        f'<section class="panel"><pre>{escape(text)}</pre></section>'
        "</div></body></html>"
    )


def _selected_kinds(selected_kind: str) -> tuple[str, ...]:
    if selected_kind == "all":
        return ("air", "plant", "zone")
    return (selected_kind,)


def _diagram_title(diagram: HVACDiagram) -> str:
    prefix = {
        "air": "Air Loop",
        "plant": "Plant Loop",
        "zone": "Zone Equipment",
    }.get(diagram.kind, "HVAC")
    return f"{prefix}: {diagram.name}"


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def _type_color_map(diagrams: list[HVACDiagram]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for diagram in diagrams:
        for path in diagram.paths:
            for node_id in path.node_ids:
                node = diagram.nodes.get(node_id)
                if node is None:
                    continue
                type_key = _node_type_key(node)
                if type_key in labels:
                    continue
                color = _TYPE_BASE_COLORS[len(labels) % len(_TYPE_BASE_COLORS)]
                labels[type_key] = color
    return labels


def _node_type_key(node: HVACNode) -> str:
    return node.node_type or node.kind


def _diagram_legend_items(diagram: HVACDiagram, type_colors: dict[str, str]) -> list[tuple[str, str]]:
    labels: list[tuple[str, str]] = []
    seen: set[str] = set()
    for path in diagram.paths:
        for node_id in path.node_ids:
            node = diagram.nodes.get(node_id)
            if node is None:
                continue
            type_key = _node_type_key(node)
            if type_key in seen:
                continue
            seen.add(type_key)
            labels.append((type_key, type_colors.get(type_key, _COLOR_BY_KIND.get(node.kind, "#f4a261"))))
    return labels
