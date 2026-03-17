"""Render HVAC diagrams as text, SVG, or HTML."""

from __future__ import annotations

from html import escape

from epjson_validator.hvac.models import HVACDiagram

_COLOR_BY_KIND = {
    "loop": "#264653",
    "side": "#2a9d8f",
    "branch": "#e9c46a",
    "zone": "#457b9d",
    "list": "#8d99ae",
    "component": "#f4a261",
}

_LEGEND_COLORS = (
    "#d62828",
    "#277da1",
    "#6a4c93",
    "#2a9d8f",
    "#f4a261",
    "#e76f51",
    "#4361ee",
    "#ff006e",
    "#3a5a40",
    "#bc6c25",
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


def render_diagrams_svg(diagrams_by_kind: dict[str, list[HVACDiagram]], selected_kind: str) -> str:
    diagrams = [diagram for kind in _selected_kinds(selected_kind) for diagram in diagrams_by_kind.get(kind, [])]
    width = 1600
    title_height = 28
    row_height = 90
    graph_margin = 36
    node_width = 170
    node_height = 42
    x_step = 210
    left_margin = 220
    legend_item_height = 26

    label_colors = _label_color_map(diagrams)
    legend_labels = list(label_colors)
    legend_rows = (len(legend_labels) + 2) // 3
    legend_height = 24 + legend_rows * legend_item_height if legend_labels else 0

    total_rows = sum(max(len(diagram.paths), 1) for diagram in diagrams)
    total_height = 40 + legend_height + len(diagrams) * (title_height + graph_margin) + total_rows * row_height

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_height}" viewBox="0 0 {width} {total_height}">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">'
        '<path d="M0,0 L10,4 L0,8 z" fill="#4a4a4a"/></marker></defs>',
        '<rect width="100%" height="100%" fill="#faf7f2"/>',
        '<style>text{font-family:Segoe UI,Arial,sans-serif;fill:#1f2933}'
        '.title{font-size:20px;font-weight:600}.subtitle{font-size:14px;font-weight:600}'
        '.path-label{font-size:12px}.node-text{font-size:12px;font-weight:600}</style>',
    ]

    y = 30
    parts.append('<text class="title" x="24" y="24">HVAC Connectivity</text>')
    if legend_labels:
        parts.append(f'<text class="subtitle" x="24" y="{y}">Legend (same name, same color)</text>')
        y += 10
        legend_cols = 3
        legend_col_width = 500
        for index, label in enumerate(legend_labels):
            row = index // legend_cols
            col = index % legend_cols
            legend_x = 24 + col * legend_col_width
            legend_y = y + row * legend_item_height
            color = label_colors[label]
            parts.append(
                f'<rect x="{legend_x}" y="{legend_y}" rx="4" ry="4" width="18" height="18" '
                f'fill="{color}" fill-opacity="0.30" stroke="{color}" stroke-width="1.5"/>'
            )
            parts.append(
                f'<text class="path-label" x="{legend_x + 26}" y="{legend_y + 13}">{escape(_truncate(label, 62))}</text>'
            )
        y += legend_rows * legend_item_height + 16
    for diagram in diagrams:
        parts.append(f'<text class="subtitle" x="24" y="{y}">{escape(_diagram_title(diagram))}</text>')
        y += 16
        if not diagram.paths:
            y += row_height
            continue
        for path in diagram.paths:
            row_top = y
            row_center = row_top + 24
            parts.append(f'<text class="path-label" x="24" y="{row_center}">{escape(path.label)}</text>')
            x = left_margin
            for index, node_id in enumerate(path.node_ids):
                node = diagram.nodes[node_id]
                color = label_colors.get(node.label, _COLOR_BY_KIND.get(node.kind, "#f4a261"))
                parts.append(
                    f'<rect x="{x}" y="{row_top}" rx="8" ry="8" width="{node_width}" height="{node_height}" '
                    f'fill="{color}" fill-opacity="0.20" stroke="{color}" stroke-width="1.5"/>'
                )
                parts.append(
                    f'<text class="node-text" x="{x + 10}" y="{row_top + 24}">{escape(_truncate(node.label, 28))}</text>'
                )
                if index < len(path.node_ids) - 1:
                    line_x1 = x + node_width
                    line_x2 = x + x_step - 18
                    line_y = row_top + node_height / 2
                    parts.append(
                        f'<line x1="{line_x1}" y1="{line_y}" x2="{line_x2}" y2="{line_y}" '
                        'stroke="#4a4a4a" stroke-width="1.5" marker-end="url(#arrow)"/>'
                    )
                x += x_step
            y += row_height
        y += graph_margin
    parts.append("</svg>")
    return "".join(parts)


def render_diagrams_html(diagrams_by_kind: dict[str, list[HVACDiagram]], selected_kind: str) -> str:
    svg = render_diagrams_svg(diagrams_by_kind, selected_kind)
    text = render_diagrams_text(diagrams_by_kind, selected_kind)
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
        "svg{display:block;max-width:100%;height:auto;}"
        "</style></head><body><div class=\"page\">"
        "<h1>HVAC Connectivity</h1>"
        "<p>Generated from epJSON. Includes text summary and simple diagram rendering.</p>"
        f'<section class="panel"><pre>{escape(text)}</pre></section>'
        f'<section class="panel">{svg}</section>'
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


def _label_color_map(diagrams: list[HVACDiagram]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for diagram in diagrams:
        for path in diagram.paths:
            for node_id in path.node_ids:
                node = diagram.nodes.get(node_id)
                if node is None or node.label in labels:
                    continue
                color = _LEGEND_COLORS[len(labels) % len(_LEGEND_COLORS)]
                labels[node.label] = color
    return labels
